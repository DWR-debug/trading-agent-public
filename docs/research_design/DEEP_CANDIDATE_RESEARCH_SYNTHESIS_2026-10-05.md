# Deep Candidate Research Synthesis — 2026-10-05

## Status

Exploratory research / design-only. This memo creates no performance evidence, ranking, tuning, holdout selection, promotion or live-trading authorization.

## Current external research findings

### 1. Trading-agent architecture

Recent open trading-agent work converges on several architectural ideas that are useful as engineering hypotheses but are not alpha evidence:

- TradingAgents uses role-specialized analysts, bounded Bull/Bear disagreement, structured reports, synthesis and a separate risk-management layer.
- FinPos separates directional reasoning from risk-aware continuous-position adjustment.
- META/FinMem-style work emphasizes episodic or layered memory and retrieval of prior market states.
- TrustTrade emphasizes selective consensus: agreement, temporal consistency and source grounding should be explicit rather than treating every retrieved source as equally reliable.
- Agent Market Arena reports that agent architecture/style can materially affect behavior and recommends continuous, verified evaluation rather than assuming the backbone model is the main determinant.

Project implication: these ideas support bounded evidence-routing, reliability overlays, typed state handoffs and adversarial review, but must remain engineering/review studies unless a separately authorized scientific contract is created.

## 2. Q222 refinement — technology disclosure vs independently observable implementation

The current Q222 contract is defensible only if the external implementation evidence has an independently reconstructable historical public-observation clock.

The strongest implementation discipline is therefore:

1. Freeze the SEC filing prefix at the SEC acceptance boundary.
2. Predeclare a narrow technology taxonomy.
3. Predeclare one or more public implementation-evidence classes.
4. Require each implementation observation to have its own archived/public timestamp semantics.
5. Freeze issuer/entity mappings before any outcome observation.
6. Treat absence of external evidence as UNKNOWN unless historical source completeness is demonstrated.
7. Kill or merge Q222 into Q220/Q217/Q211 if the external evidence channel cannot be historically reconstructed or adds no empirical separability.

Useful public evidence families to investigate first are official patent publication events, government award/contract records, and other primary public disclosures whose historical publication boundary can be reconstructed. Patent publication is attractive for technical implementation claims, while government procurement records may be attractive for deployment/contract realization, but both require historical-clock and entity-mapping verification before PIT use.

## 3. New derived relation — candidate concept, not yet registered

### Q223 concept: Independent corroboration lag / verification gap

Mechanism:
A first public observation of an economically relevant event may be followed by independently sourced confirmation. The information state is not simply the number of channels (dissemination breadth) and not merely the first-arrival latency. It is the time and information-quality gap between first disclosure and independent corroboration.

Potential state variables:

- first_public_observation_clock
- second_independent_confirmation_clock
- confirmation_lag
- number_of_independent_confirmations_at_frozen_boundary
- factual_conflict_before_confirmation
- later_correction_or_retraction_indicator

The potentially distinct mechanism is market processing under incomplete confirmation: an event can be public yet remain epistemically weak until an independent source corroborates it.

This must be treated as a research concept only. It is adjacent to, and may ultimately merge into, Q204 (information latency), Q210 (dissemination breadth), and Q218 (mandatory/voluntary source pairing).

### Cheap falsifiers for Q223

- If confirmation lag is algebraically reducible to first-vs-second publication latency already represented by Q204, merge.
- If channel count explains the state with no incremental structure, merge into Q210.
- If the effect disappears after source-independence classes are frozen, reject.
- If historical corrections/retractions materially rewrite the pre-confirmation state, the historical archive contract is insufficient.
- If first-source and confirmation-source identity mapping cannot be frozen without hindsight, reject.
- If a deterministic event key cannot pair first and confirming observations without manual outcome-informed labeling, reject.

### Feasibility test

Start with primary public sources only. Use a small frozen historical sample and test:

- archive completeness;
- source independence classification;
- exact public-observation timestamps;
- deterministic event/entity pairing;
- correction/retraction lineage;
- mutation tests for future-row insertion and source substitution.

No feature construction or performance testing is justified until these gates pass.

## 4. Additional literature-derived relation worth monitoring

Supply-chain information work suggests that information can propagate at different speeds across economically connected securities. The project already has Q207/Q212 for network diffusion. The useful unexplored interaction is not generic network sentiment, but whether the **order of disclosure across economically linked firms** contains information about which side of the relationship learns first.

This should remain a sub-hypothesis under Q207/Q212 rather than a new top-level candidate unless source/PIT work demonstrates a genuinely distinct object.

Potential state:
- dependency-edge first-observer;
- focal-vs-connected-firm disclosure lead;
- time-to-focal-confirmation;
- local corroboration deficit.

Merge-or-kill condition: if the object is only another representation of network diffusion speed, keep it inside Q207/Q212.

## 5. Historical-government-contract insight

Public procurement research supports a useful decomposition of government award information:

award occurrence != public observability != economic value.

The project should therefore distinguish:
- transaction/action date;
- first historically observable public date;
- base vs option value;
- competition class;
- recipient capability known before the event;
- subsequent production/procurement realization.

This supports Q221's existing design and strengthens the case for a strict public-boundary compiler. It does not support using later contracts to label the original event.

## 6. Information-representation insight

Recent XBRL research suggests that the practical information problem is often not syntax itself but evidence localization, table reconstruction and concept alignment. That reinforces Q220's decision to make reproducible XBRL text-block tags and presentation/relationship structure the primary mapping basis, with manual semantic reassignment prohibited.

A useful engineering corollary is to separate:
- semantic extraction;
- structural verification;
- provenance acceptance.

LLMs may assist the first layer, but deterministic structural checks should control the second and third.

## Decision

Keep Q218/Q219/Q220/Q221 as the active top-candidate wave.
Continue Q222 as unranked design with strict merge-or-kill.
Record Q223 as an exploratory sub-concept pending source/PIT feasibility and overlap audit; do not promote it to the formal candidate inventory yet.
Keep supply-chain disclosure-order as a Q207/Q212 sub-hypothesis unless empirical separability appears.

## External source anchors

TradingAgents:
https://arxiv.org/abs/2412.20138

FinPos:
https://arxiv.org/abs/2510.27251

TrustTrade:
https://arxiv.org/abs/2603.22567

Agent Market Arena:
https://arxiv.org/abs/2510.11695

Cognitive Load and Information Processing in Financial Markets:
https://arxiv.org/abs/2507.07037

VeriFin:
https://arxiv.org/abs/2608.10213

Government procurement dataset:
https://pmc.ncbi.nlm.nih.gov/articles/PMC12328818/

USAspending:
https://www.usaspending.gov/

SEC Form 8-K guidance:
https://www.sec.gov/rules-regulations/staff-guidance/compliance-disclosure-interpretations/exchange-act-form-8-k
