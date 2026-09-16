from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


class StructureLabel(str, Enum):
    HH = "HH"
    HL = "HL"
    LH = "LH"
    LL = "LL"


class SetupState(str, Enum):
    IDLE = "IDLE"
    VERIFYING = "VERIFYING"
    READY = "READY"
    INVALIDATED = "INVALIDATED"
    LOCKED = "LOCKED"


@dataclass(frozen=True, slots=True)
class Candle:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    timeframe: str = "30m"


@dataclass(frozen=True, slots=True)
class BookLevel:
    price: float
    quantity: float


@dataclass(frozen=True, slots=True)
class OrderBook:
    symbol: str
    timestamp: datetime
    bids: tuple[BookLevel, ...] = ()
    asks: tuple[BookLevel, ...] = ()


@dataclass(frozen=True, slots=True)
class MarketEvent:
    symbol: str
    timestamp: datetime
    candle: Candle | None = None
    order_book: OrderBook | None = None
    source: str = "unknown"
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SwingPoint:
    timestamp: datetime
    price: float
    is_high: bool
    label: StructureLabel


@dataclass(frozen=True, slots=True)
class Setup:
    symbol: str
    side: Side
    broken_level: float
    poc: float
    entry: float
    stop: float
    target: float
    detected_at: datetime
    verification_until: datetime


@dataclass(frozen=True, slots=True)
class OrderIntent:
    symbol: str
    side: Side
    order_type: OrderType
    quantity: float
    limit_price: float | None
    stop_price: float
    target_price: float
    client_order_id: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    equity: float
    realized_pnl_today: float
    realized_pnl_week: float
    unrealized_pnl: float
    open_positions: int


@dataclass(frozen=True, slots=True)
class RiskLimits:
    risk_fraction_per_trade: float = 0.005
    max_daily_loss_fraction: float = 0.02
    max_weekly_loss_fraction: float = 0.05
    min_rr: float = 2.5


@dataclass(frozen=True, slots=True)
class RiskDecision:
    approved: bool
    quantity: float = 0.0
    reason: str = ""
    target: float | None = None


@dataclass(frozen=True, slots=True)
class Position:
    symbol: str
    side: Side
    quantity: float
    entry_price: float
    mark_price: float

    @property
    def unrealized_pnl(self) -> float:
        direction = 1 if self.side is Side.BUY else -1
        return (self.mark_price - self.entry_price) * self.quantity * direction
