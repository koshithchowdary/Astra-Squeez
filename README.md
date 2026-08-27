# AstraSqueeze ⚡

A multi-timeframe squeeze and trend research platform inspired by the trading workflow in the supplied screenshot.

## Phase 2 features
- Real OHLC market data through Yahoo Finance / `yfinance`
- Demo-data fallback for safe UI testing
- 5m, 15m, 1h and 1d analysis options
- 15m / 1h / 4h / 1D market context model
- EMA trend alignment and RSI confirmation
- Volatility squeeze detection
- BUY SQUEEZE / SELL SQUEEZE / WAIT states
- ATR-based stop and target framework
- Historical signal backtesting
- Configurable starting capital, fees, slippage and reward:risk
- Win rate, net P&L, return, maximum drawdown and profit factor
- Equity curve and downloadable trade history CSV
- No real-order execution

## Example tickers
- `GC=F` — Gold futures
- `BTC-USD` — Bitcoin
- `ETH-USD` — Ethereum
- `EURUSD=X` — EUR/USD

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important research notes
The current backtester is intentionally simple: one position at a time, next-bar entry, ATR stop and fixed R-multiple target. It is a research tool, not evidence that the strategy is profitable. Historical results can change materially with the data source, interval, fees, slippage and execution assumptions.

## Roadmap
1. Strategy validation and full ADX / multi-timeframe resampling
2. Paper portfolio with persistent positions and trade journal
3. Walk-forward testing and parameter optimization safeguards
4. Alerts
5. Optional broker/exchange adapters behind explicit user-controlled execution settings

> Not financial advice. Real trading remains disabled.
