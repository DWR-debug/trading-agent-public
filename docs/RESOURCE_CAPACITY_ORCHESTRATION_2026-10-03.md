# Resource Capacity & Orchestration Snapshot — 2026-10-03

## Purpose

This is a point-in-time orchestration record derived from the supplied Actions-usage report plus the current repository operating model. The supplied report does not specify its historical reporting window, so the numeric usage values below are reported exactly as provided and are not treated as current live utilization.

## Capacity usage

| Resource / lane | Historical report usage | Current cadence | Current role | Why |
|---|---:|---|---|---|
| GitHub-hosted Linux | 3,907 min / 2,734 runs / 68 workflows | continuous/event-driven | CI, deterministic research, source feasibility, reproduction | shortest queues and reproducible execution |
| GitHub-hosted Windows | included in hosted pool | 6h | repo_qa | Windows QA without consuming physical PC slots |
| Self-hosted Windows pool | 3,194 min / 459 runs / 14 workflows | 30m + event/manual | two bounded lanes: local reproduction + data QA | always-routable specialist capacity; receipts remain diagnostic |
| S10 / Android | 499 min / 45 runs | 6h/event-driven | always-routable bounded utility/QA | routing assumes availability; receipt required only for evidence claims |
| ci.yml | 1,243 min / 588 runs | push | x64 + ARM CI | architecture regression coverage |
| self-hosted-continuous-qa.yml | 1,151 min / 75 runs historically | 6h | now hosted Windows repo_qa | historical self-hosted cost no longer repeats |
| permanent-pc-research-loop.yml | 1,117 min / 164 runs | 30m | local reproduction; local-AI when eligible | physical PC specialist role |
| s10-phone-worker.yml | 499 min / 45 runs | 6h | bounded mobile work | utility/acceptance only |
| current-status-sync.yml | 429 min / 429 runs | relevant master push | operational continuity | status must follow master |
| t052-exact-master-ci-gate.yml | 366 min / 329 runs | manual / explicit owner-comment | exceptional exact-master gate | redundant push trigger removed |
| ai-worker-fabric.yml | 267 min / 26 runs | 6h | OpenRouter free scheduled; Gemini/Mistral manual | provider failures must not consume recurring capacity |
| autonomous-control-plane.yml | 202 min / 202 runs | bounded periodic | queue/control coordination | lightweight control plane |
| paper-forward-persistent-mtm-2000.yml | 192 min / 192 runs | scheduled | paper shadow/forward ledger | preserve simulation state |
| workflow-lint.yml | 170 min / 169 runs | push | workflow lint | early workflow regression detection |
| evidence-critic-lab.yml | 127 min / 18 runs | manual/push | local-model benchmark | experimental AI only |
| hosted-research-failover.yml | 123 min / 119 runs | heartbeat-driven | hosted failover | resilience |

## Runner economics from the supplied report

| Pool | Failure rate | Avg run time | Avg queue time | Job runs | Total minutes |
|---|---:|---:|---:|---:|---:|
| Hosted | 20.82% | 31,858 | 3,923 | 3,664 | 3,907 |
| Self-hosted | 25.07% | 143,256 | 85,720 | 1,085 | 3,194 |

The report shows a large historical queue-time difference. It also shows that 79.41% of total reported workflow minutes came from the 10 highest-minute workflows, so a small number of lanes dominate resource consumption.

## Orchestration rules

1. Hosted Linux is the default for deterministic computation.
2. Hosted Windows is the default for Windows-specific QA.
3. The two physical Windows runners are an always-routable bounded specialist pool and may be used in parallel; they remain a specialist substrate rather than the default deterministic compute substrate.
4. S10 and future Samsung phones are always-routable mobile workers. Receipts validate execution/evidence, but lack of a fresh receipt does not mark the resource offline for scheduling.
5. Free AI is used for adversarial design, QA and engineering only. Agreement between models is not evidence.
6. Copilot Free remains reserved for high-value bounded engineering tasks: at most four sessions per month, at most 30 AI credits/session and one concurrent session.
7. Codespaces retain the existing 120 Core-hour monthly budget and its 50/25/25/10/10 soft allocation.
8. The private vault polls hourly and can be forced after critical public changes.

## Optimizations applied

- T052 push trigger removed; explicit/manual invocation retained.
- S10 high-cost probes remain manual/receipt-gated.
- Continuous QA uses hosted Windows rather than physical self-hosted Windows.
- Deep source feasibility increased from 12h to 6h because its actual runtime is small and hosted queue time is much lower.
- Q129 is hosted and split into source-feasibility and independent PIT paths.
- Deterministic frontier remains one 10-step pack every 10 minutes, covering all 30 steps per about 30 minutes without redundant triple execution.
- Scheduled AI uses OpenRouter-free; Gemini/Mistral stay manual under current observed provider instability.
- Vault recovery mirror now polls hourly.
- Heartbeat-based hosted failover is disabled as an automatic routing mechanism under the always-available pool assumption; manual failover remains available.
- The permanent Windows loop uses both runner slots in parallel (`local_reproduction` + `data_qa`).

## Remaining optimization work

- finish Q129 independent PIT;
- get fresh successful receipts for frontier packs 1 and 2 after the robustness repairs;
- complete legacy-workflow review instead of blind deletion;
- expand Q146-Q165 and Q152-Q165 source probes;
- re-check physical Windows and mobile receipts before specialist routing;
- preserve capacity reserve for data-contract/governance blockers.
