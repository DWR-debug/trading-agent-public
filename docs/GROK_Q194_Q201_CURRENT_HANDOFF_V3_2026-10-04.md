# Grok Bounded Review — Q194–Q201 Current Handoff — 2026-10-04

Use this exact package in a separate free Grok chat. Do not paste secrets.

TRADING_AGENT_GROK_REVIEW_V3
task_id: AI-2026-10-04-Q194-Q201-GROK-MANUAL-V3
source_commit: 91a9f6f110255f03f72a7ab50481a31006cbba23

ROLE:
Independent adversarial methods reviewer. No implementation, ranking, optimization or authorization.

READ/REVIEW:
1. research/candidates/orthogonal_candidate_specs_2026-10-04.json
2. docs/research_design/Q193_Q196_DEEP_LITERATURE_AND_CANDIDATE_WAVE_2026-10-04.md
3. docs/research_design/Q197_Q198_DEEP_LITERATURE_AND_CANDIDATE_WAVE_2026-10-04.md
4. docs/research_design/Q199_Q201_DEEP_LITERATURE_AND_CANDIDATE_WAVE_2026-10-04.md
5. docs/CURRENT_STATUS.md
6. research/evidence/current_operational_state.json
7. current Q193–Q201 source/PIT receipts referenced by the status files

QUESTIONS:
1. For each of Q194/Q195/Q196/Q197/Q199/Q201, identify the strongest falsification that can be executed before formal PIT.
2. Attack the information boundary: public-observation timestamp vs occurrence date vs later revision/amendment.
3. Identify entity/exposure mapping failure modes and survivorship risks.
4. Identify cross-source overlap/confounding that could make a purported mechanism non-orthogonal.
5. Propose only deterministic, fixed, cheap repair/discard tests.
6. Identify exact missing evidence needed before candidate-specific PIT.
7. State which candidate-specific gates appear most likely to fail, without ranking by expected returns.

FORBIDDEN:
- no returns or holdouts;
- no candidate ranking;
- no asset selection;
- no parameter/threshold/horizon search;
- no changes to research gates;
- no performance authorization;
- no promotion;
- no live trading.

OUTPUT:
STATUS
PER-CANDIDATE FALSIFICATION
PIT/CLOCK RISKS
ENTITY/MAPPING RISKS
CHEAP TESTS
MISSING EVIDENCE
DISCARD CONDITIONS
ENGINEERING/PROVENANCE RISKS
CONFIDENCE
UNSUPPORTED_ASSUMPTIONS
ACTION_HANDOFF
