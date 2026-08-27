import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.strategy import generate_market

st.set_page_config(page_title="AstraSqueeze", layout="wide")
st.title("⚡ AstraSqueeze")
st.caption("Multi-timeframe squeeze, trend and risk intelligence • Demo / paper-trading MVP")

symbol = st.sidebar.text_input("Symbol", "XAUUSD")
seed = st.sidebar.number_input("Demo seed", 1, 9999, 42)
bars = st.sidebar.slider("Bars", 100, 1000, 300)
df = generate_market(bars, int(seed))
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

left, right = st.columns([1.2, 1])
with left:
    st.subheader("Market Context")
    st.dataframe(pd.DataFrame({"Timeframe":["15m","1h","4h","1D"], "Bias":[last["tf15"],last["tf1h"],last["tf4h"],last["tf1d"]]}), hide_index=True, use_container_width=True)
with right:
    st.subheader("Trade Plan")
    if last["signal"] != "WAIT":
        entry = last["close"]
        risk = last["atr"] * 1.5
        side = 1 if last["signal"] == "BUY SQUEEZE" else -1
        plan = pd.DataFrame({"Level":["Entry","Stop","TP1","TP2","TP3","TP4"], "Price":[entry, entry-side*risk, entry+side*risk, entry+side*2*risk, entry+side*3*risk, entry+side*4*risk]})
        st.dataframe(plan.round(2), hide_index=True, use_container_width=True)
    else:
        st.info("No setup. Waiting for trend + squeeze alignment.")

st.warning("Demo mode: generated market data only. No real orders are placed.")
