# Q081 — Corrective Q079 E1/E2 Replication

**Date:** 2026-09-28  
**Status:** PREREGISTERED_DESIGN_ONLY / unranked

## Purpose

Q079 reached all recorded data prerequisites but produced no scientific performance result. The self-hosted execution stopped before evaluation because the E2 turnover-hysteresis output exceeded the already-preregistered gross exposure cap of 1.0 at one row.

Q081 is a corrective replication, not a new candidate search and not a performance-based variant selection exercise.

## Fixed inputs

Q081 reuses the exact immutable Q079 coverage receipt, PIT receipt and complete adjusted-close input bundle because Q079 generated no return metrics, no gate results and no holdout-based decision.

- Coverage trial: T-2026-09-28-079-COVERAGE
- PIT trial: T-2026-09-28-079-PIT
- Input bundle: T-2026-09-28-079-INPUT-FREEZE
- Universe: HAL, LRCX, OXY, COF, FIS, FISV, GM, LHX
- Geometry: 3500 common sessions; 2798 research; 700 holdout
- Costs: fee 0.001, slippage 0.0005, stress multipliers 1.5x and 2x
- Gross exposure cap: 1.0; leverage 1; long-only

## Deterministic correction

The six fixed Q067 sleeves, control arm, E1 state machine and E2 hysteresis rule remain unchanged.

Only the existing execution envelope is made enforceable: after the unchanged E2 hysteresis transformation, any long-only row above gross exposure 1.0 is scaled pro-rata to exactly 1.0. This adds no tunable parameter, threshold, asset choice, horizon choice or sign reversal.

This correction is required to make the already-preregistered gross-cap contract executable. It is evaluated symmetrically against the unchanged control and E1 arms under the same cost and 13-gate contract.

## Governance

Before execution Q081 must verify:

1. The Q079 coverage receipt still fingerprints the same frozen snapshot.
2. The Q079 PIT receipt still passes.
3. The Q079 input bundle fingerprint matches the preregistered fingerprint.
4. Safety flags remain paper-only.
5. No selection or holdout-based decision was used.
6. The corrected source contract is frozen and separately authorized.

The first Q079 failure is retained as operational evidence and is not interpreted as a negative or positive return result.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False
