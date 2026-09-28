# Frontier Execution Order — 2026-09-28

This is an execution-order note, not a performance ranking.

## Rule

A mechanism reaches performance evaluation only after:

1. exact deterministic construction is frozen;
2. PIT/leakage mutation tests pass;
3. free/public historical data feasibility is demonstrated;
4. fresh disjoint inputs are frozen;
5. one-shot authorization is issued;
6. the unchanged 13-gate evaluation and immutable reconciliation complete.

## Current machine-testable feasibility layer

C29 and M4 now have deterministic pure-function implementations and synthetic
PIT tests.

## Next non-performance gates

C30:
- verify SEC archive completeness and filing acceptance-time handling;
- freeze deterministic text representation;
- construct synthetic peer graph tests without performance evaluation.

C31:
- identify a public historical news corpus with stable identifiers and
  reproducible retention; do not substitute a current-only feed.

M5:
- audit historical Russell additions/deletions archive completeness;
- build a frozen event-record schema with publication time and effective time;
- test identifier mapping and future-information mutation.

No step above performs a return backtest or selects a candidate based on outcomes.
