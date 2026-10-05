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

## 7. New source-backed candidate: Q224 — EDGAR document-demand intensity

SEC EDGAR logs provide a second, materially different information channel: revealed document acquisition after a filing becomes public. The modern 2020-present log schema supplies request timestamp and requested archive path, allowing deterministic recovery of filing CIK/accession. The SEC also documents the missing 2017-2020 interval, schema differences, exclusion of SEC-originating traffic from the newer set, and known data-quality limitations.

Q224 should therefore start as a source/PIT candidate on the 2020-2025 window only. It must not mix the legacy 2003-2017 IP-rich logs into the modern contract without a separate schema bridge.

The literature makes the mechanism more credible than a generic "attention" hypothesis: EDGAR acquisition activity has been associated with future returns and fundamentals, with stronger effects when information is more costly to process. Other work finds attention spillovers across geographically or economically related firms, and recent research studies competitor access specifically.

Project conclusion: Q224 is worth structural feasibility work. Its first tests should be archive completeness, request-to-filing mapping, timestamp semantics, bot/automated-traffic contamination, future-log mutation, and separability from Q130/Q217/Q204/Q104. No return testing is implied by this memo.

## 8. New sub-hypothesis: acquisition demand × processing friction

Q224 and Q217 imply a theoretically interesting interaction: information acquisition demand may carry different meaning when the underlying filing is costly to process. A large acquisition burst for a difficult filing could indicate unusually high perceived information value or unusually high monitoring demand; the same burst for a trivial filing may mean something different.

This is **not** a new top-level candidate and must remain a quarantined sub-hypothesis until Q224 and Q217 independently survive their source/PIT and separability gates. No interaction tuning or threshold search is authorized.

## 9. Agent-system architecture findings

Current open-source agent systems reinforce several project-level engineering patterns:

- TradingAgents v0.6.0 has moved toward saved reports, model-tier separation, automated settlement of past decisions, parallel analysts and stricter run isolation.
- FinMem/FinAgent emphasize layered or diversified memory retrieval.
- A live TradingAgents benchmark highlights large behavioral variation across agent architectures and model backbones.
- KTD-Fin demonstrates that data-side masking is stronger than prompt-only restrictions for controlling memorized historical identity, and that cumulative return can substantially overstate stock-selection skill without factor attribution.
- TrustTrade emphasizes selective consensus based on agreement, temporal consistency and grounding rather than uniform source trust.
- Lumibot's current memory design records actual submitted orders and outcome observations as append-only runtime events, separating factual execution history from agent prose.

Project implication: the Trading Agent should increasingly treat **evidence provenance, temporal validity, source reliability and realized-action reconciliation as first-class state**, while keeping LLM reasoning advisory and bounded. This is an architectural strengthening, not evidence of trading alpha.

## 10. Research priority adjustment

Near-term highest-information work is now:

1. Q224 source/PIT feasibility on SEC EDGAR logs.
2. Q220 XBRL structural mapping and historical-prefix invariance.
3. Q218 mandatory/voluntary event alignment.
4. Q221 procurement public-boundary reconstruction.
5. Q219 options-response join after Q129 integrity confirmation.
6. Q222 external implementation-clock feasibility.
7. Q223 overlap audit; prefer merge/reject unless independent corroboration proves distinct.

No candidate should bypass cheap structural falsification merely because the literature appears economically attractive.

## Source anchors added 2026-10-05

SEC EDGAR Log File Data Sets:
https://www.sec.gov/data-research/sec-markets-data/edgar-log-file-data-sets

SEC EDGAR variables:
https://www.sec.gov/files/variables-edgar-log-file-data-sets.pdf

Li & Sun, Information acquisition and expected returns:
https://www.sciencedirect.com/science/article/pii/S0165188922000884

Lehmann & Posch, Proximity-powered attention:
https://www.sciencedirect.com/science/article/pii/S2214635025000802

Griffin & Wegner, Attention Spillover in EDGAR:
https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5783743

Onuk, Does informing investors tip off competitors?:
https://onlinelibrary.wiley.com/doi/10.1002/rfe.70047
\n

## 11. Q225 — competition-enforcement / remedy-state transitions

The legal/regulatory frontier suggests a distinct candidate class: the **state of a competitive game can change through an investigation, interim restraint, final decision, remedy, appeal or reversal**. The mechanism is the economic state transition, not the legal wording itself.

Legal-source feasibility is stronger when the public boundary is established by regulator or court publication rather than by later financial-media reporting. Initial US discovery found current GovInfo, FTC and CourtListener records, including recent antitrust and patent disputes. This establishes source reachability only; it does not establish a historical PIT panel.

Q225 should remain exploratory until:
- the first reproducible public decision boundary is defined;
- remedy/state taxonomy is frozen ex ante;
- focal/competitor mappings are frozen before outcomes;
- appeals/corrections are represented as lineage;
- Q195 enforcement-escalation overlap is explicitly tested.

