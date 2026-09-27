# Q042 — Additional Price-Only Alpha PIT

**Stand:** 2026-09-27  
**Status:** PREREGISTERED / PIT-ONLY

Q042 adds two literature-driven price/OHLCV mechanisms to the candidate research set without testing performance.

## A1b — 52-Week-High / PTH

The fixed signal uses the end-of-session price at a 21-session-skip anchor and computes the current price divided by the trailing 252-session high through that anchor. The two highest values are equally weighted.

The 52-week-high literature identifies proximity to the high as a distinct anchoring variable related to momentum and future returns. Q042 tests only PIT safety; it does not claim predictive validity.

## A6 — Overnight / Daytime Tug-of-War

For each asset, the previous 21 completed sessions are examined. A session contributes one count when its overnight return is positive and its daytime return is negative. The two highest counts are equally weighted at the next decision.

This operationalizes the published overnight/daytime reversal mechanism while keeping the implementation deterministic.

## PIT contract

For deterministic decision points, future bars are changed and the complete signal output must remain unchanged. The next session's OHLC is then changed independently and the decision output must remain unchanged.

## Governance

No performance, OOS, holdout, ranking-by-performance, parameter search or promotion is permitted. A successful result only permits later preparation of a separate fixed-rule performance preregistration on a fresh validation universe.
