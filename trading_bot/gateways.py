from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import AsyncIterator

from .domain import AccountSnapshot, Candle, MarketEvent, OrderIntent, OrderBook, Position

log = logging.getLogger(__name__)


class MarketDataGateway(ABC):
    @abstractmethod
    async def stream(self, symbol: str, timeframe: str) -> AsyncIterator[MarketEvent]:
        raise NotImplementedError

    async def close(self) -> None:
        return None


class ExecutionGateway(ABC):
    @abstractmethod
    async def submit(self, intent: OrderIntent) -> str:
        raise NotImplementedError

    @abstractmethod
    async def cancel_all(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def close_all_positions(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def account(self) -> AccountSnapshot:
        raise NotImplementedError


class PaperExecutionGateway(ExecutionGateway):
    """Safe default: records intents and never sends broker orders."""

    def __init__(self, equity: float = 100_000.0) -> None:
        self.equity = equity
        self.orders: list[OrderIntent] = []

    async def submit(self, intent: OrderIntent) -> str:
        self.orders.append(intent)
        log.warning("PAPER order accepted id=%s symbol=%s qty=%s", intent.client_order_id, intent.symbol, intent.quantity)
        return intent.client_order_id

    async def cancel_all(self) -> None:
        log.warning("PAPER cancel_all")
        self.orders.clear()

    async def close_all_positions(self) -> None:
        log.warning("PAPER close_all_positions")

    async def account(self) -> AccountSnapshot:
        return AccountSnapshot(self.equity, 0.0, 0.0, 0.0, 0)


class CCXTMarketDataGateway(MarketDataGateway):
    """CCXT async REST polling adapter; replace with CCXT Pro watch_* for WS."""

    def __init__(self, exchange_id: str, credentials: dict | None = None) -> None:
        self.exchange_id = exchange_id
        self.credentials = credentials or {}
        self.exchange = None

    async def stream(self, symbol: str, timeframe: str) -> AsyncIterator[MarketEvent]:
        import ccxt.async_support as ccxt
        cls = getattr(ccxt, self.exchange_id)
        self.exchange = cls({**self.credentials, "enableRateLimit": True})
        await self.exchange.load_markets()
        last_ts = None
        try:
            while True:
                rows = await self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=2)
                row = rows[-2]  # closed candle only
                if row[0] != last_ts:
                    last_ts = row[0]
                    import datetime as dt
                    candle = Candle(symbol, dt.datetime.fromtimestamp(row[0] / 1000, dt.timezone.utc), *map(float, row[1:6]), timeframe)
                    yield MarketEvent(symbol, candle.timestamp, candle=candle, source=f"ccxt:{self.exchange_id}")
                await __import__("asyncio").sleep(2)
        finally:
            await self.exchange.close()


class IBKRMarketDataGateway(MarketDataGateway):
    """IBKR adapter boundary. Uses ib_insync when installed; no strategy dependency on it."""

    def __init__(self, client_id: int = 71, host: str = "127.0.0.1", port: int = 7497) -> None:
        self.client_id, self.host, self.port = client_id, host, port

    async def stream(self, symbol: str, timeframe: str) -> AsyncIterator[MarketEvent]:
        raise NotImplementedError("Implement contract mapping and ib_insync/official TWS callback bridge for your IB account")
        yield  # pragma: no cover


class DhanMarketDataGateway(MarketDataGateway):
    """DhanHQ adapter boundary. The official SDK supplies MarketFeed/FullDepth callbacks."""

    def __init__(self, client_id: str, access_token: str) -> None:
        self.client_id, self.access_token = client_id, access_token

    async def stream(self, symbol: str, timeframe: str) -> AsyncIterator[MarketEvent]:
        raise NotImplementedError("Map Dhan instrument identifiers to normalized MarketEvent in the account-specific adapter")
        yield  # pragma: no cover
