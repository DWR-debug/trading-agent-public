# Trading Agent — Current Operational Status

**Current operational snapshot:** `db4eeb4ec379805ca321add6a66fa693a8ae69fd`

**Generated (UTC):** `2026-10-03T18:48:29.434365+00:00`

**Repository:** `DWR-debug/trading-agent-public`

> This file is the canonical current operational status. `PROJECT_STATUS.md` is historical reconstruction and must not override it for current operational facts. Scientific evidence remains governed by the trial ledger, immutable evidence/checkpoints and workflow artifacts.

## Current state

### Engineering

- Paper/Shadow/Forward infrastructure: **MERGED** via PR #352, merge commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`.
- The Forward path contains closed-candle market-data ingestion, a persistent update loop and a schema-v2 per-candle MTM ledger.
- Canonical data-layer infrastructure is merged.
- Bounded agent routing uses two queue lanes with fail-closed task contracts.
- **Permanent two-lane research mode: ACTIVE.** Lane A = **Formal Readiness** (advanced Coverage/PIT/compiler/provenance/authorization readiness); Lane B = **Frontier Discovery** (orthogonal source/PIT feasibility and cheap falsification). The two Windows slots are isolated by candidate/trial identity, branches/workflows and output/provenance paths. Cross-lane findings cannot retroactively alter a frozen trial.
- Two physical research slots are capacity only: they **never** create performance authorization. A performance run remains individually fail-closed until an exact current formal authorization exists.
- Continuous QA is scheduled every 6 hours on GitHub-hosted Windows and uses only the bounded `repo_qa` lane; it consumes no self-hosted Windows research slot.
- The deterministic frontier loop runs every 10 minutes on free GitHub-hosted Ubuntu; its three 10-step packs cover all 30 frontier-worker steps.
- Windows Self-Hosted capacity is always routable for bounded local reproduction, data QA, local-AI and hardware-dependent work; two physical slots are intended to run in parallel.
- Latest self-hosted capacity verification: two distinct Windows/X64 runner slots accepted concurrent jobs; see the timestamped capacity receipt.
- S10 phone capability receipt: **S10_UTILITY_ACCEPTED**; routing availability is **ASSUMED_ALWAYS_AVAILABLE** and is independent of receipt freshness.
- S10 current physical online state is intentionally not treated as a routing blocker; the OS availability policy assumes the configured S10 resource is always routable.
- Fresh S10 receipts remain mandatory to substantiate successful execution and device-derived evidence. Receipt freshness does not remove the resource from the routing pool.
- Universal pre-formal candidate robustness gate: **ACTIVE**; structural candidate robustness must pass before PREREGISTRATION, SOURCE_FEASIBILITY, COVERAGE, PIT or PERFORMANCE formal phases.
- S10 output remains non-scientific and cannot authorize performance or promotion.

### Scientific status

- Latest recorded formal result: **performance_completed_no_arm_passed_all_13_gates** for `T-2026-10-01-H06P2R3-PERFORMANCE-01`.
- Q026 is recorded as **DATA_INVALID / NO_SCIENTIFIC_OUTCOME**; it did not produce performance evidence.
- Q023 is recorded as **COVERAGE_VALIDATED** and Q025 as **DATE_PIT_VALIDATED**; these are data-contract findings, not promotion evidence.
- No current candidate is authorized for promotion or live execution.
- Q091 fixed-portfolio performance is **AUTHORIZED** only when the active registry says so; the one-shot performance workflow remains fail-closed and consumes authorization only through immutable reconciliation.

### Active research registry

