from trading_bot.domain import AccountSnapshot, OrderIntent, OrderType, RiskLimits, Side
from trading_bot.risk import RiskManager

import asyncio


def test_position_sizing_and_rr_guardrail():
    risk = RiskManager(RiskLimits(risk_fraction_per_trade=0.01, min_rr=2.5))
    intent = OrderIntent("BTC/USDT", Side.SELL, OrderType.LIMIT, 0, 100, 110, 75, "x")
    account = AccountSnapshot(10000, 0, 0, 0, 0)
    decision = asyncio.run(risk.authorize(intent, account))
    assert decision.approved
    assert decision.quantity == 1.0


def test_daily_loss_lock():
    risk = RiskManager(RiskLimits(max_daily_loss_fraction=0.02))
    intent = OrderIntent("BTC/USDT", Side.SELL, OrderType.LIMIT, 0, 100, 110, 75, "x")
    account = AccountSnapshot(10000, -250, 0, 0, 0)
    decision = asyncio.run(risk.authorize(intent, account))
    assert not decision.approved
    assert decision.reason == "daily_loss_limit"
