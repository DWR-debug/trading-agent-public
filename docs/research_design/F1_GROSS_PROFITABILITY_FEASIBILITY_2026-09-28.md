# Fundamental Profitability Feasibility — 2026-09-28

## Status
**DESIGN_ONLY / SOURCE_AND_PIT_FEASIBILITY**

This document defines one ex-ante fixed fundamental signal family for future source/PIT feasibility work. It is not a performance authorization and it does not select or rank any existing candidate.

## Motivation
Gross profitability, measured as gross profit divided by book assets, has been documented as a cross-sectional return predictor and as a source that is distinct from price-only momentum. Novy-Marx (2013) studies gross profitability-to-assets; Ball et al. (2015) discuss alternative deflators and operating profitability.

Sources:
- https://doi.org/10.1016/j.jfineco.2013.01.003
- https://doi.org/10.1016/j.jfineco.2015.02.004

These are literature inputs only and are not evidence for this project.

## Fixed candidate definition
**F1_GROSS_PROFITABILITY_ASSETS**

At each daily decision timestamp:

1. For each eligible U.S. equity, identify the most recent annual filing whose EDGAR acceptance timestamp is at or before the decision timestamp.
2. From that filing, obtain annual Revenue, CostOfGoodsAndServicesSold (or the explicitly documented equivalent), and Assets using an ex-ante fixed taxonomy/tag map.
3. Compute:

   gross_profitability = (revenue - cogs) / assets

4. At the rebalance decision, rank the complete eligible universe by this value and use the two highest-ranked securities with complete valid histories.
5. The signal remains fixed until the next scheduled rebalance.
6. Missing or ambiguous facts are a hard failure; no imputation or fallback search is permitted after observation.

No thresholds, lookbacks, alternative tag maps, rebalance frequencies, asset counts, or variants may be searched after observing outcomes.

## Required source/PIT gates
The family must not enter performance until all of the following are independently demonstrated:

- public source accessibility from the canonical runner;
- complete ticker/CIK and historical security-identity mapping;
- deterministic annual-filing selection;
- exact filing acceptance timestamp available for every used observation;
- deterministic XBRL fact selection with context/fiscal-period checks;
- amended/restated filing handling fixed ex ante;
- future-filing mutation leaves all prior decisions unchanged;
- next-session mutation leaves all prior decisions unchanged;
- complete coverage for a fresh symbol-disjoint validation universe;
- immutable raw/source fingerprints persisted before performance;
- explicit preregistration and separate one-shot authorization.

Historical revised XBRL data must never silently replace a previously visible filing fact in a past decision.

## Economic / research role
This family is intentionally orthogonal to the current Q069 price/volume candidate bank. It is a slow fundamental signal, not a risk overlay.

The first objective is **feasibility**, not profitability measurement. A DATA_INSUFFICIENT result is a valid outcome if the public historical source cannot support complete PIT reconstruction.

## Safety
`PAPER_ONLY=True`
`LIVE_TRADING_ENABLED=False`
`ORDERS_ENABLED=False`
`AUTOMATIC_PROMOTION=False`

No performance authorization is created by this document.