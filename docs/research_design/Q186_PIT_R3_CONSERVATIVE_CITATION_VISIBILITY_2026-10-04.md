# Q186 PIT-R3 — Conservative Citation Visibility Contract

## Purpose

Tighten the Q186 point-in-time contract without treating a bulk-data citation field as a public-observation timestamp.

The objective is to determine when a backward citation from a downstream patent can be admitted to the pre-grant technology graph of an upstream patent grant.

This is source/PIT feasibility only. It never evaluates returns, selects assets, tunes parameters, ranks candidates, authorizes performance, promotes a candidate or permits live trading.

## External source findings

Current PatentsView documentation exposes a `patent_date` field described through grant-date examples and a `citation_date` field for patent citations. PatentsView also states that its data are derived from USPTO full-text data and are research data rather than the authoritative USPTO record. Therefore `citation_date` must not be silently promoted to a public dissemination timestamp.

The conservative route is to anchor visibility to the actual public grant document of the citing patent, not to the later bulk-data refresh date and not to an ambiguous citation field.

## Conservative edge rule

For a candidate edge

`upstream patent -> downstream patent`

the edge is eligible for a pre-event graph at an upstream grant date only when all of the following are proven:

1. The downstream/citing patent grant document is independently identified.
2. The exact citation to the upstream/cited patent is present in that grant document.
3. The downstream/citing patent grant date is strictly earlier than the upstream patent grant date.
4. Same-day grant ties are excluded because intraday ordering is not established by the contract.
5. The citation evidence is frozen by content hash and retains its exact source URL/document identity.
6. Later PatentsView refreshes, assignments, corrections or withdrawals cannot rewrite the frozen historical observation.

The resulting public-observation boundary is the citing patent's grant date as a conservative upper bound. This is deliberately later than some possible real public-availability times, so it can reduce coverage; that loss must be measured, not optimized away.

## What this resolves

This route can potentially resolve the currently-unproven citation-publication ordering gate for a conservative subset without assuming:

- `citation_date` is a dissemination clock;
- bulk refresh time is a historical information time;
- application-publication timing is known for every citation;
- same-day patent events have an established intraday order.

## What remains unresolved

The following still require candidate-specific evidence:

- completeness census of the historical grant/citation population;
- document-level retrieval completeness and missing/withdrawn-document quarantine;
- exact assignee-to-issuer mapping and coverage;
- correction/withdrawal lineage;
- independent reproduction;
- coverage loss caused by the conservative grant-date rule.

A future extension may admit pre-grant-publication citations, but that requires a separate source/clock proof and must not be introduced as a silent relaxation of this contract.

## Scientific boundary

The R3 route is a PIT/source compiler contract only.

Forbidden in this work:

- performance measurement;
- holdout selection;
- asset selection;
- parameter/threshold/horizon search;
- event-window search;
- candidate ranking;
- promotion;
- live execution.

Safety remains:

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `ORDERS_ENABLED=False`
- `AUTOMATIC_PROMOTION=False`
