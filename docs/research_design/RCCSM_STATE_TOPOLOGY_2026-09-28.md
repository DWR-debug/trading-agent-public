# RCCSM State Topology — 2026-09-28

Status: FEASIBILITY / NO PERFORMANCE AUTHORIZATION

The next RCCSM layer is a deterministic state description built only from lagged OHLCV data.

## State descriptors

At decision index i:

- trend coherence: fraction of assets sharing the dominant sign of the fixed 63-session return;
- breadth: fraction of assets above their own fixed 200-session simple moving average;
- dispersion percentile: current 21-session cross-sectional return dispersion ranked only against the preceding fixed 252 decision points;
- shock density: fraction of assets whose recent 5-session absolute move exceeds twice their own preceding 63-session mean absolute move.

A separate disagreement layer consumes the frozen Q069 candidate bank and measures one minus mean pairwise Jaccard overlap of the selected asset sets.

All descriptors are bounded in [0,1].

## Timing rule

Only bars at or before decision index i are consumed. Future-bar mutations are mandatory regression tests.

The descriptors do not use future returns as labels, holdout outcomes, optimizer output, or post-hoc selection.

## Research meaning

This creates a clean separation:

mechanism -> state description -> admissibility routing -> risk allocation.

The disagreement variable is deliberately not assigned a performance preference at this stage. It is treated as an observable state descriptor whose empirical role remains open.

## Next stage

RCCSM-2 will use fresh observational inputs only after the state topology passes structural and replay tests on both PC and cloud runners. No market-performance authorization is implied by this document.
