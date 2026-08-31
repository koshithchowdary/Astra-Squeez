# Institutional Momentum Engine Report

## Purpose
A research-oriented trading decision engine designed to detect conditions consistent with strong market participation. It does not identify individual whales or guarantee profitable trades.

## Timeframe Model
- 1H: market regime
- 15M: directional bias and structure
- 5M: execution

## Core Conditions
### Long
1. Higher-timeframe regime is bullish or neutral.
2. 15M structure supports bullish continuation or reversal.
3. A sell-side liquidity sweep or valid continuation setup exists.
4. Bullish BOS/CHOCH is confirmed on closed candles.
5. Relative volume confirms participation.
6. Price is above or reclaiming VWAP.
7. EMA alignment and momentum filters support the trade.
8. Stop-loss has a clear structural invalidation level.
9. Reward-to-risk meets the configured minimum.
10. Price is not excessively extended from the planned entry.

### Short
Apply the inverse conditions.

## Indicators
- EMA 20 / 50 / 200
- VWAP
- RSI
- MACD
- ADX
- ATR
- Relative volume

Indicators confirm context; no single indicator creates a trade by itself.

## Liquidity and Structure
Preferred long sequence:
Liquidity sweep -> reclaim -> bullish CHOCH/BOS -> volume confirmation -> entry or controlled retest.

Preferred short sequence:
Buy-side liquidity sweep -> rejection -> bearish CHOCH/BOS -> volume confirmation -> entry or controlled retest.

## Momentum Score (0-100)
- 1H regime: 15
- 15M structure: 10
- 5M structure: 15
- Liquidity event: 15
- Relative volume: 10
- VWAP: 10
- EMA alignment: 8
- RSI: 5
- MACD: 4
- ADX: 4
- Volatility regime: 4

Grades:
- 85-100: A+ high-conviction candidate
- 75-84: A candidate
- 65-74: B watch/setup
- Below 65: no entry by default

A score cannot override failed hard-gate conditions.

## Entry Logic
Signals can be classified as:
- MARKET ENTRY: momentum confirmed at the close.
- LIMIT ENTRY: controlled pullback into the calculated entry zone.
- BREAKOUT ENTRY: enter only after the trigger level is confirmed.
- NO CHASE: setup remains valid but price is too extended.

## Stop Loss
Long:
Structural invalidation low minus an ATR-based buffer.

Short:
Structural invalidation high plus an ATR-based buffer.

The stop is based on invalidation, not an arbitrary fixed percentage.

## Take Profit
Risk R = absolute(entry - stop).

Default framework:
- TP1 = 1R
- TP2 = 2R
- TP3 = 3R

Targets may be adjusted to nearby liquidity, prior swing levels, or other validated structural targets.

## Signal Payload
Each valid signal must expose:
- Symbol
- Timeframe
- Side: LONG or SHORT
- Signal grade
- Momentum score
- Entry trigger or entry zone
- Exact planned entry
- Stop loss
- TP1
- TP2
- TP3
- Risk/reward
- Key reasons for the signal
- Invalidation/no-chase status

## No-Trade Rules
Do not enter when:
- ADX indicates weak/choppy conditions.
- Volume confirmation is absent.
- Higher timeframes conflict materially.
- The move is already extended.
- Reward-to-risk is insufficient.
- Structure is unclear.
- The stop is too wide relative to the available target.

## Trade Management
- After TP1, optionally reduce risk and move the stop according to the configured rules.
- Continue monitoring structure, VWAP, and momentum deterioration.
- A risk-management exit must be distinguishable from a strategy entry signal.

## Validation
Before real-money execution:
1. Backtest with realistic fees and slippage.
2. Validate on out-of-sample data.
3. Use walk-forward testing.
4. Review maximum drawdown, profit factor, expectancy, and trade distribution.
5. Paper trade before enabling any execution integration.

## Safety Note
This is a research and decision-support specification, not financial advice and not a guarantee of performance. "Whale" and "institutional" labels describe observable market footprints rather than verified identities.
