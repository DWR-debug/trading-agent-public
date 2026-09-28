# Q068 — Fresh E1/E2 Validation

## Status

**PREREGISTERED_DESIGN_ONLY_FROZEN**

Q068 is a fresh, symbol-disjoint validation of the two mechanisms fixed in Q067:
- E1 Alpha Common-Mode Throttle
- E2 Turnover Hysteresis

Q067 remains immutable. Its coverage failure is not repaired by changing its
universe or source contract.

## Fixed universe

The asset set is fixed ex ante from the existing source-order, coverage-only
candidate discovery run:
- workflow: 36389197475
- discovery fingerprint: b85c7c35b593ce7b8ba4e4bb27de6fe1588338684d51330cd749da076cc5441e
- selected Q068 symbols: ETR, PPL, WEC, FE, D, EXR, PSA, O

The selection rule consulted only the frozen candidate-pool order and the
coverage contract. No return, P&L, holdout, ranking or performance metric was
used. These symbols were absent from the registered research universes and
trial ledger when Q068 was frozen.

## Data contract

- source: canonical Yahoo OHLCV snapshot
- interval: 1d
- requested raw candles: 4000 per symbol
- target common-calendar candles: 3500
- study window: 2011-01-01 through 2025-09-24
- common-calendar selection: last 3500 timestamps from the full fixed-window
  intersection
- all symbols must satisfy the target coverage contract
- no partial snapshot is usable after a coverage failure

## Mechanism contract

Q068 uses exactly the same mechanism definitions as Q067.

### E1 — Alpha Common-Mode Throttle

- six fixed alpha sleeves:
  A1_TSM_CONSENSUS,
  A2_CS_MOMENTUM_TOP2,
  A3_RESIDUAL_MOMENTUM_TOP2,
  A5_LOW_BETA_TOP2,
  A1B_52W_HIGH_TOP2,
  A6_OVERNIGHT_TUGWAR_TOP2
- 63 completed holding-period lookback
- mean pairwise Pearson correlation
- activate at >= 0.70 for 3 consecutive observations
- exposure multiplier 0.50 while active
- recovery at <= 0.50 for 5 consecutive observations
- decision at close t uses only completed holding-period returns known before t
- missing sleeve history is fail-closed; no imputation
- exposure transformation only; E1 is not a predictive alpha signal

### E2 — Turnover Hysteresis

- minimum absolute per-asset weight change: 0.05
- nonzero-to-nonzero changes below threshold carry the previous weight
- zero-to-nonzero and nonzero-to-zero changes execute immediately
- applied after fixed target-weight construction and before the next holding-period
  return
- execution/cost accounting remains unchanged

## Required order

1. Fresh coverage
2. PIT mutation validation
3. Only after both pass: separately authorized fixed-rule performance evaluation
   of CONTROL, E1 and E2 under the unchanged 13-gate contract

No gate is changed. No holdout is used for selection.

## Governance

- parameter search: false
- threshold search: false
- asset search: false
- horizon search: false
- variant search: false
- family ranking: false
- holdout selection: false
- promotion: false
- automatic promotion: false
- live execution: false

Q068 is a replication/validation study, not a request to select a replacement
for Q067 after seeing performance.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
