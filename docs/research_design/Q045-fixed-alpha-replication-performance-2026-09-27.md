# Q045 — Fixed Alpha Replication Performance

Q045 is the first performance replication after two independent coverage/PIT layers.

## Universe
AON, CVS, ADSK, BA, T, F, LUV, NFLX; 4000 requested daily candles; 3500 common target; 2798 research and 700 holdout periods.

## Arms
CONTROL plus A1, A2, A3, A5, A1b and A6 are carried forward unchanged from prior PIT-safe definitions.

A new fixed diversification arm, **ENSEMBLE_ALL6**, allocates exactly 1/6 of gross exposure to each alpha arm. It is an exploratory mechanism-combination hypothesis, not a performance-weighted selection rule.

## Evaluation
All arms receive the same return, turnover, cost-stress, total-return-sensitivity, rolling and OOS/IS treatment. The 13-gate contract is unchanged.

Holdout is descriptive and remains unavailable for selection or parameter changes. There is no automatic promotion.

## Safety
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
