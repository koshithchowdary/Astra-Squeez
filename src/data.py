import pandas as pd
import yfinance as yf

INTERVAL_LIMITS = {
    "1m": "7d", "2m": "60d", "5m": "60d", "15m": "60d",
    "30m": "60d", "60m": "730d", "1h": "730d", "1d": "10y"
}


def fetch_market_data(symbol: str, interval: str = "15m", period: str | None = None) -> pd.DataFrame:
    """Fetch OHLCV data and normalize columns for AstraSqueeze."""
    period = period or INTERVAL_LIMITS.get(interval, "1y")
    data = yf.download(symbol, period=period, interval=interval, auto_adjust=False,
                       progress=False, group_by="column")
    if data.empty:
        raise ValueError(f"No market data returned for {symbol}. Check the ticker and interval.")
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data = data.rename(columns=str.lower)
    required = ["open", "high", "low", "close"]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(f"Missing OHLC columns: {missing}")
    data = data.dropna(subset=required).copy()
    return data
