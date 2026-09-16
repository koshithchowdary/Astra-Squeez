from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from .domain import AccountSnapshot, OrderIntent, Position, RiskDecision, RiskLimits, Side

log = logging.getLogger(__name__)


class RiskLock:
    def __init__(self) -> None:
        self._daily = False
        self._weekly = False
        self._lock = asyncio.Lock()

    @property
    def locked(self) -> bool:
        return self._daily or self._weekly

    async def engage(self, scope: str) -> None:
        async with self._lock:
            if scope == "daily":
                self._daily = True
            elif scope == "weekly":
                self._weekly = True
            log.critical("RISK LOCK ENGAGED scope=%s", scope)

    async def clear(self, scope: str) -> None:
        async with self._lock:
            if scope == "daily":
                self._daily = False
            elif scope == "weekly":
                self._weekly = False


class RiskManager:
    def __init__(self, limits: RiskLimits, lock: RiskLock | None = None) -> None:
        self.limits = limits
        self.lock = lock or RiskLock()

    def systemic_check(self, account: AccountSnapshot) -> str | None:
        if account.equity <= 0:
            return "non_positive_equity"
        if account.realized_pnl_today <= -account.equity * self.limits.max_daily_loss_fraction:
            return "daily_loss_limit"
        if account.realized_pnl_week <= -account.equity * self.limits.max_weekly_loss_fraction:
            return "weekly_loss_limit"
        if self.lock.locked:
            return "risk_lock"
        return None

    async def authorize(self, intent: OrderIntent, account: AccountSnapshot) -> RiskDecision:
        reason = self.systemic_check(account)
        if reason:
            scope = "weekly" if reason == "weekly_loss_limit" else "daily" if reason == "daily_loss_limit" else "daily"
            await self.lock.engage(scope)
            return RiskDecision(False, reason=reason)

        if intent.limit_price is None or intent.stop_price is None:
            return RiskDecision(False, reason="missing_entry_or_stop")
        distance = abs(intent.stop_price - intent.limit_price)
        if distance <= 0:
            return RiskDecision(False, reason="zero_stop_distance")
        if intent.target_price is None:
            return RiskDecision(False, reason="missing_target")
        reward = abs(intent.target_price - intent.limit_price)
        rr = reward / distance
        if rr < self.limits.min_rr:
            return RiskDecision(False, reason=f"rr_below_minimum:{rr:.4f}")

        risk_budget = account.equity * self.limits.risk_fraction_per_trade
        quantity = risk_budget / distance
        if quantity <= 0:
            return RiskDecision(False, reason="non_positive_quantity")
        log.info("risk approved symbol=%s qty=%.8f risk_budget=%.2f rr=%.2f", intent.symbol, quantity, risk_budget, rr)
        return RiskDecision(True, quantity=quantity, target=intent.target_price)


class KillSwitch:
    """Fail-closed global liquidation coordinator."""

    def __init__(self, execution_gateway) -> None:
        self.execution = execution_gateway
        self.triggered = False

    async def trigger(self, scope: str) -> None:
        if self.triggered:
            return
        self.triggered = True
        log.critical("KILL SWITCH triggered scope=%s", scope)
        await self.execution.cancel_all()
        await self.execution.close_all_positions()


class PositionSizer:
    """Separate sizing math to keep broker/exchange semantics out of risk logic."""

    @staticmethod
    def size(equity: float, risk_fraction: float, entry: float, stop: float, contract_multiplier: float = 1.0) -> float:
        distance = abs(entry - stop)
        if distance <= 0 or contract_multiplier <= 0:
            return 0.0
        return (equity * risk_fraction) / (distance * contract_multiplier)
