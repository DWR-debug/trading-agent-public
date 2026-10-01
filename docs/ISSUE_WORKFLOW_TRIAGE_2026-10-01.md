# Issue / Workflow Triage — 2026-10-01

## Scope

This is an operational triage record. It does not create scientific evidence, rank candidates, authorize performance, change gates, select holdout data, promote any strategy, or enable live execution.

## Open engineering issues

| Issue | Role | Decision |
| --- | --- | --- |
| #641 AGENT-025 | bounded agent scope gate | ACTIVE; third bounded Copilot attempt in progress after publish/credit fixes |
| #642 AGENT-026 | bounded agent capacity lease | KEEP OPEN; independent governance hardening |
| #643 AGENT-027 | agent failure handoff | KEEP OPEN; contract corrected to preserve protected-path invariant |

## Open research/design issues

| Issue | Role | Decision |
| --- | --- | --- |
| #568 Q073 | expanded orthogonal candidate search | KEEP OPEN; distinct research-design lane |
| #570 Q075 | information-channel coverage/PIT feasibility | KEEP OPEN; data-contract lane |
| #573 Q078 | literature-derived orthogonal expansion | KEEP OPEN; design lane |
| #578 Q080 | tail/network/state orthogonal bank | KEEP OPEN; design lane |
| #580 Q082 | SEC shareholder-experience signal | KEEP OPEN; source/PIT feasibility required |
| #583 Q084 | market-state / earnings transition feasibility | KEEP OPEN; feasibility track |
| #588 Q088 | textual peer network / rebalance demand | KEEP OPEN; distinct textual-information channel |
| #591 frontier | unusual-alpha frontier | KEEP OPEN; design-only synthesis / source-PIT progression |
| #211 milestone | project-level presentable-result milestone | KEEP OPEN; umbrella tracking |

## Closed / historical issues

The following were closed after verifying that their work is complete or historically superseded while preserving evidence:

- #343 zero-job anomaly: current hosted execution is operating; historical anomaly remains preserved.
- #536 Q069 completed design; frozen candidate bank is used by successors.
- #587 Q081-R1/R2 historical correction chain.
- #589 Q089 completed one-shot performance validation; no arm passed all 13 gates.
- #693 Q081-R3 implementation-invalid historical correction.
- #694 Q081-R4 completed corrective reproduction; no further authorization.

## Workflow policy

### Active lanes

- CI / Workflow Lint: technical integrity.
- Autonomous Resource Control Plane: bounded issue discovery and routing.
- Autonomous Agent Request Queue: bounded engineering execution with protected Copilot reserve.
- Permanent Self-Hosted Research Loop: two parallel Windows runner lanes plus local AI smoke.
- Continuous QA: four self-hosted QA lanes.
- Paper Forward / Paper Forward 2000 EUR: operational shadow/MTM only.
- Public Frontier Feasibility: design/source/PIT feasibility only.
- H06 Master Coverage Repair + H06 Independent Reproduction: current PIT infrastructure validation.

### Historical auto-trigger cleanup

Completed one-shot/historical execution workflows for C29/Q067/Q068/Q070/Q077R1/Q081R1-R4/Q091/Q094/Q095 were converted to manual-dispatch only. Their files and evidence remain preserved.

## Known operational fixes

1. H06 cross-workflow artifact retrieval now uses `actions/download-artifact@v8`.
2. H06 Windows verification/reconciliation no longer depends on the machine PowerShell execution policy.
3. Copilot session cap is aligned with the current CLI technical floor of 30 AI credits.
4. Copilot publication falls back to the actual working Git branch and refuses direct publication to `master`.
5. Copilot protected budget state reads now fail closed instead of treating transient read failures as an empty budget.
6. Control-plane issue collection no longer hides valid `agent` / `agent-ready` tasks behind an `agent-cli-ready` API filter.

## Current safety

`PAPER_ONLY=True`
`LIVE_TRADING_ENABLED=False`
`ORDERS_ENABLED=False`
`AUTOMATIC_PROMOTION=False`

Paid agent/API budget remains 0 USD.
