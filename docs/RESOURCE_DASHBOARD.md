# Trading Agent — Resource Dashboard

Snapshot: 2026-10-04 (architecture update)
Repository: DWR-debug/trading-agent-public
Master verified before dashboard commit: 023ec7a1d047b0e924c687300cc3782aae43eec1

## Capacity

| Resource | State / role | Cadence |
|---|---|---|
| Windows self-hosted A | Formal Readiness / local reproduction | 10 min + event-driven |
| Windows self-hosted B | Frontier Discovery / data QA | 10 min + event-driven |
| GitHub-hosted Ubuntu | deterministic frontier, CI, source/PIT work | 10 min / event-driven |
| S10 / Android | deterministic mechanical research/governance QA | 2 h + meaningful changes |
| Free AI | bounded adversarial/design/engineering review | event-driven |

PR #1046 was merged as 07b3fa39b73203fa99eae3968bb393fd0e362e5b. It increased the permanent Windows research pulse to 10 minutes and made deterministic S10 mechanical QA the recurring default.

## Research focus

- Q194 — A: therapeutic substitution pressure × shortage state.
- Q195 — A: EPA inspection → enforcement escalation × facility exposure.
- Q196 — B: patent citation provenance mix × technology exposure.
- Q193 — C / dependency gated: administrative information convergence; no composition before component-level PIT.
- Q197 — frontier: government-demand shock propagation through a frozen supplier network.
- Q198 — frontier: Federal Register public-inspection → publication → effective stage gap.
- Q199 — frontier: patent-publication shock × technology/competitive exposure.
- Q201 — frontier: ClinicalTrials.gov results-first-posted event × sponsor/competitive exposure.

## Scientific boundary

~~~text
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
paid_usage_usd=0
~~~

Operational capacity never creates scientific authorization. Source feasibility and PIT readiness remain non-authorizing; any performance run requires its own exact current authorization, immutable reconciliation and ledger evidence.

## Canonical sources

- Current operational status: docs/CURRENT_STATUS.md
- Resource/orchestration history: docs/RESOURCE_CAPACITY_ORCHESTRATION_2026-10-03.md
- Persistent OS contract: ops/trading_agent_os_state.json
- Acceleration contract: research/governance/persistent_research_acceleration_contract.json

## Status-lag note

The status synchronizer records the source commit that was synchronized. Because status synchronization itself creates a subsequent documentation-only commit, the status snapshot SHA may intentionally trail the absolute master tip by one or more commits. This dashboard therefore identifies the master SHA it was verified against and must not be treated as a scientific receipt.
## Dashboard website and refresh policy

The canonical dashboard UI is **`docs/dashboard/index.html`** with machine-readable snapshot data in **`docs/dashboard/dashboard_data.json`**.

The snapshot is refreshed automatically once per day at **03:35 UTC** by **`.github/workflows/resource-dashboard-update.yml`**, and it can also be refreshed on request through workflow dispatch. The website's **Update now** button opens that GitHub Actions workflow so an authenticated user can run the update immediately; no credential is embedded in the public HTML.

The dashboard is an operational snapshot, not a live runner-control plane and not scientific evidence. It deliberately distinguishes routing assumptions from timestamped execution receipts.

GitHub Pages deployment is defined in **`.github/workflows/github-pages-dashboard.yml`** and publishes the repository's **`/docs`** directory. The Pages root redirects to the dashboard, which is available at **`/dashboard/`** on the repository's Pages domain once Pages is enabled.
