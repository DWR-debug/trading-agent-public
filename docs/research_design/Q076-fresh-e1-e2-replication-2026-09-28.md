# Q076 — Fresh E1/E2 Replication with Immutable Input Bundle

## Status

**PREREGISTERED_PERFORMANCE**

Q076 is a fresh symbol-disjoint replication of the unchanged Q067 E1/E2 mechanisms.

## Fixed universe

The symbols are the next source-order coverage batch after Q068 from the same frozen discovery:
- SPG
- CCI
- EQIX
- ESS
- ARE
- WY
- PLD
- KIM

The selection basis is coverage-only and source-order fixed; no performance metric is consulted.

## Mechanisms

Exactly unchanged Q067 definitions:
- E1 Alpha Common-Mode Throttle
- E2 Turnover Hysteresis

All 13 gates remain unchanged.

## Reproducibility hardening

Q068 exposed that persisting only a performance receipt is insufficient when an OHLCV snapshot is missing. Q076 therefore freezes the entire performance input bundle before authorization:
1. aligned canonical OHLCV snapshot;
2. adjusted-close series used by the existing total-return-sensitivity gate;
3. manifest and per-dataset fingerprints.

The performance computation must not perform network access.

## Required order

1. coverage;
2. PIT;
3. input-bundle freeze;
4. separate performance authorization;
5. fixed-rule performance;
6. evidence reconciliation.

No tuning, family ranking, holdout selection, asset selection or promotion is permitted.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
