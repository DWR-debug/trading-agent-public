# Trading Agent — Current Operational Status

**Current operational snapshot:** `a1dc0761a6156466d92e086e4559462b7eaefb66`

**Generated (UTC):** `2026-09-28T16:06:31.614094+00:00`

**Repository:** `DWR-debug/trading-agent-public`

> This file is the canonical current operational status. `PROJECT_STATUS.md` is historical reconstruction and must not override it for current operational facts. Scientific evidence remains governed by the trial ledger, immutable evidence/checkpoints and workflow artifacts.

## Current state

### Engineering

- Paper/Shadow/Forward infrastructure: **MERGED** via PR #352, merge commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`.
- The Forward path contains closed-candle market-data ingestion, a persistent update loop and a schema-v2 per-candle MTM ledger.
- Canonical data-layer infrastructure is merged.
- Bounded agent routing uses two queue lanes with fail-closed task contracts.
- Self-hosted Continuous QA is scheduled hourly at minute 15 under label `trading-agent-research`.
- The current architecture claims one runner process; a second process is only a prepared scale path, not an online capacity claim.

### Scientific status

- Latest recorded formal result: **NO_ARM_PASSED_ALL_13_GATES** for `T-2026-09-27-065`.
- Q026 is recorded as **DATA_INVALID / NO_SCIENTIFIC_OUTCOME**; it did not produce performance evidence.
- Q023 is recorded as **COVERAGE_VALIDATED** and Q025 as **DATE_PIT_VALIDATED**; these are data-contract findings, not promotion evidence.
- No current candidate is authorized for promotion or live execution.
- Candidate discovery and PIT feasibility remain the required steps before any new formal performance evaluation.

### Active research registry

- Q081-R1: **PREREGISTERED_WAITING_PREFLIGHT**; corrective reproduction only, no performance authorization.
- Q089: **PLANNED**; clean fresh validation successor to quarantined Q086, not yet performance-authorized.
- Q084, Q088 and Q082 remain **design/feasibility tracks** for unusual market-state, textual-network, rebalance-demand and SEC information channels.
- The unusual-strategy frontier is maintained in `docs/research_design/RESEARCH_FRONTIER_UNUSUAL_2026-09-28.md` and is design-only until feasibility and provenance are established.

### Q067 execution pipeline

- Operational state: **RETIRED**.
- Coverage receipt: **MISSING**.
- PIT receipt: **MISSING**.
- Performance authorization: **False**.
- Performance evidence: **MISSING**.
- Ledger reconciled: **False**.
- Blocking reasons: **obsolete execution path retired; historical evidence preserved**.

This is an operational pipeline summary only; it does not create scientific evidence or select a candidate.

### Q068 execution pipeline

- Operational state: **RETIRED**.
- Coverage receipt: **MISSING**.
- PIT receipt: **MISSING**.
- Performance authorization: **False**.
- Performance evidence: **MISSING**.
- Ledger reconciled: **False**.
- Blocking reasons: **obsolete execution path retired; historical evidence preserved**.

Q068 is a fresh symbol-disjoint validation of the unchanged Q067 E1/E2 mechanisms. This operational summary does not create scientific evidence or select an arm.

### Q070 execution pipeline

- Operational state: **PERMANENTLY_BLOCKED**.
- Coverage receipt: **COVERAGE_PASSED**.
- PIT receipt: **PIT_PASSED**.
- Performance preregistration: **PERMANENTLY_BLOCKED**.
- Performance authorization: **False**.
- Performance evidence: **MISSING**.
- Ledger reconciled: **False**.
- Blocking reasons: **frozen snapshot unrecoverable; execution workflows retired**.

Q070 is the fresh symbol-disjoint validation pipeline for the fixed Q069 OHLCV candidate bank. This operational summary does not create scientific evidence or rank candidates.

### Resource policy

- Paid agent/API budget: **0 USD**.
- Actual available capital: **0 EUR**.
- Hypothetical reference capital: **2000 EUR**, simulation/planning only.
- Legacy 500-EUR operational canary remains separate.
- Deterministic research stays on reproducible runner paths.
- Agent output is never scientific evidence by itself.

## Safety

`PAPER_ONLY=True`

`LIVE_TRADING_ENABLED=False`

`ORDERS_ENABLED=False`

`AUTOMATIC_PROMOTION=False`

## Canonical source order

1. Current operational facts: `docs/CURRENT_STATUS.md` and `research/evidence/current_operational_state.json`
2. Technical truth: current `master`
3. Scientific evidence: trial ledger, immutable evidence/checkpoints and workflow artifacts
4. Project intent: `docs/PROJECT_CONTEXT.md`
5. Historical reconstruction: `PROJECT_STATUS.md`

## Continuity protocol

Every relevant `master` push triggers the status synchronizer. It records the exact source commit being synchronized and updates these two operational-status files in a documentation-only commit. Those files are excluded from the synchronizer trigger, preventing recursive commits.

A future `trading agent` chat must read this file first, then verify live GitHub state before acting.
