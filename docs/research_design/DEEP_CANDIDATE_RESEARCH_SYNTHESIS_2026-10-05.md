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


## 18. Current TradingAgents / FinAgent architecture scan — implementation implications

Current open-source agent frameworks have moved materially toward deterministic run state rather than treating an LLM conversation as the experiment itself.

TradingAgents v0.6.0 now separates model providers by reasoning tier, settles prior decisions across all tickers while analysis continues, preserves run settings in reports, and maintains stricter point-in-time behavior for historical backtests. The project has also added parallel analyst execution and unattended CLI runs. These are engineering patterns, not alpha evidence.

Open-Finance-Lab's FinAgent Orchestration framework goes further with a DAG Planner, Orchestrator, Registration Bus, specialized Data/Alpha/Risk/Cost/Portfolio/Execution/Backtest/Audit pools, and a Memory Agent storing structured execution traces. Its stated architecture is explicitly graph- and memory-based.

Project implication:
- preserve the current separation between hypothesis generation, source/PIT compilation, scientific authorization and execution;
- make the experiment manifest, data clock, source lineage and outcome settlement first-class state;
- keep agent prose advisory and require deterministic gates for every transition that can influence scientific authority;
- prefer parallel independent analyst/source workers but serialize only the immutable decision boundary and reconciliation;
- strengthen the dashboard around event timelines and provenance, because observability is itself a reliability feature.

No external framework performance claim is project evidence.

## 19. Federal Register public-inspection stage — sharpen Q198, do not create a new candidate

A deeper source review substantially strengthens Q198 rather than creating a separate family.

Federal Register rules state that documents are generally filed for public inspection at least one business day before publication, and that the date and hour of filing are explicitly noted. Current Federal Register issues continue to state that documents are available for public inspection before official publication unless earlier filing is requested.

This creates a clean three-stage information clock for Q198:

1. document filed for public inspection;
2. official Federal Register publication;
3. effective date.

The economically relevant insight is therefore not simply "regulatory news." It is a **pre-publication public-observability interval**. The same document can move from legally/publicly inspectable to officially published without changing its substantive content.

Implementation consequence:
- use the public-inspection filing timestamp as the earliest admissible public boundary when reproducible;
- retain official publication and effective dates as later state transitions;
- model emergency/early-inspection deviations separately from the regular schedule;
- prohibit use of agency submission/receipt times that are not publicly observable;
- test whether the pre-publication interval is deterministic and sufficiently populated before any outcome work.

The current Q198 issue already contains the correct stage-transition structure, so the result is a contract refinement, not inventory expansion.

## 20. SEC EDGAR request topology — strengthen Q224/Q226

SEC's modern EDGAR log schema exposes request time and the archive path of the requested asset. The archive path encodes the filer CIK and accession number, which permits deterministic filing-level attribution.

This supports a richer but still source-derived view than total request count:

- current-filing vs historical-filing access;
- index-page vs document/exhibit/structured-data access when the path permits the distinction;
- breadth of distinct assets requested within one filing;
- temporal depth of requests following a filing;
- ratio of contextual/historical access to immediate focal-filing access.

Q226 should remain nested under Q224 until this topology demonstrates incremental information not reducible to total demand.

Important adversarial control:
- modern logs cover 2020 onward but have a missing 2017–2020 interval and differ materially from the older 2003–2017 data;
- SEC warns of lost/damaged files and extraction limitations;
- the newer dataset excludes SEC-originating searches.

Therefore no stitched long panel should be assumed. The first gate remains an immutable modern-window census and mutation test.

## 21. SEC post-acceptance correction lineage — exploratory risk-state idea, not a new top-level candidate

SEC documentation confirms that filer corrective disclosures usually leave both the original filing and the corrective filing publicly available. SEC documentation also states that post-acceptance corrections/deletions can alter EDGAR indexes, with daily, feed and weekly-rebuilt index behavior depending on when the correction is processed.

This suggests a possible future **filing-stability / correction-history risk state**:
- issuer's historical rate of substantive corrective disclosures;
- latency from initial acceptance to correction;
- concentration of corrections by form/section;
- recurrence of the same correction class.

