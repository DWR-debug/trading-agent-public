# Q089 — Clean Fresh Q069 Validation — 2026-09-28

## Status

PREREGISTRATION / COVERAGE-PENDING

Q089 is the clean successor to quarantined Q086. Its purpose is a fresh
symbol-disjoint validation of the unchanged Q069 candidate bank.

The design layer does not create performance evidence and does not authorize
performance execution.

## Fixed candidate bank

- C7 LOW_MAX_21
- C8 LOW_IDIO_VOL_273
- C9 LONG_TERM_REVERSAL_756
- C10 TREND_EFFICIENCY_63
- C11 VOLUME_CONFIRMED_TREND_126

These definitions are imported from the frozen Q069 implementation and may not
be changed during Q089.

## Coverage contract

Study window: 2011-01-01 through 2025-09-24.

- raw fetch target: 5000 daily candles;
- common-session target: 3500;
- exactly eight symbols;
- source-order coverage selection only;
- every symbol already present in any registered universe, preregistration or
  prior asset-freeze artifact is excluded by the global prior-research filter.

Coverage is the only allowed basis for symbol selection.

## Evidence sequence

1. Q089 coverage discovery;
2. complete Q089 snapshot persistence to the repository;
3. Q089 input-bundle fingerprint;
4. network-free Q089 PIT mutation tests;
5. final Q089 performance preregistration bound to those exact receipts;
6. one-shot authorization in a separate step;
7. fixed-rule 13-gate performance;
8. immutable reconciliation.

No parameter, threshold, asset, horizon, variant or family search is permitted
after the Q089 design is registered. Holdout data cannot influence any step.

## Provenance

Required trial family:

- coverage: T-2026-09-28-089-COVERAGE
- PIT: T-2026-09-28-089-PIT
- input freeze: T-2026-09-28-089-INPUT-FREEZE
- performance: T-2026-09-28-089-PERFORMANCE

Historical Q086/Q085/Q070 receipts are not reused. Their only role is as
historical context for the quarantine decision.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
