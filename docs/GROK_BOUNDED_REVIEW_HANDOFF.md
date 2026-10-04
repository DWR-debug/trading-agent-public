# Grok — bounded Trading-Agent review handoff

## Purpose

Use Grok only as an independent reviewer. The Trading-Agent Orchestrator remains responsible for
research direction, evidence acceptance, PIT validation, gates, authorization and promotion.

## Safe manual setup

1. Open Grok in a separate chat/account.
2. Copy the task contract below into Grok.
3. Do not paste API keys, GitHub tokens, passwords, private URLs or secrets.
4. Ask Grok to return only the requested structured review.
5. Paste the returned review back into the Trading-Agent chat. The Orchestrator will verify every
   material claim against repository files, source contracts and deterministic tooling.

## Task contract

TRADING_AGENT_GROK_REVIEW_V1
task_id: <immutable task id supplied by the Orchestrator>
scope: <exact candidate/source/PIT task>
source_commit: <exact master SHA supplied by the Orchestrator>

ROLE:
Act as an independent adversarial reviewer. Do not implement, rank or optimize candidates.

READ/REVIEW:
<exact files/snippets supplied by the Orchestrator>

QUESTIONS:
1. What is the strongest falsification of the proposed mechanism?
2. What PIT/leakage/clock/revision risk remains?
3. What deterministic test would falsify the claim cheaply?
4. What evidence is missing before formal coverage/PIT?
5. What engineering or provenance defect is most likely?

FORBIDDEN:
- no use of holdout performance;
- no ranking by returns;
- no asset/parameter/threshold/horizon selection;
- no promotion or live-trading recommendation;
- no modification of gates;
- no paid API usage;
- clearly label uncertainty and unsupported claims.

OUTPUT:
Return JSON-like sections:
STATUS
FALSIFICATION
PIT_RISKS
CHEAP_TESTS
MISSING_EVIDENCE
ENGINEERING_RISKS
CONFIDENCE
UNSUPPORTED_ASSUMPTIONS

END CONTRACT
