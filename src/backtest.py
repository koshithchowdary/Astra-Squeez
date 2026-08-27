from dataclasses import dataclass
import numpy as np
import pandas as pd

@dataclass
class BacktestResult:
    trades: pd.DataFrame
    equity: pd.DataFrame
    metrics: dict


def run_backtest(df: pd.DataFrame, fee_bps: float = 5.0, slippage_bps: float = 2.0,
                 risk_atr: float = 1.5, target_r: float = 2.0,
                 initial_capital: float = 10000.0) -> BacktestResult:
    """Single-position signal backtest. Entries occur on the next bar to reduce look-ahead bias."""
    cash = float(initial_capital)
    position = None
    trades = []
    equity_rows = []
    fee_rate = fee_bps / 10000.0
    slip_rate = slippage_bps / 10000.0

    for i in range(1, len(df)):
        row = df.iloc[i]
        prev = df.iloc[i - 1]
        price = float(row.close)
        if position is None and prev.signal in ("BUY SQUEEZE", "SELL SQUEEZE"):
            side = 1 if prev.signal == "BUY SQUEEZE" else -1
            entry = price * (1 + slip_rate * side)
            stop = entry - side * float(prev.atr) * risk_atr
            target = entry + side * abs(entry - stop) * target_r
            position = {"side": side, "entry": entry, "stop": stop, "target": target,
                        "entry_time": row.name, "signal": prev.signal}
        elif position is not None:
            side = position["side"]
            exit_price = None
            reason = None
            if side == 1:
                if row.low <= position["stop"]:
                    exit_price, reason = position["stop"], "STOP"
                elif row.high >= position["target"]:
                    exit_price, reason = position["target"], "TARGET"
            else:
                if row.high >= position["stop"]:
                    exit_price, reason = position["stop"], "STOP"
                elif row.low <= position["target"]:
                    exit_price, reason = position["target"], "TARGET"
            if exit_price is not None:
                exit_price *= (1 - slip_rate * side)
                gross_return = side * (exit_price - position["entry"]) / position["entry"]
                net_return = gross_return - 2 * fee_rate
                pnl = cash * net_return
                cash += pnl
                trades.append({**position, "exit_time": row.name, "exit": exit_price,
                               "reason": reason, "return_pct": net_return * 100, "pnl": pnl})
                position = None
        mark = cash
        if position is not None:
            mark *= 1 + position["side"] * (price - position["entry"]) / position["entry"]
        equity_rows.append({"time": row.name, "equity": mark})

    trades_df = pd.DataFrame(trades)
    equity_df = pd.DataFrame(equity_rows)
    if equity_df.empty:
        equity_df = pd.DataFrame([{"time": df.index[0], "equity": initial_capital}])
    running_max = equity_df.equity.cummax()
    drawdown = equity_df.equity / running_max - 1
    if trades_df.empty:
        metrics = {"trades": 0, "win_rate": 0.0, "net_pnl": 0.0, "return_pct": 0.0,
                   "max_drawdown_pct": 0.0, "profit_factor": 0.0}
    else:
        wins = trades_df[trades_df.pnl > 0]
        losses = trades_df[trades_df.pnl < 0]
        gross_profit = wins.pnl.sum()
        gross_loss = abs(losses.pnl.sum())
        metrics = {
            "trades": len(trades_df),
            "win_rate": len(wins) / len(trades_df) * 100,
            "net_pnl": cash - initial_capital,
            "return_pct": (cash / initial_capital - 1) * 100,
            "max_drawdown_pct": drawdown.min() * 100,
            "profit_factor": gross_profit / gross_loss if gross_loss else np.inf,
        }
    return BacktestResult(trades_df, equity_df, metrics)
