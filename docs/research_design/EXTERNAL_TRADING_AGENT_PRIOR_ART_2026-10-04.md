# External Trading-Agent Prior Art Review — 2026-10-04

## Purpose

Systematically review public trading-agent / quantitative-agent research for architecture, research-process and integrity ideas that are materially relevant to this project.

**Boundary:** this review is design/governance input only. External claims are not scientific evidence for this project. No external performance number, ranking, model claim or promotion rule is imported as evidence.

## Snapshot reviewed

- Repository: `DWR-debug/trading-agent-public`
- Current operational status snapshot: `0899b0fbf9f3528411488789caf435b732c8005d`
- Documentation-only status synchronizer commit: `c7037330e21a409919ea9dd240cb57cb80f86979`
- Date: 2026-10-04
- Safety: `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False`, `AUTOMATIC_PROMOTION=False`

## Systems reviewed

### TradingAgents — TauricResearch

Public repository and changelog reviewed; the current README reports v0.6.0 (2026-10), while the changelog documents the preceding v0.5.x PIT/backtest work.

Relevant architecture:
- role-specialized agents and explicit research/trader/risk stages;
- dated backtest execution over ticker/date grids;
- portfolio-aware context;
- explicit PIT treatment of fundamentals as filed;
- decision records and handling of malformed/unreadable decisions.

High-value lesson for this project:
**historical agent context must be constructed from the information available at the simulated decision time, not from today's retrievable data.** This independently reinforces our acceptance-time / PIT architecture.

What is not imported:
- LLM-generated trading decisions as scientific evidence;
- external reported performance;
- any autonomous promotion rule.

### ai-hedge-fund — virattt

Public architecture and vision materials reviewed.

Relevant architecture:
- one end-to-end pipeline from data through analysis, portfolio/risk and ledger;
- same code path intended across backtest, paper and live operation;
- deterministic order sizing / execution boundaries;
- PIT-by-construction emphasis;
- historical backtests can hide ticker/company/date identity from agent prompts and use relative period labels.

High-value lesson:
**add an agent-context integrity layer that can anonymize asset identity and relative time for retrospective agent tasks.** The deterministic research compiler retains the authoritative mapping; only the agent-facing context is blinded.

This can reduce accidental leakage from model memorization of company/date-specific information without changing the underlying scientific data.

Additional lesson:
**audit replay parity**: the state object and decision semantics used by retrospective simulation should be structurally compatible with the eventual paper/forward path, rather than maintaining separate semantics.

### RD-Agent — Microsoft Research / Qlib ecosystem

Research/development/feedback loop reviewed.

Relevant architecture:
- hypothesis generation;
- code-based implementation and execution;
- feedback from execution results;
- adaptive scheduling across research directions.

High-value lesson already substantially present in this project:
**adaptive resource allocation should optimize information gain, cheap falsifiability, source quality, PIT feasibility, novelty and reproducibility—not realized performance.**

Our current research scheduler already encodes this boundary and explicitly forbids performance/holdout-based routing.

What is not imported:
- performance-driven iterative optimization inside an unfrozen candidate;
- bandit-style selection based on holdout results;
- any external ARR/performance claims.

### FinRobot — AI4Finance Foundation

Relevant design principle:
**models reason; deterministic software computes; agents orchestrate; systems verify.**

This closely matches the current Trading Agent OS separation between AI worker material, deterministic compilers and evidence/governance.

No architectural replacement is warranted; this is a confirmation of the current separation.

### Qlib — Microsoft

Relevant ideas:
- explicit experiment / recorder structures;
- reproducible data, model and run lineage;
- end-to-end quantitative workflow management.

High-value lesson:
our existing trial ledger, immutable evidence, fingerprints, source manifests and receipts already implement the essential version of this pattern.

Potential hardening:
maintain a single provenance envelope across candidate -> source state -> compiler -> run -> receipt -> independent reproduction whenever a new subsystem is introduced.

### AlphaAgent / Alpha-GPT / AlphaForge family

Reviewed as examples of LLM-assisted alpha generation.

Most relevant lesson:
**novelty and complexity must be controlled before accepting generated research ideas.** AlphaAgent, in particular, uses structural/AST-oriented constraints to reduce homogeneous or overly complex generated factors.

Our project already has a stronger domain-specific analogue:
- orthogonal-information-first scheduling;
- minimum mechanism novelty distance;
- universal pre-formal robustness gate;
- no performance-driven candidate selection.

Potential hardening:
when mechanism representations become more formal, consider an explicit structural mechanism fingerprint / similarity audit. This must remain a pre-formal anti-duplication control and never become a performance-ranking mechanism.

### FinMem

Reviewed for layered, time-aware financial memory.

Useful only for a future non-authoritative agent-memory layer. It is **not** adopted as a scientific memory source because retrieval-heavy semantic memory can blur provenance unless every item carries exact source/time lineage.

## Adopt / strengthen / reject

