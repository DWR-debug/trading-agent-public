# Trading Agent — Bounded Subagent Protocol

## Role

The Trading Agent Orchestrator may delegate bounded engineering, QA, adversarial review and research-design work to free AI workers.

A subagent is never the scientific decision authority. Deterministic project tooling, immutable receipts, the Trial Ledger and formal governance remain authoritative.

## Allowed work

Subagents may:
- attack a frozen hypothesis or source/PIT design;
- identify confounds, leakage risks, missing provenance and engineering defects;
- propose fixed falsification or repair tests;
- review code structure and workflow contracts;
- produce a bounded action handoff.

## Forbidden work

Subagents must not:
- inspect or use holdout performance for selection;
- rank candidates by observed returns;
- select assets, parameters, thresholds or horizons from performance;
- modify research gates;
- authorize performance, promotion, orders or live trading;
- create scientific evidence merely by producing an AI response;
- use paid resources.

## Provider routes

### OpenRouter Free

Event-driven bounded adversarial review. The accepted route is fixed to the free router model and deduplicates unchanged task context.

### Groq Free

Independent Q187-Q192 source/PIT adversarial review. It is allowed to run only after a successful free-tier preflight with explicit free-mode attestation and is otherwise fail-closed.

### Gemini / Antigravity

Bounded local Windows worker for manually selected review/engineering tasks. Free-mode verification is mandatory; the worker is not part of the permanent 10-minute research pulse.

### Mistral

Manual-only opportunistic route while provider availability/rate limits remain uncertain.

## Handoff contract

Each task has:
1. immutable `task_id`;
2. fixed repository context files;
3. explicit forbidden operations;
4. maximum runtime;
5. provider and free-only contract;
6. output/receipt path;
7. no-write or bounded-write scope;
8. deterministic follow-up work owned by the Orchestrator.

The Orchestrator must preserve disagreement and uncertainty. No subagent output is treated as a fact until independently verified.

## New-chat continuity

A new `trading agent` chat reads this protocol through the canonical chat entrypoint and current OS state. Existing task contracts, provider state, workflow receipts and current master remain the source of truth.