However, current feasibility is not yet sufficient for a separate candidate. The correction process mixes administrative and substantive errors, and a robust historical prefix requires reconstructing the exact state of EDGAR indexes at the relevant date. Therefore:
- keep this as a research note under Q131/Q204;
- investigate source observability first;
- do not promote unless the historical correction state is mechanically reconstructable and empirically separable from disclosure complexity.

## 22. New economic-system relation — information acquisition has two markets, not one

The Q224/Q227 work suggests a broader unifying hypothesis:

**Information acquisition can have a latent/private clock and a separate public-observation clock.**

Q224: market participant retrieves already-public EDGAR material.
Q227: participant requests potentially non-public regulatory records.
Q198: regulator's document becomes publicly inspectable before official publication.

The common object is not "attention." It is the **conversion of costly or staged information acquisition into public observability**.

This creates a useful cross-candidate control layer:
- acquisition cost/proximity;
- latent acquisition time;
- first public observability;
- subsequent confirmation/publication;
- later correction or state transition.

The control layer must never merge otherwise distinct economic mechanisms, but it can provide a common causal-clock vocabulary for avoiding accidental look-ahead.

## 23. Decision after external scan

- Q224: remain primary source/PIT candidate.
- Q226: remain a nested Q224 mechanism until independent separation is demonstrated.
- Q227: remain P1 and separate from Q224, with the two-clock contract mandatory.
- Q198: strengthen around public-inspection -> publication -> effective chronology; do not create a new candidate.
- SEC correction-history idea: exploratory risk-state note only, not candidate inventory.
- Agent-system findings: implement as provenance/orchestration requirements, not alpha claims.

## Sources added in this scan

TradingAgents current repository:
https://github.com/TauricResearch/TradingAgents

FinAgent Orchestration current repository:
https://github.com/Open-Finance-Lab/AgenticTrading

SEC EDGAR log variables:
https://www.sec.gov/files/variables-edgar-log-file-data-sets.pdf

SEC EDGAR Log File Data Sets:
https://www.sec.gov/data-research/sec-markets-data/edgar-log-file-data-sets

SEC EDGAR data access and post-acceptance corrections:
https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

SEC corrective disclosure guidance:
https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/correct-or-delete-filing

Federal Register public-inspection rules:
https://www.govinfo.gov/content/pkg/CFR-2025-title1-vol1/pdf/CFR-2025-title1-vol1.pdf


## 24. Patent examination capacity as an information-quality state

A new cross-domain connection is worth preserving under Q196/Q211 rather than expanding the top-level inventory.

USPTO provides a historical Office Action Research Dataset covering examiner actions mailed in 2008–mid-2017 and states that newer APIs expose office-action rejection/citation data from October 2017 onward. This creates a potentially useful two-architecture source route, but the transition interval and exact field semantics must be audited before any historical panel is assumed.

Academic evidence indicates that examiner busyness affects patent quality and can predict subsequent stock returns. This does not authorize a project signal; it motivates a structural mechanism: **the same patent-information event may carry different informational quality depending on the institutional processing environment under which it was examined**.

Potential pre-outcome state variables:
- examiner workload percentile using only information observable by the action boundary;
- art-unit workload;
- examiner experience / historical decision dispersion;
- rejection-type composition in the current office action;
- lag from application/publication to office action, only where both dates are admissible at the public boundary.

Hard PIT requirement:
- no future applications may contribute to workload;
- no later grant/citation/litigation outcome may define the state;
- public application availability and office-action publication timing must be reconstructed separately;
- any 2008–mid-2017 / post-Oct-2017 source bridge must prove completeness or retain the transition gap as missing;
- examiner identity and assignment must be frozen from the contemporaneously public record.

Cheap falsifiers:
- collapse after controlling for Q196 citation provenance;
- collapse to patent count/publication timing;
- workload state cannot be reproduced without future applications;
- source-architecture transition creates an unresolvable gap;
- examiner assignment is not stable enough for deterministic historical reconstruction.

Decision: retain as a nested research mechanism, not a new candidate. It is interesting because it shifts the information object from the firm's technological disclosure to the **institutional reliability/processing state behind that disclosure**.

Sources:
https://www.uspto.gov/ip-policy/economic-research/research-datasets/office-action-research-dataset-patents
https://www.uspto.gov/ip-policy/economic-research/research-datasets/historical-patent-data-files
https://www.sciencedirect.com/science/article/pii/S0304405X21004785