- Q081-R2: **HISTORICAL_IMPLEMENTATION_INVALIDATED**; infrastructure-rebased corrective reproduction; no performance authorization.
- Q089: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fresh symbol-disjoint successor to quarantined Q086; separate performance authorization remains required.
- Q077-R1: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; coverage-only repair after the original Q077 pool left insufficient unused symbols; no performance authorization.
- Q091: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fixed portfolio architecture on the fresh symbol-disjoint universe; performance authorization flag = **False**.
- Q092: **DIAGNOSTIC_COMPLETED_ONLY**; post-performance Q091 failure-mechanism diagnosis; no performance authorization.
- Q093: **COMPLETED_DIAGNOSTIC_ONLY**; Q091 turnover/cost attribution diagnosis; no performance authorization.
- Q094: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fixed monthly-rebalance successor to the Q091 low-turnover diagnosis; performance authorization flag = **False**.
- Q084, Q088 and Q082 remain **design/feasibility tracks** for unusual market-state, textual-network, rebalance-demand and SEC information channels.
- The unusual-strategy frontier is maintained in `docs/research_design/RESEARCH_FRONTIER_UNUSUAL_2026-09-28.md` and is design-only until feasibility and provenance are established.
- Research OS capability lattice: `research/governance/research_os_source_registry_2026_09_30.json`; it is metadata only and cannot authorize performance.
- Q104 orthogonal candidate wave: **SOURCE_FEASIBILITY_COMPLETED_DUAL_ARCH**; 5/6 data-backed candidates are source-feasible and Q104:R9 is synthetic-only. The archived receipt is `research/evidence/q104_source_feasibility_2026_10_01.json`.
- Q105 historical archive/PIT feasibility: **COMPLETED**, with I21 remaining historically window-limited.
- Q106 shared SEC/Treasury PIT join integrity: **COMPLETED_DUAL_ARCH**.
- Q107 fresh Q104 equity coverage: **COMPLETED**; 8/8 symbols and 3,704 common sessions.
- Q108 real SEC/XBRL/13F/Treasury PIT integration: **COMPLETED_DUAL_ARCH**; 8/8 issuer filings and 8/8 XBRL lineage verified, 13F sample and Treasury chain verified.
- Candidate-specific next gates: I19/I20 = full 13F security coverage; I22 = frozen event-state compiler; M6 = fixed Treasury state reuse; I21 = explicit bounded historical horizon; R9 = synthetic-only.

### Q129 Options Source / PIT

- Q129 historical options source-feasibility: **COMPLETED** on hosted Linux with pinned release hashes verified.
- Independent Q129 PIT/structural reproduction: **REPRODUCED**; workflow run `37123847841`, receipt fingerprint `41d723734f030d1a212f5eb4b3e6467223a5cfcdeb97c77ffa9713f8889c7587`.
- The fixed downstream view preserves raw rows and quarantines quote/calendar anomalies deterministically; same-day use remains **False**.
- This receipt does **not** authorize performance, holdout selection, ranking, tuning, promotion or live execution.

### Verified Source/PIT Frontier Outcomes — 2026-10-03