| Idea | Decision | Rationale |
|---|---|---|
| PIT-by-construction for agent-facing historical context | **STRENGTHEN** | Aligns directly with project PIT rules; prevents current-data leakage into retrospective agent analysis. |
| Historical asset/date blinding for agent prompts | **ADOPT AS GOVERNANCE DESIGN** | Useful privacy/information-leakage control; deterministic research mapping remains authoritative. |
| Single replay/state path across backtest/paper/forward | **STRENGTHEN** | Reduces semantic drift between retrospective and operational paths. |
| Invalid/unreadable agent output -> review/quarantine, never silent neutral mapping | **ADOPT** | Prevents malformed semantic output from becoming an implicit HOLD/neutral decision. |
| Information-gain / falsifiability scheduling | **ALREADY ADOPTED** | Current Research OS already encodes this and forbids performance-based routing. |
| Experiment/recorder lineage | **ALREADY ADOPTED** | Trial ledger, fingerprints, receipts and evidence artifacts cover the core need. |
| AST/structural novelty guard | **DEFER / MONITOR** | Current mechanism-novelty gate is sufficient; add only when a formal structural representation can be defined without introducing tuning leakage. |
| Performance-driven bandit research allocation | **REJECT** | Conflicts with frozen-trial discipline and creates optimization pressure before independent validation. |
| LLM-generated alpha as direct evidence | **REJECT** | Agent output is not scientific evidence. Deterministic reproduction is mandatory. |
| Auto-promotion based on agent confidence | **REJECT** | Conflicts with explicit automatic-promotion prohibition. |
| Semantic layered memory as evidence store | **REJECT FOR EVIDENCE; POSSIBLE LATER FOR WORKER CONTEXT** | Provenance risk is too high for the scientific layer. |

## Concrete project implications

### 1. Agent Historical-Context Integrity Contract

For any future agent task that retrospectively evaluates historical market/research states:

1. The agent receives only a frozen, cutoff-bounded context.
2. Exact asset/company identity may be replaced by a run-local stable identifier.
3. Exact calendar dates may be represented as relative period labels where feasible.
4. The authoritative identity/time mapping remains outside the model-facing prompt and is retained in deterministic artifacts.
5. Current web retrieval, present-day fundamentals or later amendments may not enter the historical context.
6. Context construction must emit a deterministic fingerprint.
7. Any mismatch between context fingerprint and frozen task manifest is fail-closed.

This is an **agent-integrity control**, not a new trading signal.

### 2. Replay-Parity Audit

For every future agent-assisted component that reaches paper/forward infrastructure:

- the same state schema should drive retrospective and forward evaluation;
- decision serialization should be identical;
- timestamps/candle boundaries should come from one canonical contract;
- any differences must be explicit, versioned and tested;
- no agent-only shortcut may bypass deterministic risk or execution gates.

### 3. Invalid Agent Decision Semantics

Agent outputs that are incomplete, contradictory or schema-invalid should be classified as **REVIEW_REQUIRED / INVALID**, not silently mapped to HOLD, neutral or another executable meaning.

Agent output remains subordinate worker material and never becomes scientific evidence or performance authorization.

### 4. Research Scheduler Boundary

Retain the current policy:
- orthogonal information first;
- minimum novelty distance;
- cheap falsification;
- source/PIT feasibility;
- reproducibility;
- no performance/holdout-driven routing.

RD-Agent-style feedback is useful only inside that non-performance boundary.

## Immediate research priority

The external scan does **not** displace the current scientific sequence.

Lane A / Formal Readiness:
1. Q121-R6 exhaustive SEC acceptance-time compilation.
2. Q121-R7 revision lineage after valid R6.
3. Q104:I19 historical XBRL + 13F archive completion and independent reproduction.
4. I20 / I22 / M6 according to their candidate-specific gates.

Lane B / Frontier Discovery:
1. Continue orthogonal public-information source/PIT feasibility.
2. Prioritize candidates with high novelty, high cheap-falsifiability and credible historical clock semantics.
3. Reject source-feasible ideas early when candidate-specific PIT cannot be reconstructed.

## Evidence boundary

The following are external prior-art observations, not project evidence:
- authors' reported benchmark/performance claims;
- external candidate rankings;
- external model-confidence claims;
- external auto-trading or promotion claims.

Only project-native deterministic runs, preregistrations, immutable receipts, independent reproductions, Trial Ledger entries and authorization artifacts can create scientific evidence here.

## Primary references

- TauricResearch/TradingAgents: https://github.com/TauricResearch/TradingAgents
- TauricResearch/TradingAgents changelog: https://github.com/TauricResearch/TradingAgents/blob/main/CHANGELOG.md
- virattt/ai-hedge-fund: https://github.com/virattt/ai-hedge-fund
- Microsoft Qlib: https://github.com/microsoft/qlib
- Microsoft RD-Agent: https://github.com/microsoft/RD-Agent
- AI4Finance FinRobot: https://github.com/AI4Finance-Foundation/FinRobot
- AlphaAgent implementation: https://github.com/atanasvasilevjourney/alphaagent
- AlphaAgent paper: https://arxiv.org/abs/2502.16789
- Alpha-GPT paper: https://arxiv.org/abs/2308.00016
- AlphaForge implementation: https://github.com/dulyhao/alphaforge

## Status

**PRIOR_ART_REVIEW_COMPLETED**

No scientific candidate was promoted, ranked by performance, retuned or authorized as a result of this review.
