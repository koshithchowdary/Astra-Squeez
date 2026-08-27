import numpy as np
import pandas as pd


def _atr(df, n=14):
    tr = pd.concat([
        df.high - df.low,
        (df.high - df.close.shift()).abs(),
        (df.low - df.close.shift()).abs()
    ], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def apply_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """Apply AstraSqueeze indicators and signals to normalized OHLC data."""
    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]
    df["ema_fast"] = df.close.ewm(span=9, adjust=False).mean()
    df["ema_slow"] = df.close.ewm(span=21, adjust=False).mean()
    df["atr"] = _atr(df).bfill()

    up = df.close.diff().clip(lower=0).rolling(14).mean()
    down = (-df.close.diff().clip(upper=0)).rolling(14).mean().replace(0, np.nan)
    df["rsi"] = (100 - 100 / (1 + up / down)).bfill()

    trend = df.ema_fast > df.ema_slow
    df["tf15"] = np.where(trend, "BULL", "BEAR")
    df["tf1h"] = np.where(df.close > df.close.rolling(12).mean(), "BULL", "BEAR")
    df["tf4h"] = np.where(df.close > df.close.rolling(48).mean(), "BULL", "BEAR")
    df["tf1d"] = np.where(df.close > df.close.rolling(96).mean(), "BULL", "BEAR")
    bulls = (df[["tf15", "tf1h", "tf4h", "tf1d"]] == "BULL").sum(axis=1)
    df["context"] = np.where(bulls >= 3, "BULL", np.where(bulls <= 1, "BEAR", "MIXED"))

    # Trend-strength proxy retained from the MVP; replace with full ADX in a later strategy-validation phase.
    df["adx"] = (100 * df.close.diff(14).abs() / (df["atr"] * 14).replace(0, np.nan)).clip(0, 100).bfill()
    mid = df.close.rolling(20).mean()
    std = df.close.rolling(20).std()
    width = (4 * std / mid).bfill()
    squeeze = width < width.rolling(100, min_periods=20).quantile(.25)
    buy = squeeze & trend & (df.rsi > 52) & (df.context == "BULL")
    sell = squeeze & (~trend) & (df.rsi < 48) & (df.context == "BEAR")
    df["signal"] = np.select([buy, sell], ["BUY SQUEEZE", "SELL SQUEEZE"], default="WAIT")
    return df


def generate_market(n=300, seed=42):
    rng = np.random.default_rng(seed)
    ret = rng.normal(0.0002, 0.006, n)
    close = 4600 * np.exp(np.cumsum(ret))
    open_ = np.r_[close[0], close[:-1]]
    spread = np.maximum(close * rng.uniform(.001, .006, n), 1)
    high = np.maximum(open_, close) + spread
    low = np.minimum(open_, close) - spread
    idx = pd.date_range(end=pd.Timestamp.now(), periods=n, freq="5min")
    raw = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close}, index=idx)
    return apply_strategy(raw)
