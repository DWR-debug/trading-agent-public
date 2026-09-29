# Research Frontier Expansion — Public SEC Filing Signals (2026-09-29)

## Status

**DESIGN_ONLY_UNRANKED**

This document expands the unusual-candidate frontier with two public-data mechanisms.
It does not authorize performance, ranking, holdout selection, promotion or live
execution.

The two mechanisms are deliberately separated from the existing price-only,
risk-text, news-sentiment, benchmark-rebalance and sleeve-risk families.

## Candidate C32 — INSIDER_OPEN_MARKET_CLUSTER

### Economic question

Do clusters of disclosed insider open-market purchases contain forward information
beyond price-derived signals when the signal is formed only after the filing has
actually been accepted by EDGAR?

### Data channel

Public SEC EDGAR Form 4 filings.

The implementation must use the EDGAR acceptance timestamp as the information
availability boundary. Filing/report dates alone are insufficient because they do
not guarantee that the information was public at the decision time.

### Frozen mechanism concept

Construct a deterministic event state from Form 4 transactions that:
- identifies qualifying open-market purchases;
- excludes grants, option exercises, gifts and other non-purchase transaction types;
- aggregates qualifying insider purchase information over a fixed, ex-ante event
  window once parameters are formally frozen;
- maps each event to the issuer/security using stable SEC identifiers;
- becomes active only after EDGAR acceptance;
- never uses later corrections, future filings or subsequently revised metadata at
  an earlier decision time.

The eventual exposure transformation must be fixed before any coverage/PIT evidence
is inspected.

### Required feasibility gates

1. Historical Form 4 archive completeness for the intended issuer universe.
2. Stable accession/CIK/security mapping.
3. Deterministic transaction-type filtering.
4. Acceptance-timestamp PIT mutation tests.
5. Treatment of amended/corrected filings.
6. Deduplication and multiple-insider aggregation rules.
7. Public-data retention sufficient for a reproducible frozen snapshot.

No performance evaluation is permitted before all gates pass.

## Candidate C33 — LAGGED_13F_HOLDING_CHANGE

### Economic question

Does the publicly disclosed change in institutional equity holdings contain
forward information after enforcing the regulatory publication lag?

### Data channel

Public SEC Form 13F filings.

Form 13F reports are required for qualifying institutional investment managers and
are due within 45 days after the end of the relevant calendar quarter. The project
must therefore treat the EDGAR acceptance/publication timestamp, not the quarter-end
portfolio date, as the earliest decision-time availability boundary.

### Frozen mechanism concept

Construct a deterministic issuer/security exposure change from successive accepted
13F filings:
- normalize holdings by stable security identifiers;
- compare only filings that were publicly available at the decision time;
- aggregate manager-level changes using a fixed ex-ante rule;
- explicitly preserve the reporting lag;
- handle amended filings without retroactively exposing information;
- reject unresolved or ambiguous security mappings rather than imputing them.

The implementation must remain a lagged information signal rather than a current
holdings snapshot.

### Required feasibility gates

1. Historical Form 13F archive coverage and completeness.
2. Stable security/CUSIP/issuer mapping over time.
3. Deterministic treatment of amendments and restatements.
4. Exact publication/acceptance-time PIT handling.
5. Explicit quarter-to-publication lag accounting.
6. Reproducible manager aggregation.
7. Frozen input-bundle reproducibility.

No performance evaluation is permitted before all gates pass.

## Relationship to existing frontier

C32 and C33 are not replacements for C29, M4, C30, C31 or M5.

The current frontier remains broad but unranked. Candidate families must be evaluated
on feasibility and provenance before any performance decision. No candidate may be
promoted merely because its information source is economically intuitive or because
external literature reports an effect.

## Scientific sequence

For each candidate:

1. Design-only review.
2. Ex-ante mechanism freeze.
3. Public-data archive/coverage audit.
4. Synthetic PIT and mutation validation.
5. Fresh, fully disjoint input bundle where applicable.
6. Separate one-shot performance authorization.
7. Unchanged 13-gate evaluation.
8. Immutable reconciliation into the evidence ledger.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

## External provenance

SEC EDGAR documents provide public submission/filing timestamps, including an
EDGAR acceptance timestamp. Form 13F is subject to the statutory 45-day reporting
cycle. These external facts are used only to define the data-access feasibility
boundary; they are not project performance evidence.
