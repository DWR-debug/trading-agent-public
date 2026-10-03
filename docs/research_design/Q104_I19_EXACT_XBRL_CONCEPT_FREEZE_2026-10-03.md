# Q104:I19 — Exact XBRL Concept Freeze

## Status

DESIGN CONTRACT FROZEN / PIT-ONLY. No performance authorization.

## Fixed fundamental state

The candidate uses only three exact standard US-GAAP XBRL concepts:

- `us-gaap:NetIncomeLoss`
- `us-gaap:NetCashProvidedByUsedInOperatingActivities`
- `us-gaap:Assets`

The fixed accrual amount is:

`NetIncomeLoss - NetCashProvidedByUsedInOperatingActivities`

The fixed accrual-intensity denominator is average assets across the current and immediately preceding comparable period-end:

`(Assets_current + Assets_prior) / 2`

The resulting state is positive, negative, or exactly zero. Missing aligned facts produce `MISSING`; no imputation or concept substitution is permitted.

The SEC's current EDGAR XBRL Guide explicitly documents `us-gaap:NetCashProvidedByUsedInOperatingActivities` as the appropriate element for cash provided by/used in operating activities. SEC-filing examples also expose `us-gaap:NetIncomeLoss`. These source facts support the concept identity; they do not establish predictive power. citeturn896177search23turn896177search0

## Filing contract

Only 10-K and 10-Q facts are eligible. The latest accepted filing by the decision cutoff is selected only when all three exact concepts are present with the required duration/instant alignment. Amendments remain separate lineage and supersede an earlier filing only from their own SEC acceptance boundary.

The historical study starts at 2013-07-01 because the project's 13F data-set path begins in July 2013; this is a new preregistered research window, not a retrospective change to completed trials.

## Institutional component

The institutional side is supplied by the existing deterministic Q114 13F transition compiler. At issuer level, the fixed state is the sign of:

`count(INCREASE + NEW) - count(DECREASE + EXIT)`

Zero or missing eligible transitions are not silently treated as positive demand.

## PIT / mutation rules

Only information accepted by SEC by the decision cutoff may enter the state. The joined daily state maps to the first eligible XNYS session after the acceptance date.

The compiler must fail closed on future-event injection, row-order mutations, amendment-order changes, or period/instant mismatch.

## Governance

This specification creates no performance authorization, no holdout access, no ranking and no promotion. A separate historical 13F/PIT population and independent reproduction remain mandatory.

## Next gate

`historical SEC 13F archive/security completeness + concept-specific PIT compiler + independent reproduction`
