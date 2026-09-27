# Q039 — Price-Only Alpha PIT Preflight

Stand: 2026-09-27
Status: PREREGISTERED / PIT-ONLY
Basis: Q038 fresh disjoint coverage

## Purpose

Q039 tests whether the price/OHLCV implementations of the ex-ante alpha mechanisms can change when information strictly after the decision point is changed.

No return, Sharpe, drawdown, profit factor, rolling performance or holdout metric is calculated.

## Frozen universe

Q038 validated eight fully symbol-disjoint candidates: IVE, IWL, DLN, DHS, DON, DES, USRT, ITB.
Q038 found 4,000 common sessions with zero invalid OHLCV rows in the reported acquisitions.

## PIT mechanisms

A1 — Multi-Horizon Trend Continuation: fixed sign vote over 21/63/252-session price changes.
A2 — Cross-Sectional Momentum: fixed 252-session formation return, 21-session skip, top-two cross-sectional rank.
A3 — Residual Momentum: fixed 252-return formation window ending 21 sessions before the decision, residualized against the equal-weight universe return.
A5 — Low-Beta Defensive Premium: fixed 252-return beta estimate ending 21 sessions before the decision; two lowest-beta assets.

## Mutation contract

At deterministic decision points, Q039 evaluates the four fixed mechanisms, changes every OHLC value strictly after the decision point, recomputes all signals, and requires identical outputs. A separate next-session OHLC mutation must also leave the decision output unchanged.

## Next gate

A successful Q039 result permits only preparation of fixed-rule performance preregistration. It does not authorize performance.

A4 event/information research remains separate because its validity depends on external publication timestamps and source-specific PIT evidence.
