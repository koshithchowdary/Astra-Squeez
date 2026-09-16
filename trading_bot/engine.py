from __future__ import annotations

import asyncio
import logging
from dataclasses import replace

from .gateways import ExecutionGateway, MarketDataGateway
from .risk import KillSwitch, RiskManager
from .strategy import StructuralRetestStrategy

log = logging.getLogger(__name__)


class TradingEngine:
    """Event-driven orchestration. Data, strategy, risk and execution remain independent."""

    def __init__(self, data: MarketDataGateway, execution: ExecutionGateway, strategy: StructuralRetestStrategy, risk: RiskManager) -> None:
        self.data, self.execution, self.strategy, self.risk = data, execution, strategy, risk
        self.kill_switch = KillSwitch(execution)
        self.running = False

    async def run_symbol(self, symbol: str, timeframe: str = "30m") -> None:
        self.running = True
        log.info("engine starting symbol=%s timeframe=%s", symbol, timeframe)
        async for event in self.data.stream(symbol, timeframe):
            if not self.running:
                break
            if not event.candle:
                continue
            try:
                intent = await self.strategy.on_candle(event.candle)
                if not intent:
                    continue
                account = await self.execution.account()
                decision = await self.risk.authorize(intent, account)
                if not decision.approved:
                    log.warning("order rejected symbol=%s reason=%s", symbol, decision.reason)
                    if decision.reason in {"daily_loss_limit", "weekly_loss_limit", "risk_lock"}:
                        await self.kill_switch.trigger(decision.reason)
                    continue
                final_intent = replace(intent, quantity=decision.quantity)
                order_id = await self.execution.submit(final_intent)
                log.info("order submitted id=%s", order_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("event lifecycle failed symbol=%s", symbol)

    async def stop(self) -> None:
        self.running = False
        await self.data.close()
        log.info("engine stopped")
