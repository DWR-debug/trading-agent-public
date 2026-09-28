# Q079 — Fresh E1/E2 Fixed Replication — 2026-09-28

## Status

**PREREGISTERED_PERFORMANCE_DESIGN**

Q079 is a fresh, symbol-disjoint replication of the unchanged Q067 E1/E2 mechanisms.

## Fixed universe

The selection source was Q079 coverage-only discovery. The discovery fixed 90 unique established equities in source order, mechanically removed all already-registered symbols and identified 17 coverage-valid candidates.

The first eight coverage-valid symbols are now frozen:
- HAL
- LRCX
- OXY
- COF
- FIS
- FISV
- GM
- LHX

No return, P&L, holdout, rank or gate result was consulted for this selection.

## Mechanisms

Exactly unchanged Q067:
- E1 Alpha Common-Mode Throttle
- E2 Turnover Hysteresis
- symmetric CONTROL arm

All 13 gates remain unchanged.

## Reproducibility hardening

Unlike Q068, Q079 persists the complete performance input bundle before authorization:
1. canonical OHLCV snapshot;
2. adjusted-close series required by total-return-sensitivity accounting;
3. manifest and fingerprints;
4. source contract fingerprints.

The performance job must run without network access.

## Required order

1. Fresh coverage
2. PIT mutation validation
3. Complete input-bundle freeze
4. Separate fixed-rule performance authorization
5. Fixed-rule performance
6. Evidence reconciliation

No tuning, ranking, holdout selection, asset replacement or promotion is permitted.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
