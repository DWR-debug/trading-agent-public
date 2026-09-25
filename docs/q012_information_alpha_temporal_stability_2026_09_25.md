# Q012 Information-Alpha Temporal Stability Diagnostic — 2026-09-25

## Status

**Diagnostic-only. No performance trial is authorized by this document.**

Q012 tests whether the fixed Q011 GDELT information features retain their descriptive relationships over a materially longer historical window.

## Fixed design
- Window: 2026-03-29 through 2026-09-24 (180 calendar days)
- Assets: SPY, TLT, GLD
- Source: GDELT 2.0 Event export
- Event filter: international event with num_articles >= 3
- Features: event count, attention score, source breadth, article count, negative Goldstein magnitude, mean tone

## Stability analysis
For the common market-day observations, the ordered sample is split into its first and second half. For every fixed asset-feature pair, Pearson and Spearman relationships are reported for both halves, together with sign consistency and absolute correlation change.

No feature is selected, no threshold is optimized, no asset is selected and no holdout is used. A later performance study, if justified, requires a new preregistration and the unchanged evidence contract.

## Point-in-time rule
Event features for a target market day use only events strictly after the previous market day and strictly before the target market day. Target returns are measured from previous close to target close; the five-day return starts at the target close. Same-day performance is not used.

## Safety
PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False; automatic_promotion=False.
