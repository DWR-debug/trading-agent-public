# Q067 — Fixed Mechanism Freeze

## Status

PREREGISTERED_DESIGN_ONLY_FROZEN

The exact implementation parameters are frozen before fresh coverage or PIT evidence is
inspected. No performance evaluation is authorized by this freeze.

## Fresh validation universe

ANSS, ROP, NVR, ZION, SLB, EIX, K, CCL

The eight titles were selected only as a fixed, fresh, cross-sector universe that is absent
from both the immutable trial ledger and the registered research-universe catalogue at freeze
time. Any overlap at execution fails closed. No replacement or performance-based asset selection
is permitted.

Coverage contract:

- 4,000 requested daily candles per symbol;
- 3,500 common daily candles as the frozen study snapshot;
- fixed study window 2011-01-01 through 2025-12-31;
- canonical data layer only.

## E1 — Alpha common-mode throttle

At each decision close, calculate the mean pairwise Pearson correlation of the six completed alpha
sleeve return streams over the previous 63 holding periods that are fully known before the decision
close.

Activation requires mean correlation at least 0.70 for three consecutive decision observations.
Once active, aggregate alpha exposure is multiplied by 0.50.

Recovery requires mean correlation at most 0.50 for five consecutive observations. State
transitions are evaluated at the decision close and affect the subsequent holding period.

The six alpha sleeves are evaluated symmetrically with equal sleeve weight:
A1_TSM_CONSENSUS, A2_CS_MOMENTUM_TOP2, A3_RESIDUAL_MOMENTUM_TOP2, A5_LOW_BETA_TOP2,
A1B_52W_HIGH_TOP2, A6_OVERNIGHT_TUGWAR_TOP2.

Missing sleeve history is a hard error; no imputation is allowed.

E1 is an exposure transformation, not a predictive signal.

## E2 — Turnover hysteresis

After the fixed six-sleeve equal-weight target is generated, apply a 0.05 absolute-weight
per-asset deadband.

For nonzero-to-nonzero target changes below 0.05, carry the previously held weight forward.
Zero-to-nonzero and nonzero-to-zero transitions execute immediately.

The rule changes implementation churn, not signal formation. Cost accounting remains the
unchanged repository execution/cost contract.

## Scientific sequence

1. Freeze the implementation (this document).
2. Run fresh symbol-disjoint coverage.
3. Run PIT mutation validation on the frozen snapshot.
4. Only after both gates pass may a separate fixed-rule performance study be created for E1 and E2.
5. Any later performance study uses the unchanged 13-gate evidence contract and cannot use holdout
   outcomes for family or parameter selection.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

## Explicit non-actions

No backtest is performed here. No holdout is opened. No parameter or asset search is performed.
