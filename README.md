# Astra-Squeez — Event-Driven Structural Retest Engine

A modular Python algorithmic-trading engine implementing the Structural Break & Confluence Retest specification.

## Architecture
- **Market data ingestion:** broker/exchange-neutral OHLCV and order-book models.
- **Strategy engine:** HH/HL/LH/LL swing structure, bearish Market Structure Shift (MSS), fixed-range Volume Profile/POC, asynchronous 15-minute verification, and clean retest rejection.
- **Execution layer:** broker-agnostic order gateway with an async CCXT implementation boundary and explicit IBKR/Dhan integration boundaries.
- **Risk engine:** equity-based position sizing from exact entry/stop distance, structural stop-loss, minimum 2.5R target, and daily/weekly loss locks.
- **Kill switch:** cancels working limits, closes open positions, and locks trading after configured daily/weekly loss limits.
- **API:** FastAPI lifecycle and health endpoints.
- **Operations:** structured lifecycle logging throughout ingestion, signal generation, risk approval, execution, and shutdown.

## Supported integration boundaries
- Crypto: CCXT async REST/WebSocket-compatible gateway boundary.
- Equities/Futures: Interactive Brokers gateway boundary.
- Local brokerage: Dhan REST/WebSocket gateway boundary.

External feeds are normalized into the same internal domain models so strategy and risk logic remain independent of the broker.

## Safety defaults
Execution is **PAPER mode by default**. Live execution must be explicitly configured through a real broker gateway and should not be enabled until broker-specific order semantics, quantity/price rounding, reconnect handling, reconciliation, persistence, and restart recovery are validated.

## Run

```bash
pip install -r requirements.txt
uvicorn trading_bot.api:app --host 0.0.0.0 --port 8000
```

Run tests with:

```bash
pytest
```

## Project structure

```text
trading_bot/
├── api.py        # FastAPI application
├── domain.py     # normalized market/order/account models
├── engine.py     # event-driven orchestration
├── gateways.py   # market-data and execution boundaries
├── risk.py       # sizing and daily/weekly loss controls
├── strategy.py   # structural MSS + volume-profile retest strategy
└── __init__.py

tests/
└── test_risk.py

requirements.txt
```

This repository intentionally contains only the new event-driven trading engine and its tests; the previous squeeze/backtesting/Streamlit application has been removed.
