import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.strategy import generate_market
from src.data import fetch_market_data
from src.backtest import run_backtest

st.set_page_config(page_title="AstraSqueeze", layout="wide")
st.title("⚡ AstraSqueeze")
st.caption("Multi-timeframe squeeze, trend and risk intelligence • Phase 2 Research & Paper Trading")

st.sidebar.header("Market Data")
mode = st.sidebar.selectbox("Data source", ["Real market data", "Demo data"])
symbol = st.sidebar.text_input("Ticker", "GC=F", help="Examples: GC=F for Gold futures, BTC-USD, EURUSD=X")
interval = st.sidebar.selectbox("Interval", ["5m", "15m", "1h", "1d"], index=1)
bars = st.sidebar.slider("Demo bars", 100, 1000, 300)
st.sidebar.header("Backtest")
initial_capital = st.sidebar.number_input("Starting capital", min_value=1000.0, value=10000.0, step=1000.0)
fee_bps = st.sidebar.number_input("Fees (bps / side)", min_value=0.0, value=5.0, step=1.0)
slippage_bps = st.sidebar.number_input("Slippage (bps / side)", min_value=0.0, value=2.0, step=1.0)
target_r = st.sidebar.slider("Target reward:risk", 1.0, 5.0, 2.0, 0.25)

try:
    if mode == "Real market data":
        df = fetch_market_data(symbol, interval)
    else:
        df = generate_market(bars)
    df = generate_market(1) if df.empty else df
    if mode == "Real market data":
        # Apply the existing indicator/signal engine to real OHLC data.
        from src.strategy import apply_strategy
        df = apply_strategy(df)
except Exception as exc:
    st.error(f"Data error: {exc}")
    st.stop()

last = df.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Market Context", last["context"])
c2.metric("ADX", f'{last["adx"]:.1f}')
c3.metric("Current Signal", last["signal"])
c4.metric("Last Price", f'{last["close"]:.2f}')

fig = go.Figure()
fig.add_trace(go.Candlestick(x=df.index, open=df.open, high=df.high, low=df.low, close=df.close, name=symbol))
fig.add_trace(go.Scatter(x=df.index, y=df["ema_fast"], name="EMA Fast"))
fig.add_trace(go.Scatter(x=df.index, y=df["ema_slow"], name="EMA Slow"))
st.plotly_chart(fig, use_container_width=True)

result = run_backtest(df, fee_bps=fee_bps, slippage_bps=slippage_bps,
                      target_r=target_r, initial_capital=initial_capital)
st.subheader("Backtest Performance")
m = result.metrics
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("Trades", m["trades"])
m2.metric("Win rate", f'{m["win_rate"]:.1f}%')
m3.metric("Net P&L", f'{m["net_pnl"]:,.2f}')
m4.metric("Return", f'{m["return_pct"]:.2f}%')
m5.metric("Max drawdown", f'{m["max_drawdown_pct"]:.2f}%')
pf = "∞" if m["profit_factor"] == float("inf") else f'{m["profit_factor"]:.2f}'
m6.metric("Profit factor", pf)

st.line_chart(result.equity.set_index("time")["equity"])
if not result.trades.empty:
    st.subheader("Trade History")
    st.dataframe(result.trades.round(4), use_container_width=True, hide_index=True)
    st.download_button("Download trades CSV", result.trades.to_csv(index=False),
                       file_name="astra_squeeze_trades.csv", mime="text/csv")
else:
    st.info("No completed trades for the selected dataset and parameters.")

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Market Context")
    st.dataframe(pd.DataFrame({"Timeframe":["15m","1h","4h","1D"], "Bias":[last["tf15"],last["tf1h"],last["tf4h"],last["tf1d"]]}), hide_index=True, use_container_width=True)
with right:
    st.subheader("Paper Trade Plan")
    if last["signal"] != "WAIT":
        entry = last["close"]
        risk = last["atr"] * 1.5
        side = 1 if last["signal"] == "BUY SQUEEZE" else -1
        plan = pd.DataFrame({"Level":["Entry","Stop","TP1","TP2","TP3","TP4"], "Price":[entry, entry-side*risk, entry+side*risk, entry+side*2*risk, entry+side*3*risk, entry+side*4*risk]})
        st.dataframe(plan.round(2), hide_index=True, use_container_width=True)
    else:
        st.info("No setup. Waiting for trend + squeeze alignment.")

st.warning("Research and paper-trading mode only. Historical results do not guarantee future performance, and no real orders are placed.")
