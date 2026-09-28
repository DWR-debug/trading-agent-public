# Q085 — Fresh Q069 Validation with Persistent Evidence Bundle — 2026-09-28

**Status:** PREREGISTERED_DESIGN_ONLY  
**Issue:** #584

Q085 is the controlled successor to Q070 after Q070 became a reproducibility block without scientific outcome. The fixed Q069 candidate definitions are carried forward unchanged.

## Fixed candidate bank
- C7 LOW_MAX_21
- C8 LOW_IDIO_VOL_273
- C9 LONG_TERM_REVERSAL_756
- C10 TREND_EFFICIENCY_63
- C11 VOLUME_CONFIRMED_TREND_126

## Coverage contract
Study window 2011-01-01 through 2025-09-24; raw fetch 5000 daily candles; target 3500 common sessions; eight symbols selected only by fixed source-order coverage and disjointness rules.

## Evidence-preservation requirement
The complete frozen snapshot must be persisted to the repository immediately after successful coverage and before PIT evaluation. A later live-source rebuild is never accepted as an equivalent substitute.

## Scientific sequence
Coverage -> immediate snapshot persistence -> network-free PIT -> one-shot performance authorization -> fixed-rule performance -> immutable reconciliation.

No parameter, threshold, asset, horizon, variant or family search; no holdout selection; no promotion; no live execution.

## Safety
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
