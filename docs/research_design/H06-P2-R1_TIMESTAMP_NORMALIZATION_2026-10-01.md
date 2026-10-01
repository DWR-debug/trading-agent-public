# H06-P2-R1 Corrective Performance Gate — 2026-10-01

H06-P2-R1 is an implementation-only correction trial for T-2026-10-01-H06P2-PERFORMANCE-01.

The scientific scope remains frozen: the same 15-symbol universe and sector map, 252/21 momentum rule, sector-demean residualization, global Top-5/Bottom-5 treatment and raw-global control, +/-0.10 weights, gross 1.0/net 0.0, unchanged costs/stress and unchanged 13 gates. The same frozen coverage, PIT, snapshot and adjusted-close input bundle is reused.

Only execution-boundary compatibility is corrected:
1. accept the canonical frozen coverage receipt's nested `coverage.status=COVERAGE_READY`;
2. canonicalize ISO timestamp strings and market `datetime` values to the same ISO key before adjusted-close lookup.

No scientific data, signal, portfolio, cost, horizon, threshold, asset selection, parameter search or holdout-selection rule changes.
