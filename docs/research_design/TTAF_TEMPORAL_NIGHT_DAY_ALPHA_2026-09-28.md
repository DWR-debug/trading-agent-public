# Temporal Tug-of-War Alpha Family (TTAF) — 2026-09-28

Status: DESIGN + OBSERVATIONAL FEASIBILITY ONLY

Recent 2025–2026 research continues to study the information difference between overnight and intraday return components and reports that the two components can have different predictive behavior. One 2026 study attributes part of overnight-return predictability to trading constraints; another 2026 study reports an overnight/intraday “tug-of-war” pattern; a 2026 index study reports short-horizon overnight reversal that varies with volatility. These are research motivations, not project evidence.

TTAF freezes a single first mechanism:

**TTAF_NIGHT_DAY_TUG_OF_WAR_21**

For each asset and decision day:

overnight_t = Open_t / Close_(t-1) - 1

intraday_t = Close_t / Open_t - 1

overnight_21 = sum of the last 21 overnight returns

intraday_21 = sum of the last 21 intraday returns

temporal_wedge_21 = overnight_21 - intraday_21

signal = -temporal_wedge_21

No threshold, horizon, variant, asset or sign search is allowed after freeze. The stage emits only raw phase decomposition and provenance.

Mandatory validation:
- exact OHLCV timing;
- future-bar mutation invariance;
- deterministic replay;
- fresh disjoint coverage before any performance;
- standard cost contract;
- unchanged 13-gate evaluator;
- one-shot performance authorization.

No performance authorization is contained here.
