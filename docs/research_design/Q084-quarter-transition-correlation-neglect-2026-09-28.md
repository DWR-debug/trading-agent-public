# Q084 — Quarter-Transition / Correlation-Neglect Candidate Family — 2026-09-28

**Status:** PREREGISTERED_DESIGN_ONLY / unranked  
**Issue:** #583

## Research objective

Q084 introduces a market-state mechanism motivated by Guo & Wachter's September 2026 work on correlation neglect in asset prices. The paper reports negative serial dependence from the second month of a quarter into the first month of the next quarter and links it to predictably repetitive earnings information. citeturn514113search0turn514113search3

This project adaptation is a hypothesis-generation layer only. It creates no performance evidence.

## Candidate M2 — QUARTER_TRANSITION_REVERSAL_STATE

At the end of the second calendar month of each quarter:

1. compute the completed return of the fixed equal-weight market series over that month;
2. for the first month of the next quarter, set the market-state direction to the opposite sign of that completed return;
3. use a deterministic zero-return state of zero exposure.

No alternative month definitions, thresholds, scaling rules, optimization or sign search are permitted.

The mechanism is intended for allocator/exposure research because it is market-wide rather than cross-sectional.

## Candidate C24 — EARNINGS_REPETITION_STATE

Using only public SEC filings:

1. identify a fixed class of earnings-related filings;
2. select reported revenue, net-income and diluted-EPS XBRL facts under an ex-ante deterministic rule;
3. anchor each fact to the filing's EDGAR acceptance datetime;
4. build a quarterly information vector from the values publicly available at that timestamp;
5. compute cosine similarity to the most recent comparable historical quarter;
6. combine the fixed similarity state with the issuer's completed prior-month return direction to create a next-month reversal state.

C24 is explicitly an adaptation, not a replication of Guo & Wachter's research design.

## Feasibility risks

- SEC XBRL fact duplication and taxonomy changes.
- Filing acceptance time versus market-session boundary.
- Multiple filings for the same quarter.
- Restatements and later revisions.
- Missing or non-comparable XBRL facts.
- The market-wide M2 mechanism may be too correlated with existing common-mode risk; this is a reason to test and diagnose, not to tune.

## Research sequence

1. Synthetic unit tests.
2. PIT mutation tests.
3. SEC public-source and XBRL coverage audit.
4. Fixed event/entity mapping.
5. Fresh disjoint input bundle.
6. Separate one-shot authorization.
7. Performance under the existing evidence framework where applicable.

## Governance

No parameter, threshold, horizon, asset, feature, variant or family search; no holdout selection; no automatic promotion; no live execution.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False

## Sources

- Guo & Wachter, NBER Working Paper 35753, September 2026. citeturn514113search0turn514113search3
- SEC EDGAR public filing/XBRL infrastructure already covered by the project's Q071/Q075 source contracts.
