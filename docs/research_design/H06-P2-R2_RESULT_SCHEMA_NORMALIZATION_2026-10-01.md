# H06-P2-R2 Corrective Performance Gate — 2026-10-01

H06-P2-R2 is an isolated implementation correction following the H06-P2-R1 execution incident.

The scientific scope remains frozen exactly as preregistered for H06-P2:
the same 15-symbol universe and sector map, 252/21 formation rule,
sector-demean residualization, global Top-5/Bottom-5 treatment and raw-global
control, +/-0.10 weights, gross 1.0/net 0.0, unchanged costs/stress and unchanged
13 gates, with the identical frozen coverage, PIT, snapshot and adjusted-close
input bundle.

The single correction is in result metadata construction: the runner now takes
the universe label from the preregistration object rather than from the frozen
input-freeze receipt, which does not contain a top-level `universe` field.

No scientific input, signal, portfolio, cost, horizon, threshold, asset selection,
parameter search, holdout selection, or performance calculation is changed.
