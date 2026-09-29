# Q096 — Frontier Source/PIT Audit — 2026-09-29

**Status:** SOURCE_FEASIBILITY_REVIEWED / PIT_ARCHIVE_AUDIT_PENDING  
**Scope:** public-data feasibility only; no performance evaluation  
**Inventory at review:** 44 candidate mechanisms

## Findings

### SEC information channels

SEC EDGAR exposes public filing history and XBRL APIs without authentication or API keys. The SEC documents real-time dissemination updates and bulk archives, while historical EDGAR filing pages expose accession identifiers and acceptance timestamps.

This supports the following channels as technically viable for further historical archive/PIT work:

- Q072:I2A / I2B — Form 4
- Q072:X1 / X2 — Form 4 combinations
- Q073:I7 — 13F
- Q078:I11 / I12 / I13 — 13F-derived mechanisms
- Q073:I8 / Q078:I14 — 8-K / filing information
- Q082:C22–C25 — shares outstanding via SEC XBRL + OHLCV
- Q088:C25 / frontier:C30 — 10-K/10-Q text

The key remaining blocker is not public accessibility but reconstruction quality: stable identifiers, amendments, historical issuer/security mapping, complete source preservation and exact point-in-time visibility must be demonstrated on the frozen research universe.

### GDELT news channel

The public GDELT event archive exposes daily compressed historical files. This is sufficient to continue C31/C21 feasibility work, subject to deterministic entity-to-security mapping, immutable source preservation, coverage measurement and PIT verification.

### Russell reconstitution channel

FTSE Russell publishes historical reconstitution schedules and dated preliminary/final additions/deletions. The event channel is therefore publicly inspectable, but historical document/version completeness, timestamp preservation and historical security mapping remain mandatory before any performance authorization.

### Options channel

The detailed historical Cboe option quote/trade datasets needed for an implied-borrow construction are commercial data products. Cboe does publish historical option-volume downloads, but the richer historical quote/analytics datasets are offered as purchases/custom deliveries.

Therefore Q078:O1 remains UNPROVEN_PUBLIC_HISTORICAL_SOURCE under the project’s zero-paid-data policy and is not eligible for performance authorization unless a complete free historical substitute is independently established.

## Governance

This review does not rank candidates, estimate expected returns, search parameters, select assets, use holdout data, or authorize performance.

Required order remains:

1. historical archive coverage;
2. PIT/security/entity mapping;
3. immutable source bundle;
4. PIT mutation/reconciliation checks;
5. fresh symbol-disjoint validation;
6. separate one-shot performance authorization.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False