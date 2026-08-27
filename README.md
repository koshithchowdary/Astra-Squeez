# AstraSqueeze ⚡

A multi-timeframe squeeze and trend intelligence MVP inspired by the trading workflow in the supplied screenshot.

## Features
- 15m / 1h / 4h / 1D market context
- EMA trend alignment
- RSI confirmation
- Volatility squeeze detection
- BUY SQUEEZE / SELL SQUEEZE / WAIT states
- ATR-based stop loss and TP1–TP4
- Interactive Streamlit dashboard
- Safe generated data demo mode

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Roadmap
1. Historical/live market data adapters
2. Configurable indicators and proper ADX
3. Backtesting with fees and slippage
4. Paper trading
5. Alerts
6. Broker/exchange integration behind an explicit execution toggle

> Not financial advice. No live trading is enabled in this MVP.
