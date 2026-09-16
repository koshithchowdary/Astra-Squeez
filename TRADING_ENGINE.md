# Event-Driven Structural Retest Engine

This branch adds a modular Python trading-engine foundation to Astra-Squeez. The design deliberately separates **market data ingestion**, **strategy**, **risk**, and **execution** behind interfaces.

## Architecture

```text
CCXT / IBKR / Dhan
        |
        v
 MarketDataGateway ---> normalized MarketEvent
        |
        v
 StructuralRetestStrategy
   | structure swings
   | MSS detection
   | fixed-range volume profile / POC
   | >=15 minute async verification
   | clean rejection
        |
        v
   OrderIntent
        |
        v
 RiskManager
   | equity-based risk budget
   | exact entry/stop distance sizing
   | minimum 2.5R target
   | daily/weekly loss lock
        |
        v
 ExecutionGateway ---> Paper / broker adapter
        |
        +---- KillSwitch: cancel limits + close positions
```

## Strategy lifecycle

1. Candles are normalized into `Candle` regardless of asset class.
2. Confirmed swing points are labeled HH/HL/LH/LL.
3. A bearish MSS requires an aggressive candle-body close below the latest structural floor.
4. The fixed-range profile finds POC and requires POC/floor confluence.
5. The setup enters `VERIFYING`; no order is sent during this period.
6. After at least 15 minutes, price must retest the broken zone and close back below it with bearish rejection.
7. A structural limit order is created at the floor/POC midpoint.
8. Risk sizing uses `equity * risk_fraction / abs(entry-stop)`.
9. The target is hard-coded at >=2.5R.
10. Daily/weekly loss limits fail closed and invoke cancellation plus position liquidation through the execution gateway.

## Safety

The service starts in **PAPER mode**. No live broker order implementation is enabled by default. IBKR and Dhan adapters are explicit integration boundaries because contract/instrument mappings, account permissions, order semantics, and production connectivity must be configured for the actual account. Do not turn on live execution without independent paper testing, reconciliation, rate-limit handling, idempotency, and broker-specific order validation.

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-trading-bot.txt
python run_trading_bot.py
```

Then use `POST /run` with `{ "symbol": "BTC/USDT", "timeframe": "30m", "exchange": "binance" }`.

## Broker integration notes

- **CCXT:** the adapter uses `ccxt.async_support` for asynchronous REST polling of closed candles. CCXT's async package is documented by the project; a CCXT Pro `watch*` implementation can replace the polling loop where WebSocket access is licensed/available.
- **IBKR:** implement the `IBKRMarketDataGateway` contract bridge using TWS/IB Gateway callbacks and map contracts to normalized candles/depth. The core engine remains broker-independent.
- **Dhan:** use the current DhanHQ Python client/MarketFeed or FullDepth callbacks in `DhanMarketDataGateway`, mapping Dhan instrument identifiers to the normalized event model.

## Operational hardening still required before live deployment

- persistent event/order/position store and restart recovery
- broker reconciliation and idempotent client-order IDs
- clock synchronization and stale-feed detection
- heartbeat/watchdog and exponential reconnects
- exchange-specific tick/lot/contract multiplier rounding
- transaction costs, slippage and partial-fill accounting
- persistent daily/weekly P&L state across process restarts
- multi-symbol concurrency and per-symbol state isolation
- secrets management and network controls
- comprehensive historical, walk-forward and paper-trading validation