- **Q121-R1:** `Q121R1_SOURCE_ROUTE_FALSIFIED`; the preregistered SEC browse route failed its subject-issuer identity contract. The verified workflow receipt records 93 discovered entries and 15 deterministic identity checks; receipt fingerprint `9c9a3a4fa05ccc5aa8e59d254c75577abb60b869dd53ff35505b335424cfbf8e`.
- **Q121-R2:** `Q121R2_BLOCKED_BY_Q121R1_FALSIFICATION`; no independent reconciliation was claimed. Receipt fingerprint `fd7b63d9f05e0cf9abf588c9c2d6c2ff02e2ea413927218de6f4e1c29f9fff97`.
- **Q121-R3:** `Q121R3_FORM_INDEX_ROUTE_FEASIBILITY_COMPLETED`; official SEC quarterly form-index route completed for 7 quarters with 61,818 relevant form rows and 3 frozen controls. Receipt fingerprint `a18abdffe2fde48dc4084d420f0a8d5c6ade92727baa23dcecaad481e9452dc1`.
- **Q121-R4:** `Q121R4_MASTER_INDEX_ROUTE_FEASIBILITY_COMPLETED`; independent SEC quarterly master-index route completed for the same 7-quarter window with 61,818 relevant form rows and 3 frozen controls. Receipt fingerprint `3f5616d6ddc18c0f39a10316fe3cbf69e98be2911741552f8a70d133ba94c076`.
- **Q121-R5:** `Q121R5_DUAL_INDEX_POPULATION_RECONCILIATION_COMPLETED`; the form-index and master-index populations are exactly equal as multisets on the frozen window/form scope: 61,818 rows, 61,818 unique canonical keys, zero left-only/right-only keys. Receipt fingerprint `897bc13c5f722d9a701ae7994b237fe7afd233f15cdc5e644061aa674b8f26c1`. This is source-population evidence only; acceptance timestamps, revision lineage and same-day PIT safety remain unproven.
- **Q127-R1:** `Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED`; four fixed historical dates were retrieved and parsed. Revision lineage and same-day PIT safety remain unresolved. Receipt fingerprint `60815a092421762ac1da2a96d003865b72f25eb640778287964a9648cdfc5b74`.
- **Q130-R1:** `Q130R1_SOURCE_FEASIBILITY_COMPLETED`; the frozen historical Wikimedia source probe passed, while publication/revision timing remains outside formal same-day PIT safety.
- **Q131-R1:** `Q131R1_FIXED_WINDOW_NO_MATCHING_FILINGS`; the fixed 2025-09-22 through 2025-09-24 issuer/form window yielded zero matching filings, so no complexity vector was inferred. Receipt fingerprint `e5d5077874d3eaa06b688c7294e83c42d3797da1c9cffdfdb98e067112d07a70`.
- These are discovery/source/PIT findings only. They do not authorize performance, holdout selection, tuning, ranking, promotion or live execution.

### Q171–Q178 Public Source Frontier

- Source-feasibility run: **COMPLETED** on master; Q171, Q172, Q174–Q177 and Q178 passed source probes; Q173 remains license-blocked.
- PIT-readiness: Q171 has a sample historical Common Crawl reconstruction receipt; Q174–Q177 have source-clock/version/revision semantics confirmed but are **not yet candidate-specific PIT-valid**.
- No member of this wave is performance-authorized; no holdout selection, tuning, ranking, promotion or live execution is permitted.

### Q133–Q170 Public Source Frontier

- Hosted discovery/source-feasibility run: **COMPLETED**; 25 source probes passed across Q133–Q170.
- Newly source-feasible candidates include Q137, Q144, Q147–Q151, Q153–Q155, Q157–Q158, Q161–Q169; remaining candidates stay blocked or design-only pending further source/PIT work.
- **PIT-readiness R1 is now ACTIVE** for the 21 source-feasible candidates; it audits candidate-specific clock, revision/version, entity-mapping and historical-archive requirements without evaluating returns or ranking candidates.
- Source-feasibility and PIT-readiness are not performance evidence and do not authorize performance, holdout selection, ranking, tuning, promotion or live execution.

### H06 independent PIT

- Status: **PIT_REPRODUCED_RECONCILED**.
- Independent reproduction workflow: `36843059301`.
- Canonical coverage workflow: `36842998210`.
- Checked PIT decision points: **2545**.
- Semantic check fingerprint: `658ed9e58edb457bf42337fc3ebf081178d157ae88ca0bcca5745112eb60aae7`.
- This is PIT/data-contract evidence only; it does not authorize performance or promotion.

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
- Protected Copilot reserve starts **2026-10-01T00:00:00Z**: at most 4 sessions/month, 30 AI credits/session, 1 concurrent session; actual entitlement is verified at dispatch and no paid fallback/overage is permitted.
- Permanent research continuity uses the two self-hosted Windows lanes every 30 minutes, free-AI rotation every 6 hours when authenticated, always-routable S10/Android utility capacity, and bounded agent dispatch every 2 hours. Hosted research failover is manual-only.

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