## 25. Regulatory stress-test certification — nested mechanism only

Current Federal Reserve stress-test documentation exposes a particularly clean external-certification clock: the Board publicly releases bank-level supervisory stress-test results at a specified timestamp, and covered institutions have defined subsequent disclosure windows. The 2026 results page also provides bank-level results and historical 2013–2026 datasets. This is a more standardized external-information process than issuer self-reporting.

The economic mechanism is potentially distinct from generic disclosure sentiment: an external supervisor evaluates capital resilience under a fixed scenario and publishes a certification-like state that can influence regulatory capital constraints. Historical Federal Reserve work finds that larger stress-test capital buffers reduce bank lending, with downstream effects on firms' credit access, investment and employment.

Potential state, discovery-only:
- supervisory stress-loss / capital depletion relative to pre-event capital;
- change in stress capital buffer requirement;
- bank-specific external-certification state;
- pre-event bank capital cushion × supervisory stress sensitivity.

Hard PIT conditions:
- use only the exact Board publication boundary;
- pre-event balance-sheet/capital values only;
- no later bank disclosures to reconstruct the original state;
- preserve scenario-version lineage and historical methodology changes;
- distinguish supervisory result publication from the later bank disclosure;
- do not infer an "unexpected" surprise without an independently frozen pre-event expectation dataset.

Overlap controls:
- merge with Q214 if it becomes only a risk-state transformation;
- merge with Q222/Q220 if only a generic external-vs-internal representation gap remains;
- reject if the result is driven solely by known bank size/capital ratios without incremental stress-test structure.

Decision: keep as a nested regulatory-certification hypothesis. Do not add a top-level candidate until a source/PIT census demonstrates a genuinely distinct observable and sufficient historical coverage.

Sources:
https://www.federalreserve.gov/supervisionreg/dfa-stress-tests-2026.htm
https://www.federalreserve.gov/newsevents/pressreleases/bcreg20260624a.htm
https://www.federalreserve.gov/econres/feds/the-effects-of-bank-capital-buffers-on-bank-lending-and-firm-activity.htm
https://www.federalreserve.gov/publications/dodd-frank-act-stress-test-publications.htm


## 26. New Q228 — regulatory scrutiny is an information channel, not merely a delay

A deeper SEC source review identifies a genuinely different object from simple disclosure complexity or generic release latency. The SEC states that it selectively reviews filings, concentrates on disclosures that may conflict with rules/accounting standards or appear materially deficient in explanation or clarity, and can conduct multiple rounds of comments and filer responses. Public correspondence has been available in EDGAR since 2005; current SEC guidance states that correspondence is released at least 20 business days after effectiveness or completion of the relevant review.

This creates a potentially useful information state:
issuer disclosure -> regulator scrutiny -> issuer response/amendment -> review closure.

The latent review process is not public at inception, so the first admissible public signal is the release of the SEC correspondence. This is a two-clock problem analogous to Q227 but with a different economic object: Q227 observes costly information acquisition by an outside requester; Q228 observes regulatory scrutiny of the issuer's own disclosure.

Why Q228 is potentially distinct:
- Q217 measures processing/friction properties of the filing itself;
- Q218 measures content allocation across mandatory and voluntary channels;
- Q195 measures inspection/enforcement escalation;
- Q204 measures timing between public information stages;
- Q228 measures the regulator's interrogation of the disclosure and the issuer's subsequent response process.

The 2017 literature finds that SEC comment letters concern accounting, financial reporting and disclosure issues and studies their resolution/informational consequences. This is mechanism motivation only.

First feasibility gate:
1. historical EDGAR correspondence population census from 2005 onward;
2. deterministic reviewed-filing/review-cycle linkage;
3. provenance separation of SEC-originated UPLOAD letters and filer CORRESP responses;
4. public-observation clock reconstruction;
5. amendment/review-closure lineage;
6. deterministic topic taxonomy;
7. independent PIT reproduction.

Cheap merge/kill conditions are explicitly Q217/Q218/Q195/Q204. If comment intensity becomes only a proxy for filing complexity, or if the only persistent object is publication delay, Q228 should be merged or killed rather than tuned.

