from __future__ import annotations

import asyncio
import logging
from collections import deque
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pandas as pd

from .domain import Candle, OrderIntent, OrderType, Setup, Side, StructureLabel, SwingPoint

log = logging.getLogger(__name__)


class VolumeProfile:
    """Fixed-range volume profile using close-price bins and candle volume."""

    def __init__(self, bins: int = 48) -> None:
        self.bins = bins

    def poc(self, candles: list[Candle]) -> float:
        if not candles:
            raise ValueError("volume profile requires candles")
        frame = pd.DataFrame([c.__dict__ for c in candles])
        lo, hi = float(frame.low.min()), float(frame.high.max())
        if hi <= lo:
            return float(frame.close.iloc[-1])
        edges = pd.np.linspace(lo, hi, self.bins + 1) if hasattr(pd, "np") else None
        if edges is None:
            import numpy as np
            edges = np.linspace(lo, hi, self.bins + 1)
        idx = pd.cut(frame.close, bins=edges, include_lowest=True, labels=False)
        volume = frame.assign(bin=idx).groupby("bin", observed=True).volume.sum()
        selected = int(volume.idxmax())
        return float((edges[selected] + edges[selected + 1]) / 2)


class MarketStructureTracker:
    def __init__(self, left_right: int = 2, max_points: int = 100) -> None:
        self.lr = left_right
        self.candles: deque[Candle] = deque(maxlen=500)
        self.swings: deque[SwingPoint] = deque(maxlen=max_points)

    def update(self, candle: Candle) -> SwingPoint | None:
        self.candles.append(candle)
        n = len(self.candles)
        if n < 2 * self.lr + 1:
            return None
        c = list(self.candles)
        candidate = c[-self.lr - 1]
        window = c[-2 * self.lr - 1 :]
        is_high = candidate.high == max(x.high for x in window)
        is_low = candidate.low == min(x.low for x in window)
        if not (is_high or is_low):
            return None
        is_high = is_high and not is_low
        price = candidate.high if is_high else candidate.low
        previous = [s for s in self.swings if s.is_high == is_high]
        if not previous:
            label = StructureLabel.HH if is_high else StructureLabel.LL
        else:
            label = (StructureLabel.HH if price > previous[-1].price else StructureLabel.LH) if is_high else (StructureLabel.HL if price > previous[-1].price else StructureLabel.LL)
        swing = SwingPoint(candidate.timestamp, price, is_high, label)
        self.swings.append(swing)
        log.info("structure swing symbol=%s label=%s price=%.8f", candle.symbol, label, price)
        return swing

    def key_floor(self) -> float | None:
        lows = [s.price for s in self.swings if not s.is_high]
        return lows[-1] if lows else None

    def key_ceiling(self) -> float | None:
        highs = [s.price for s in self.swings if s.is_high]
        return highs[-1] if highs else None


class StructuralRetestStrategy:
    """Bearish MSS -> 15m verification -> rejection -> structural limit entry."""

    def __init__(self, verification_minutes: int = 15, profile_window: int = 96) -> None:
        self.verification = timedelta(minutes=verification_minutes)
        self.profile_window = profile_window
        self.structure: dict[str, MarketStructureTracker] = {}
        self.history: dict[str, deque[Candle]] = {}
        self.pending: dict[str, Setup] = {}
        self.profile = VolumeProfile()
        self._lock = asyncio.Lock()

    async def on_candle(self, candle: Candle) -> OrderIntent | None:
        async with self._lock:
            tracker = self.structure.setdefault(candle.symbol, MarketStructureTracker())
            history = self.history.setdefault(candle.symbol, deque(maxlen=self.profile_window))
            history.append(candle)
            tracker.update(candle)
            setup = self.pending.get(candle.symbol)

            if setup:
                if candle.timestamp >= setup.verification_until:
                    if self._clean_rejection(candle, setup):
                        self.pending.pop(candle.symbol, None)
                        return self._intent(candle, setup)
                    log.info("verification failed symbol=%s", candle.symbol)
                    self.pending.pop(candle.symbol, None)
                elif candle.high > setup.broken_level and candle.close > setup.broken_level:
                    log.info("MSS retest invalidated symbol=%s", candle.symbol)
                    self.pending.pop(candle.symbol, None)
                return None

            floor = tracker.key_floor()
            if floor is None or candle.close >= floor:
                return None
            # Aggressive close through structural floor = bearish MSS.
            body = abs(candle.close - candle.open)
            range_ = max(candle.high - candle.low, 1e-12)
            if body / range_ < 0.60:
                return None
            poc = self.profile.poc(list(history))
            if abs(poc - floor) > range_ * 1.5:
                return None
            now = candle.timestamp
            self.pending[candle.symbol] = Setup(
                symbol=candle.symbol, side=Side.SELL, broken_level=floor,
                poc=poc, entry=(floor + poc) / 2, stop=candle.high,
                target=0.0, detected_at=now, verification_until=now + self.verification,
            )
            log.warning("bearish MSS detected symbol=%s floor=%.8f poc=%.8f verify_until=%s", candle.symbol, floor, poc, now + self.verification)
            return None

    @staticmethod
    def _clean_rejection(candle: Candle, setup: Setup) -> bool:
        zone = (setup.broken_level + setup.poc) / 2
        touched = candle.high >= min(setup.broken_level, setup.poc)
        rejected = candle.close < zone and candle.close < candle.open
        return touched and rejected

    @staticmethod
    def _intent(candle: Candle, setup: Setup) -> OrderIntent:
        entry = setup.entry
        stop = setup.stop
        risk = abs(stop - entry)
        target = entry - 2.5 * risk
        return OrderIntent(
            symbol=candle.symbol, side=Side.SELL, order_type=OrderType.LIMIT,
            quantity=0.0, limit_price=entry, stop_price=stop, target_price=target,
            client_order_id=f"srt-{candle.symbol}-{uuid4().hex[:12]}",
            metadata={"reason": "bearish_mss_retest", "poc": setup.poc, "rr": 2.5},
        )
