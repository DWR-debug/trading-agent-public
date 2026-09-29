# Q091 — Fixed Portfolio Architecture after Q090

## Status

DESIGN ONLY / COVERAGE-PIT PREPARATION

Q090 descriptively found that all five unchanged Q069 sleeves retained substantial
common market exposure. Q091 therefore changes only portfolio construction.

Two variants are frozen and unranked:

- **E1** — equal-weight ensemble: average all five Q069 target-weight vectors with 1/5 sleeve weights.
- **E2** — cross-sectional residualized ensemble: demean each Q069 target vector across the full fresh universe, average the five residual vectors equally, then gross-normalize to unit gross exposure.

The underlying Q069 signals, windows, assets chosen by coverage, costs and the 13-gate evidence contract are not optimized here.

## Why this is a new hypothesis

The hypothesis is architectural rather than parametric: reducing common cross-sectional
market exposure and combining mechanically distinct sleeves may alter drawdown behavior
without changing the underlying alpha definitions.

Q090 is diagnostic evidence only. It is not used to select one of the two Q091 variants.

## Required sequence

1. exact source/rule freeze;
2. fresh symbol-disjoint coverage;
3. immutable common-calendar snapshot;
4. PIT/mutation tests;
5. separate one-shot authorization;
6. symmetric fixed-rule performance under the unchanged 13-gate framework;
7. immutable reconciliation.

No holdout selection, parameter/threshold/asset/horizon/variant search, ranking,
promotion or live execution is permitted.

Safety remains:
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