Sources:
https://www.sec.gov/answers/commentletters.htm
https://www.sec.gov/search-filings/edgar-search-assistance/how-search-edgar-correspondence
https://www.sec.gov/about/divisions-offices/division-corporation-finance/filing-review-process-corp-fin
https://www.sciencedirect.com/science/article/pii/S0278425417300650
https://onlinelibrary.wiley.com/doi/10.1111/1911-3846.12297

## 27. Q228 versus Q227 — common clock discipline, different information economics

The project now has two complementary regulatory-observation channels:

- Q227: outside party incurs acquisition cost to request information from the regulator; public signal arrives only when the request becomes observable.
- Q228: regulator scrutinizes issuer disclosure; public signal arrives only when the correspondence becomes observable.

Both require a latent-process clock distinct from the public-observation clock. Their source schemas, contamination risks and economic mechanisms are sufficiently different to preserve them separately.

The broader reusable control is a typed event lineage:
latent_process -> first_public_observation -> response/confirmation -> closure/amendment.

This lineage is a governance primitive, not a candidate family and must not itself be performance-ranked.


## 28. Q229 — regulator-disclosed complaint → management-response state

A deep source scan identifies a potentially useful public information channel that differs from filing text, investor demand and regulatory review: **complaints submitted by consumers and the firm's subsequent response process**.

The CFPB Consumer Complaint Database is freely downloadable and exposes complaint submission date, company, product/issue and company-response attributes. The CFPB states that complaints sent to companies for response are generally published after the company responds or after 15 days, whichever comes first, and that the database updates generally daily. The CFPB also warns that the database is not a statistical sample of consumer experience and that raw company-level counts must be interpreted relative to firm size/market share. citeturn496534search0turn496534search8

This suggests a two-clock mechanism analogous to Q227 but economically different:
- latent clock: complaint submission/receipt;
- public clock: first public database observation;
- response clock: company response and disposition.

The candidate should therefore avoid treating complaint count as the signal. More interesting predeclared states are topic/severity composition, response timeliness, disposition, unresolved status at publication, and **complaint–response divergence**.

Recent 2026 research is unusually close to the proposed object. Cai et al. report that consumer complaints reveal latent firm problems associated with lower future stock returns and weaker operating performance, with product-quality, false-advertising and transaction-trap topics more informative than logistics complaints. A separate 2023 study finds that regulator-disclosed consumer complaints induce peer-bank learning in local mortgage markets. These are mechanism motivation, not project evidence. citeturn452164search3turn452164search5

A major control is publication selection: only complaints eligible for company response enter the public database, and publication occurs after a response or 15 days. The public dataset therefore does not measure latent complaint incidence without selection. That selection must be frozen rather than statistically “corrected” using outcomes.

Useful cross-domain replication routes exist. The FCC Consumer Complaints Data starts on October 31, 2014 and is public-domain; the FCC states that it does not verify the facts alleged. FINRA's Rule 4530 system also records quarterly customer-complaint statistics by problem and product. citeturn452164search9turn452164search13

Decision: **Q229 remains P1 source-feasibility exploratory**. It should move toward the active frontier only after the public-observation clock, historical taxonomy, company/issuer mapping and publication-selection controls are mechanically reproducible.

## 29. Q230 — cross-capital-structure bond-implied equity information state

A second strong result comes from current cross-asset research. A September 2026 paper by Auh and Kim reports that corporate-bond signals predict next-month equity returns for the same issuers after stock controls and attributes the mechanism to segmentation between bond and equity markets. A related 2026 paper reports bond-to-equity spillovers across capital-structure factors. citeturn511378search0turn511378search7

The important project distinction is that Q230 is **not ordinary bond momentum**. The proposed object is the information-processing gap between two specialized investor clienteles:
bond market state -> equity repricing.

The free-data feasibility route is materially better than the enhanced TRACE route might initially suggest. FINRA states that public Trade Activity contains up to ten years of end-of-day data, while enhanced historical transaction data with otherwise non-disseminated fields require a paid agreement. FINRA's public API documentation exposes a corporate/agency security master and daily-list routes as well as market-close/end-of-day files. citeturn403955search0turn403955search1turn403955search18