The candidate is rejected if it collapses to generic enforcement presence, case counts, legal-text sentiment or an existing contract/procurement lineage.

## 12. Q226 — EDGAR document-age composition

Q226 remains a subcandidate of Q224. Its key distinction is the **composition of requested documents by age**, not total request volume. Current-filing-only acquisition and current-plus-historical acquisition are potentially different information-acquisition states.

This design is motivated by earlier EDGAR research in which simultaneous access to current and historical filings was associated with stronger relations than simple current-filing activity. The modern SEC log schema allows request-level timestamp and filing accession recovery but lacks the richer historical IP identity fields of the 2003-2017 dataset.

Therefore Q226 must not claim to identify "deep research" or investor sophistication directly. At the first feasibility stage it measures only observable aggregate age-composition of EDGAR requests. It survives only if that composition is reproducible and not reducible to Q224 total acquisition intensity, Q130 attention, or Q217 filing complexity.

## 13. Measurement warning for Q224/Q226

The recent literature on observable versus unobservable information acquisition creates an important adversarial control: the public observability of research activity can itself change the research behavior. Therefore an observed EDGAR download series is not necessarily a monotonic proxy for latent information demand. Low observed traffic can mean low demand, substitution to less-visible channels, or strategic suppression of observable traces.

This should become a **mandatory alternative explanation** in any eventual Q224/Q226 PIT/performance design. It is a measurement-control requirement, not a reason to discard the candidate before testing.

## 14. Refined research hierarchy

The present frontier should converge rather than expand indefinitely:

- **Primary candidate:** Q224, only after source/PIT feasibility.
- **Nested mechanism:** Q226, retained inside Q224 unless independent separability appears.
- **Current top wave:** Q218/Q219/Q220/Q221.
- **Unranked external-verification candidate:** Q222.
- **Exploratory overlap test:** Q223.
- **Exploratory legal-state candidate:** Q225.

This keeps the active shortlist constrained while allowing high-information exploratory ideas to be preserved without prematurely promoting them.

## 15. Agent architecture implication

Current open-source systems reinforce that the strongest reusable architecture ideas are not "LLM predicts returns" but:
- persistent factual decision/outcome ledgers;
- explicit separation of proposal/thesis/risk-note/actual-execution events;
- model/provider specialization by role;
- data-side contamination controls;
- factor-adjusted attribution;
- source-aware selective consensus;
- explicit cost and strategy-consistency diagnostics.

These patterns should be treated as engineering requirements for reliability and reproducibility rather than as evidence of alpha.
\n

## 16. Q227 — SEC FOIA information-acquisition state

A materially distinct information channel emerged from the SEC FOIA logs. Unlike Q224, which observes archive-access traffic after public filings, Q227 measures the act of filing a costly request to the regulator for records that may not already be publicly available. A 2026 Review of Accounting Studies paper using SEC FOIA logs reports heterogeneous value relevance across requester groups and argues that the request itself can reveal costly information acquisition; the SEC's current FOIA page exposes monthly CSV logs through August 2026.

This is not project performance evidence. The correct project decision is **P1 source feasibility**, not return testing.

The first implementation gate is historical data semantics: public-log coverage must be frozen, requester category definitions must be reproducible, descriptions must be classified under a predeclared deterministic taxonomy, and targets must be mapped to issuers without hindsight. Commercial archive/due-diligence firms can generate large volumes of requests that are not investor research; bulk-request concentration therefore becomes a mandatory alternative explanation.

The acquisition clock should remain the request submission date. Receipt, closure and disposition are process outcomes and must not be used to move the signal backward in time. The project should also explicitly distinguish requests for already-public filing exhibits from requests plausibly seeking otherwise unavailable regulatory information. A collapse after this separation is a valid kill result rather than a reason to search for another parameterization.

Q227 remains separate from Q224 because the observable object, institutional process and contamination risks differ. It should merge into Q224 only if empirical/source analysis shows that FOIA requests add no distinct information-acquisition object beyond EDGAR archive demand.

## 17. Q227 temporal refinement — private acquisition clock vs public observation clock

Q227 requires a stricter two-clock contract than the initial design. The FOIA request submission date is the latent acquisition clock used by the literature, but it is not automatically a tradable public-data clock. The SEC publishes the logs with a changing frequency: retrospective for 2006–2012, annual/quarterly for 2013–2018, and monthly from 2019 in the 2026 study. The study finds that short-window post-request effects are weak during monthly publication, while more frequent public release strengthens price incorporation around the publication of the requests. Therefore our implementation must model the earliest public log-observation boundary separately and prohibit backdating a public strategy feature to the request date.

This refinement increases Q227's scientific quality but also raises its cost. The feasibility gate must reconstruct publication batches and their historical visibility, assign each request to the earliest public batch, and test whether the observable batch signal remains distinct from Q224 EDGAR demand. A request can be economically informative without being immediately tradable by us; that distinction is mandatory.
