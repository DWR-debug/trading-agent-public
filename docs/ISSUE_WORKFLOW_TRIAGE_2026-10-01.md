# Issue / Workflow Triage — 2026-10-03

## Scope

This is an operational triage record. It does not create scientific evidence, rank candidates, authorize performance, change gates, select holdout data, promote any strategy, or enable live execution.

## Open engineering issues

| Issue | Role | Decision |
| --- | --- | --- |
| #643 AGENT-027 | agent failure handoff | OPEN; bounded engineering backlog; not on the critical candidate-research path |

## Open research/design issues

| Issue | Role | Decision |
| --- | --- | --- |
| #568 Q073 | expanded orthogonal candidate search | OPEN; broad discovery inventory / lower-priority background |
| #570 Q075 | information-channel coverage/PIT feasibility | OPEN; data-contract lane |
| #573 Q078 | literature-derived orthogonal expansion | OPEN; design lane |
| #578 Q080 | tail/network/state orthogonal bank | OPEN; design lane |
| #580 Q082 | SEC shareholder-experience signal | OPEN; source/PIT feasibility required |
| #583 Q084 | market-state / earnings transition feasibility | OPEN; feasibility complete in registry; follow-up must be explicit before more compute |
| #588 Q088 | textual peer network / rebalance demand | OPEN; distinct textual-information channel |
| #591 frontier | unusual-alpha frontier | OPEN; design-only synthesis / source-PIT progression |
| #744 Q109 | N-PORT / risk / text / insider frontier | OPEN; active registry and downstream PIT gates |
| #755 Q104:I22 | SEC filing-arrival compiler | OPEN; compiler implemented; candidate-specific next gate remains |
| #757 Q118 | composition / bundle compatibility | OPEN; downstream structural contract |
| #761 Q119 | Treasury demand shape | OPEN; live feasibility path active |
| #768 Q120 | CFTC TFF positioning divergence | OPEN; release-date/PIT recovery required |
| #787 Q121 discovery plane | literature-to-hypothesis quarantine | OPEN; capability layer; deterministic intake expansion |
| #819 Q122 | CFTC release-date evidence | OPEN; evidence compiler required for Q120 PIT |
| #855 Q124 | orthogonal source/theory frontier matrix | OPEN; discovery inventory |
| #856 Q126 | SEC filing-arrival × residual momentum | OPEN; newly added discovery wave, now quarantined for routing |
| #857 Q127 | Reg SHO short-pressure × liquidity | OPEN; newly added discovery wave, now quarantined for routing |
| #858 Q128 | options imbalance × liquidity | OPEN; newly added discovery wave, source feasibility first |
| #859 Q129 | gamma concentration | OPEN; newly added discovery wave, source/sign feasibility first |
| #864 Q130 | information-arrival × attention lag | OPEN; newly added discovery wave, attention-clock feasibility first |
| #868 Q131 | information complexity × turnover | OPEN; newly added discovery wave, deterministic complexity/PIT first |
| #869 Q132 | asymmetric residual × systematic state | OPEN; newly added discovery wave, decomposition/PIT first |
| #871 frontier | turnover × information complexity | OPEN; discovery-only; must remain distinct from Q131 and avoid duplicate-lineage convergence |
| #879 campaign | candidate-quality/performance-validity campaign | OPEN; umbrella priority through 2026-10-25 |
| #882 Q121 | SEC beneficial-ownership timing | OPEN; Discovery/PIT-only, 94-event receipt already exists |
| #754 ECL | isolated Evidence-Critic Lab | OPEN; bounded support/metrics infrastructure only |
| #211 milestone | presentable-result milestone | OPEN; umbrella tracking |

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
- Continuous QA: one essential self-hosted repo QA heartbeat lane every six hours; full hosted CI remains the primary broad test suite.
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