This gives a strict first implementation:
- use only free public end-of-day TRACE information;
- no paid historical data;
- construct a deterministic bond-security -> issuer mapping;
- aggregate across eligible bonds under a fixed predeclared rule;
- separate rate-market and broad credit effects from issuer-specific bond information;
- require bond information to precede the equity decision boundary;
- preserve bond lifecycle, cancellation/reversal and maturity changes.

The major unknown is therefore **not the economic mechanism but the free historical implementation contract**: whether the public EOD route supplies enough stable issuer-linked observations to construct an immutable long panel without licensed data.

Decision: **Q230 remains P1 source-feasibility exploratory**, with a potentially high priority if the free TRACE source census passes.

## 30. New architecture lesson from current trading-agent systems

The current open-source trading-agent landscape reinforces a useful division of labor rather than suggesting new alpha by itself.

TradingAgents v0.6.0 now emphasizes parallel analysts, persisted run reports, per-model-tier providers, point-in-time backtesting and settlement of completed decisions while analysis continues. FinRobot uses a lead orchestrator, specialized research/modeling/synthesis agents, explicit bull/bear/judge debate, and deterministic financial computation separated from LLM narration. FinAgent combines multimodal market intelligence, chart-based reflection, investor-flow inputs and diversified memory retrieval. FinMem emphasizes layered memory and explicit temporal handling of financial information. citeturn476947search2turn476947search5turn476947search0turn911978academia56

The project-level inference is narrower and more important:
1. agent parallelism should maximize **independent source discovery and verification**;
2. memory should persist evidence, provenance and failed hypotheses, not just model prose;
3. deterministic computation should own all scientific state transitions;
4. LLM agents should propose, challenge and synthesize but never grant scientific authority;
5. post-decision outcome settlement is useful for agent learning, but must remain outside the frozen historical prefix used to generate the original decision.

No observed open-source agent result is treated as project performance evidence.

## 31. Cross-domain source scan — important negative and nested findings

Several additional public data systems are rich enough to matter, but do not currently justify new top-level candidates:

**EPA ECHO.** EPA provides downloadable compliance/enforcement datasets, including inspection dates/findings, violations, enforcement actions and penalties; formal enforcement histories extend back to cases concluded after September 30, 2000. However, ECHO is refreshed from underlying source databases on a weekly schedule and some displayed compliance statuses are allegations rather than final adjudications. This makes ECHO promising for a nested Q195/Q225 regulatory-state research track but not yet for a clean new candidate. citeturn850783search0turn850783search1turn850783search6

**FCC ULS.** FCC's Universal Licensing System provides public application/license data and daily/weekly transaction files, while spectrum licensing and leasing can encode economically meaningful capacity changes. Historical public datasets exist, but the open-data catalog page for the main ULS dataset itself has not been updated since 2017, so current historical-prefix/revision semantics are not yet strong enough for top-level candidate admission. citeturn324017search0turn324017search1turn324017search13

**USPTO maintenance fees.** USPTO confirms that utility and reissue utility patents require maintenance fees at fixed 3.0–3.5, 7.0–7.5 and 11.0–11.5 year windows, and that payment histories and expiration notices are publicly available. This could encode an economically interesting **option-exercise / abandonment state** distinct from patent publication or citations. However, current public storefront access and historical bulk reproducibility need a dedicated source census before it is promoted beyond a nested Q196/Q211 mechanism. citeturn645904search1turn645904search6

These paths should be explored only when their source/PIT contract provides enough incremental information to justify the compute.


## 32. 2026-10-05/06 external re-check — current primary-source confirmations

This re-check was performed against current public sources after the prior synthesis. It changes no candidate authorization and no scientific evidence boundary.

### Q219 — filing-change × options-response mechanism receives direct 2026 support

The Journal of Financial and Quantitative Analysis reports in 2026 that larger textual changes in 10-Ks are associated with larger post-release increases in option volatility smirks, consistent with options traders reacting to negative information in changed text. The return predictability of textual changes is stronger when the option-smirk response is larger, and the documented reaction is concentrated after release. This materially strengthens the economic plausibility of Q219 while simultaneously raising the importance of its exact post-filing clock and same-session exclusion. It does not authorize performance testing.

Source: https://jfqa.org/2026/03/19/attentive-options-traders-textual-changes-to-10-ks-and-option-volatility-smirk/

### Q220 — the representation layer is economically meaningful, not merely technical

