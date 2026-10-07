# Trading Agent — Resource Dashboard

Snapshot: 2026-10-04 (architecture update)
Repository: DWR-debug/trading-agent-public
Master verified before dashboard commit: 023ec7a1d047b0e924c687300cc3782aae43eec1

## Capacity

| Resource | State / role | Cadence |
|---|---|---|
| Windows self-hosted A | Formal Readiness / local reproduction | 10 min + event-driven |
| Windows self-hosted B | Frontier Discovery / data QA | 10 min + event-driven |
| Windows self-hosted C | Long deterministic runs / independent reproduction | event-driven |
| GitHub-hosted Ubuntu | deterministic frontier, CI, source/PIT work | 10 min / event-driven |
| S10 / Android | adaptive deterministic research/governance QA | 20 min + meaningful changes |
| Free AI | bounded adversarial/design/engineering review | event-driven |

PR #1046 was merged as 07b3fa39b73203fa99eae3968bb393fd0e362e5b. It increased the permanent Windows research pulse to 10 minutes and made deterministic S10 mechanical QA the recurring default. Runner C is reserved for long deterministic reproductions and does not create scientific authorization.

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

The live dashboard snapshot is refreshed automatically every **5 minutes** by **`.github/workflows/resource-dashboard-update.yml`**, and it can also be refreshed on request through workflow dispatch. The published Pages snapshot is ephemeral and is not committed back to `master`. The website's **Update now** button opens that GitHub Actions workflow so an authenticated user can run the update immediately; no credential is embedded in the public HTML.

The dashboard is an operational snapshot, not a live runner-control plane and not scientific evidence. It deliberately distinguishes routing assumptions from timestamped execution receipts.

GitHub Pages deployment is defined in **`.github/workflows/github-pages-dashboard.yml`** and publishes the repository's **`/docs`** directory. The Pages root redirects to the dashboard, which is available at **`/dashboard/`** on the repository's Pages domain once Pages is enabled.


## Research Control Board upgrade — 2026-10-05

The dashboard is now a machine-generated operational control board rather than a static capacity list.

It presents four distinct operational layers:

1. **Resource fleet** — configured Windows A/B/C, GitHub-hosted x64/ARM64, S10, Samsung fleet, Free AI, bounded agent queue, Codespaces fallback, Paper Forward/Shadow and GitHub Pages.
2. **Current work board** — active GitHub Actions work with resource/runner, lane, workflow task, job, state, start time and triggering actor. This describes operational assignment only; it is not scientific evidence.
3. **Research board** — active candidate/trial states, lane, next gate and performance-authority flag from the canonical operational state.
4. **AI / agent fabric** — latest persisted provider state for OpenRouter Free, Groq Free, Gemini CLI and Mistral, including free-mode state, model and timestamp.

The generator uses the authenticated GitHub Actions API when the dashboard update workflow runs. Runner details are read from the Actions runner endpoint and current work from Actions workflow runs/jobs. When those APIs are unavailable, the snapshot degrades gracefully instead of inventing status.

The word **worker** on the dashboard refers to an actual runner/provider/job assignment where available. The GitHub workflow **actor** is displayed separately because an actor triggering a workflow is not necessarily the worker executing it.

The dashboard remains deliberately non-authorizing. Active/busy runners, provider availability, research stage and work assignment cannot authorize performance, holdout selection, ranking, tuning, promotion or live execution.

The dashboard snapshot is still refreshed deliberately rather than every few minutes to avoid consuming hosted compute merely to produce activity.


## Candidate progress semantics — 2026-10-07

The candidate pipeline no longer uses expected job duration as a progress indicator. **Gesamtentwicklung** is a deterministic lifecycle index across six common research milestones: design/robustness, source feasibility, coverage, PIT, independent reproduction, and performance validation. **Fortschritt zum nächsten Milestone** is the percentage of successful completed jobs within the currently active candidate workflow; when that workflow has not started, it is 0%. These percentages describe recorded development execution only, not the probability of success, expected return, or authorization state.

## Capacity-state semantics — 2026-10-07

The resource card distinguishes four operational states. **ARBEITET** requires at least one visible active research job for that resource. A busy self-hosted runner without a mapped research job is shown as **RUNNER BESETZT** and does not masquerade as research work. When there is no active research job but a scheduled executable next-gate exists, the state is **AUTO-DISPATCH BEREIT**. **VERFÜGBAR** is reserved for capacity with neither active research work nor a pending executable plan.

Planned work never increments active-job or research-job counts. Runner `busy` is surfaced separately from `current_assignments`, so incomplete runner/job visibility cannot convert planned or unknown work into false active research.
