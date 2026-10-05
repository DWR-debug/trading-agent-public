# TradingAgents Architecture Replication — 2026-10-05

## Status

Design-only research / engineering study. This document does not authorize market-performance testing, candidate ranking, tuning, holdout selection, promotion, or live execution.

## External source

Xiao, Sun, Luo & Wang, "TradingAgents: Multi-Agents LLM Financial Trading Framework", arXiv:2412.20138v7 (2025-06-03).

The paper proposes a simulated trading-firm architecture with specialized analyst roles, a bounded bull/bear research debate, a trader, a three-perspective risk-management discussion, and a fund-manager layer. It also uses structured reports around free-form debate and assigns model classes by task complexity.

## What is potentially useful for Trading-Agent-OS

The potentially transferable contribution is architectural rather than an accepted alpha claim:

- independent role-scoped evidence extraction;
- bounded adversarial disagreement before synthesis;
- explicit separation between research conclusion and risk screening;
- structured state handoffs surrounding natural-language deliberation;
- task-specific model routing;
- preservation of an auditable decision chain.

These elements overlap with existing project components such as the decision adapter, shadow replay/ledger, reliability overlay and bounded free-AI review fabric.

## What must not be imported

The paper's reported trading results are not admissible project evidence. The paper evaluates 1 January through 29 March 2024, uses AAPL/GOOGL/AMZN for the headline comparison, and reports unusually high Sharpe ratios; the authors explicitly note that the highest Sharpe exceeds their expected empirical range and attribute this partly to the short, low-pullback test period and high per-prediction LLM/tool cost.

The paper's external data/provider architecture is also not imported into the project. Every project research input remains subject to our source, point-in-time, identity, revision-lineage and authorization contracts.

## Falsifiable architecture hypothesis

H_A1:
A bounded multi-role pipeline with independent evidence reports, explicit adversarial disagreement, structured synthesis and a separate risk screen can improve deterministic decision/review quality relative to an otherwise equivalent single-pass or unstructured pipeline.

This is an engineering/review hypothesis first. It is not a claim that the architecture produces alpha.

## Cheap falsification plan

1. Compare parallel independent evidence extraction against a single combined prompt on frozen synthetic and real project evidence packets.
2. Measure whether bull/bear or adversarial review surfaces contradictions that a single-pass reviewer misses.
3. Verify that debate outputs are summarized into a typed/structured state without losing provenance identifiers or silently changing source facts.
4. Verify that risk-screen outputs cannot mutate the original evidence packet and cannot create performance authorization.
5. Verify that disagreement is preserved as a first-class state rather than coerced into HOLD/neutral by parsing.
6. Verify deterministic replay: identical frozen inputs produce identical structural decisions or an explicit non-deterministic annotation.
7. Test task-specific model routing only as a resource/quality question; do not optimize market returns.

## Required invariants

- no shared mutable research state across isolated research lanes;
- no future data or outcome-derived fields in pre-decision contexts;
- no LLM output is scientific evidence;
- no architecture result creates performance authorization;
- no silent fallback from malformed/ambiguous model output to a tradeable HOLD;
- full provenance/fingerprint chain retained for every accepted decision packet;
- shadow/paper boundary remains fail-closed.

## Proposed bounded implementation study

A deterministic architecture benchmark should exercise existing project components rather than create a parallel trading system:

Evidence packet
→ independent role-scoped reviewers
→ bounded adversarial disagreement
→ structured synthesis
→ separate risk/reliability overlay
→ decision_adapter
→ shadow_replay / shadow_ledger

The benchmark should use frozen project fixtures and synthetic mutations first. Only after structural tests pass may a later, separately authorized study ask whether any architecture change affects market-performance metrics.

## Relation to existing candidates

The study is orthogonal to Q197/Q199/Q201/Q202-Q204 and must not be merged into their market hypotheses.

It may inform the existing reliability/consensus overlay and the OS agent-mesh design. Any later composition is a new frozen contract and requires independent validation.

## Research decision

INITIAL ASSESSMENT: INTERESTING_AS_ARCHITECTURE / NOT_YET_AN_ALPHA_CANDIDATE.

Next gate: implement and execute the bounded deterministic architecture benchmark, then adversarially review its failure modes. Do not initiate market-performance testing from this paper alone.

## Source

https://arxiv.org/pdf/2412.20138