The SEC's Inline XBRL design intentionally combines human-readable and machine-readable information in a single document. The SEC states that its EDGAR APIs expose submission and XBRL data in real time, with typical processing delays below one second for submissions and below one minute for XBRL, although peak filing periods can be slower. Existing empirical work finds iXBRL adoption lowers stock-return drift and facilitates information being impounded after annual-report filings. Therefore Q220 should preserve a strict distinction between (a) economic information content, (b) machine-readable representation/tagging, and (c) user accessibility. A deterministic filing-local four-state representation — narrative-only change / structured-only change / both / neither — is a useful design decomposition, provided mapping is frozen and no later taxonomy correction is allowed to rewrite the historical state.

Sources: https://www.sec.gov/data-research/structured-data/inline-xbrl ; https://www.sec.gov/search-filings/edgar-application-programming-interfaces ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3600458

### Q221 — sequence structure should be central, not award size

A current NBER 2026 conference abstract using federal R&D contracts from 1984–2024 reports that R&D awards embed an implicit guarantee of future noncompetitive procurement and that private value is strongly linked to later production contracts from the same R&D-awarding agency, especially for noncompetitive awards and vertically integrated firms. This supports Q221's sequence-state framing: R&D award -> modifications -> same-agency production/procurement realization. The public-clock problem remains independent. SAM.gov now contains former FPDS contract-award data, but current public access explicitly excludes DoD awards unrevealed within 90 days of signing. Consequently Date Signed cannot by itself be treated as the tradable event clock for the full public universe; Q221 must reconstruct first public observability and retain unrevealed intervals as unavailable rather than backdating them.

Sources: https://www.nber.org/conferences/rate-return-research-and-development-investments-fall-2026 ; https://sam.gov/fpds ; https://alpha.sam.gov/contract-data

### Q230 — cross-capital-structure information channel is strongly corroborated

A September 2026 SSRN paper finds issuer-level corporate-bond signals predict next-month equity returns after stock characteristics and interprets the result as gradual information incorporation across segmented bond/equity markets. A second 2026 study reports cross-market effects concentrated in illiquid and hard-to-arbitrage segments. This makes Q230 one of the stronger orthogonal candidates economically, but the project bottleneck remains free historical TRACE implementation, issuer/security mapping and lifecycle/reversal handling. The correct priority is therefore source-panel feasibility, not parameter search.

Sources: https://papers.ssrn.com/sol3/Delivery.cfm/7527218.pdf?abstractid=7527218&mirid=1 ; https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6588823

### Cross-candidate public-clock principle

The latest source review suggests a reusable governance primitive: separate economic_event_time, first_public_observation_time, subsequent_confirmation_time, and correction_or_reversal_time. This is especially important where publication is staged or selectively delayed. SEC EDGAR provides unusually granular public timing for accepted filings; SAM.gov explicitly documents a current DoD unrevealed window; regulatory requests/correspondence and other staged channels can have a similar latent-process/public-observation split. This is a control-plane concept, not a candidate family and must not be performance-ranked.

### Trading-agent architecture re-check

The current TradingAgents repository reached v0.6.0 on 2026-10-03. Its current public documentation emphasizes persisted reports, checkpoint/recovery, time-scoped backtesting, parallel analyst execution and settlement of historical decisions. FinRobot's current repository explicitly separates model reasoning, deterministic software computation, agent orchestration and system verification. FinMem continues to emphasize layered memory and temporal handling of financial information. The useful project inference is narrow: preserve append-only evidence/outcome memory, typed temporal state, parallel independent analysts and deterministic verification; do not infer alpha from the architecture itself.

Sources: https://github.com/TauricResearch/TradingAgents ; https://github.com/AI4Finance-Foundation/FinRobot ; https://mlanthology.org/iclrw/2024/li2024iclrw-finmem/

### Resulting priority

Keep the active top-candidate wave unchanged: Q218 / Q219 / Q220 / Q221. Raise confidence in Q219, Q220 and Q221's mechanism plausibility, while keeping the scientific bottleneck exactly where it belongs: source completeness, public-clock reconstruction, PIT integrity, deterministic compilation, mutation tests and independent reproduction. Q230 remains a high-value exploratory side track until the free historical TRACE contract is proven. No performance, holdout selection, ranking, tuning, promotion or live execution is authorized by this scan.
