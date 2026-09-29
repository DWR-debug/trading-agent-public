# Trading Agent — Current Operational Status

**Current operational snapshot:** `67ba8bb934e2bc73b7db1cfba2260967785d6a7b`

**Generated (UTC):** `2026-09-29T16:21:47.763844+00:00`

**Repository:** `DWR-debug/trading-agent-public`

> This file is the canonical current operational status. `PROJECT_STATUS.md` is historical reconstruction and must not override it for current operational facts. Scientific evidence remains governed by the trial ledger, immutable evidence/checkpoints and workflow artifacts.

## Current state

### Engineering

- Paper/Shadow/Forward infrastructure: **MERGED** via PR #352, merge commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`.
- The Forward path contains closed-candle market-data ingestion, a persistent update loop and a schema-v2 per-candle MTM ledger.
- Canonical data-layer infrastructure is merged.
- Bounded agent routing uses two queue lanes with fail-closed task contracts.
- Self-hosted Continuous QA is scheduled hourly at minute 15 under label `trading-agent-research`.
- Latest self-hosted capacity verification: two distinct Windows/X64 runner slots accepted concurrent jobs; see the timestamped capacity receipt.

### Scientific status

- Latest recorded formal result: **performance_completed_no_arm_passed_all_13_gates** for `T-2026-09-29-095`.
- Q026 is recorded as **DATA_INVALID / NO_SCIENTIFIC_OUTCOME**; it did not produce performance evidence.
- Q023 is recorded as **COVERAGE_VALIDATED** and Q025 as **DATE_PIT_VALIDATED**; these are data-contract findings, not promotion evidence.
- No current candidate is authorized for promotion or live execution.
- Q091 fixed-portfolio performance is **AUTHORIZED** only when the active registry says so; the one-shot performance workflow remains fail-closed and consumes authorization only through immutable reconciliation.

### Active research registry

- Q081-R2: **PREREGISTERED_WAITING_AUTHORIZATION**; infrastructure-rebased corrective reproduction; no performance authorization.
- Q089: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fresh symbol-disjoint successor to quarantined Q086; separate performance authorization remains required.
- Q077-R1: **COVERAGE_VALIDATED_WAITING_PIT**; coverage-only repair after the original Q077 pool left insufficient unused symbols; no performance authorization.
- Q091: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fixed portfolio architecture on the fresh symbol-disjoint universe; performance authorization flag = **False**.
- Q092: **DIAGNOSTIC_COMPLETED_ONLY**; post-performance Q091 failure-mechanism diagnosis; no performance authorization.
- Q093: **COMPLETED_DIAGNOSTIC_ONLY**; Q091 turnover/cost attribution diagnosis; no performance authorization.
- Q094: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fixed monthly-rebalance successor to the Q091 low-turnover diagnosis; performance authorization flag = **False**.
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

### Operator action when runner capacity is being (re)activated

- Open **two PowerShell windows** on the Windows research PC.
- Keep the existing Runner #1 process running in window 1.
- Use window 2 for Runner #2 (LHT-N133732-2).
- When activation/reconfiguration is needed, paste the resulting **non-secret** commands/output into the current "trading agent" chat so the orchestration can verify the live state.
- **Never paste registration tokens, API keys, OAuth tokens or passwords into chat.**
- Do not switch a runner to Windows service mode until local AI authentication has been verified; Windows service mode requires administrative privileges and can change the user/keyring context available to local AI CLIs.

### Resource policy

- Paid agent/API budget: **0 USD**.
- Actual available capital: **0 EUR**.
- Hypothetical reference capital: **2000 EUR**, simulation/planning only.
- Legacy 500-EUR operational canary remains separate.
- Deterministic research stays on reproducible runner paths.
- Agent output is never scientific evidence by itself.
- Protected Copilot reserve starts **2026-10-01T00:00:00Z**: at most 4 sessions/month, 12 AI credits/session, 1 concurrent session; actual entitlement is verified at dispatch and no paid fallback/overage is permitted.
- Both self-hosted Windows runners remain the preferred parallel local capacity; the local AI smoke check runs only after the two research lanes complete.

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
