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

## Two-AI operating model

A second AI may be attached as an independent bounded worker under the Orchestrator. The
Orchestrator remains the sole controller of research direction, evidence acceptance, gates,
authorization and promotion.

A second AI may be operated in either of two modes:
1. **Connected worker:** provider/API-backed execution through an explicit adapter, fixed task
   contract, isolated branch/output scope and deterministic verification.
2. **Independent chat worker:** a separate human-opened AI chat receives the same immutable
   task contract as a handoff; its answer is returned to the Orchestrator for independent
   verification. This mode is useful but is not machine-to-machine autonomous control.

The second AI is most valuable for orthogonal adversarial review, source/PIT attack, competing
implementation proposals and failure diagnosis. It must not share mutable candidate state with
the primary Orchestrator and must never decide based on hidden or holdout performance.

### Grok route

Grok is an eligible **optional second reviewer**, but under the current project budget it is
manual/free-chat only. The xAI API requires an xAI API key and credits, so it is not enabled as
an automated project worker while the repository policy remains 0 USD paid API spend.

A future Grok adapter, if the budget policy is deliberately changed, must use the same bounded
task contract, secret handling, isolated outputs and deterministic Orchestrator verification as
every other worker. No API key is placed in chat, commits, issues, artifacts or source files.

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
