# Q011 Orthogonal Information / Alpha Discovery — 2026-09-25

## Status

**Discovery-only. No performance trial is authorized by this document.**

The research question is whether a point-in-time global information-intensity source can provide a fixed, reproducible feature family that is sufficiently distinct from the repeatedly tested portfolio-risk, volatility-scaling, trend-consistency and lifecycle-exit controls.

## Fixed design

- Window: 2026-08-24 through 2026-09-24
- Assets: SPY, TLT, GLD
- Source: GDELT 2.0 Event exports
- Event filter: international event with at least 3 articles
- Features: event count, attention score, source breadth, article count, negative Goldstein magnitude, mean tone

The attention score is the sum over qualifying events of max(1, |Goldstein scale|) multiplied by log1p(number of mentions). This is an ex ante descriptive feature, not an optimized trading threshold.

## Point-in-time rule

For each target market day, only event records strictly between the previous market day and the target market day are used. The target return is previous-close to target-close; a five-market-day forward return is recorded descriptively. Same-day performance is never used to define the information feature.

## No-selection rules

The run does not select assets, parameters, thresholds or a holdout. It reports descriptive feature/return relationships and event-presence summaries only. A positive descriptive relationship is not a promotion signal.

Any future performance test derived from this discovery requires a new preregistration, fresh coverage preflight, fully symbol-disjoint validation data and the unchanged Evidence Contract.

## Safety

PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False; automatic_promotion=False.
