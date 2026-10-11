# Project-wide research synthesis: information mechanisms, PIT integrity, and research efficiency

**Date:** 2026-10-11 UTC  
**Classification:** literature synthesis / design-only / no candidate authorization  
**Repository basis:** `99ece057f143582710b8ecce1dd050a5f6b74185`  
**Purpose:** synthesize existing candidate families and relevant research, identify distinct economic observables, and reduce duplicate research and look-ahead risk before spending more compute.

## Executive conclusions

1. **The scarce resource is not another signal idea; it is a defensible information boundary.** Many public datasets contain useful economic events, but the date on an event, the date an agency records it, the date a source API first exposes it, and the date a researcher downloads it are different clocks. Every candidate needs a source-specific first-public-observation contract and immutable revision lineage.
2. **The project's most reusable intellectual asset should be a typed public-information state machine.** The common unit is `(event identity, source version, first admissible public boundary, state transition, frozen entity exposure, correction lineage)`. Reuse parsers and provenance infrastructure, not economic hypotheses.
3. **The current overlap audit is incomplete.** `automation/evidence_graph_stage4_stage5.py` currently derives pairwise novelty only from `orthogonal_candidate_specs_2026-10-05.json`. It indexes other documents but does not add legacy candidate inventories and discovery seeds to the pairwise signature universe. Q157 (legacy wave) therefore is not compared with Q227/Q231 (current manifest) by the novelty engine. This PR adds deterministic cross-wave inventory loading and regression tests. It does not auto-merge candidates or alter execution eligibility.
4. **Novelty must be judged by the economic object and decisive falsifier, not by source name or candidate ID.** Shared data sources often justify shared compilers; different candidate labels do not establish independence. A candidate must identify what it measures that an adjacent candidate does not.
5. **The literature supports disciplined temporal construction and multiplicity controls, not automatic alpha claims.** Data-vintage research shows that first releases and later revisions can carry different information; high-throughput asset-pricing research warns against selecting winners from large hypothesis spaces; temporal-LLM research highlights model-training leakage beyond ordinary data joins.
6. The active execution focus remains **Q104:I19, Q220 and Q221**. **Q218 remains excluded** from active execution, candidate dispatch, and successor selection. The bounded Q221 archive inventory ran on 2026-10-11 (`38161449892`): archive metadata parsed, but no dated multi-version series was found; the fail-closed receipt does not establish an event-level first-public boundary or a frozen recipient-to-issuer mapping.

## 1. Cross-project mechanism map

| Mechanism family | Existing related candidates | Distinguishing observable | Shared infrastructure; do not conflate |
|---|---|---|---|
| Regulatory information acquisition | Q157 / Q227 / Q231; adjacent Q224 / Q226 | Publicly logged acquisition/request state, requester/topic mix, or age composition of requested filings | FOIA request IDs, issuer mapping, public-log vintages, EDGAR request parser, traffic-quality controls |
| Cross-channel chronology | Q204 / Q215 / Q223; adjacent Q228 | Release-stage latency vs an external state preceding issuer disclosure vs independently corroborating/contradicting content | Event identity, source clocks, correction history, frozen issuer exposure |
| Filing representation and processing | Q217 / Q220 / Q222 | Complexity/friction vs narrative/structured XBRL mismatch vs claims contradicted by external implementation evidence | Filing acceptance, XBRL contexts, text blocks, taxonomy/presentation maps, source provenance |
| Federal R&D and demand | Q197 / Q203 / Q221; bridge to Q191/Q199 | Network demand propagation vs award conditional on financing constraints vs award option/capability state | Award and transaction IDs, amendments, recipient identity, public release boundary, patent/science identity links |
| Science and technology chronology | Q176 / Q191 / Q196 / Q199 | Publication burst vs science-to-patent stage order vs citation provenance vs patent first-publication shock | DOI, patent family/assignee, publication vintages, citation source and correction lineage |
| Product/regulatory state transitions | Q154/Q155 and seeds Q233/Q235, plus related regulatory tracks | Shortage/substitution vs recall-severity confirmation vs import restriction; the state transition must be explicit | FDA product/manufacturer IDs, enforcement/recall histories, source vintages and issuer exposure |
| Physical vs digital operational state | Port satellite/AIS divergence; facility-light anomalies; cyber exploitation × exact product version | Physical activity not reflected in broadcast data; facility activity shock; confirmed exploited vulnerability in a demonstrably affected product | Geospatial/versioned entity mapping, sensor-quality controls, official release timestamps, immutable exposure edges |

This table is a *relationship map*, not a ranking of expected returns. The project should prefer a shared, validated data layer and distinct predeclared observables over many nearly identical candidate IDs.

## 2. Literature and methodological implications

### 2.1 Data revisions are economically meaningful

Borup and Schütte, **“Asset pricing with data revisions”** (*Journal of Financial Markets*, 2019), examine real-time vintages of consumption data. Their reported results distinguish initial releases from later revisions and treat the revision process as information rather than as a clerical nuisance. This directly supports the project's rule that current revised values cannot silently replace historical as-known values.

- Paper record: https://consensus.app/papers/details/c06096cf36685742b18746771a23fc97/
- Practical consequence: preserve each source vintage, first-public boundary, later correction, and the exact version used by each historical decision.
- Limitation: a macro-data result does not establish an edge for SEC/XBRL or procurement candidates; it establishes why vintage handling is necessary.

### 2.2 Temporal leakage can occur inside models, not just in joins

He, Lv, Manela and Wu, **“Chronologically Consistent Large Language Models”** (2025), study language models constructed from chronologically restricted data and report a financial-news application. This highlights a project-wide distinction: a correct point-in-time dataset does not guarantee a point-in-time text representation if the model or embedding has been trained on future documents.

- Paper record: https://consensus.app/papers/details/518c675d55ae5797882706fafb9c52d3/
- Practical consequence: every future text/LLM candidate needs model/version provenance, training-corpus cutoff or a defensible leakage analysis, prompt/version fingerprints, and an independent temporal non-interference test. “The filing timestamp is correct” is insufficient when the representation model may know later events.
- Limitation: the paper's findings are not proof that any current project model leaks or that a PIT model will be profitable.

### 2.3 Large hypothesis spaces require explicit multiplicity control

Chen and Dim, **“High-Throughput Asset Pricing”** (2023), describe empirical-Bayes methods for large collections of trading strategies and discuss the weakness of naive selection on maximum Sharpe ratios. Harvey, Liu and Zhu's factor-zoo work similarly emphasizes the multiple-testing burden in empirical asset pricing. McLean and Pontiff's replication research is a further reminder that published predictability may attenuate after discovery.

- Chen & Dim, **“High-Throughput Asset Pricing”** (2023) was returned by the literature search, but a publisher/author canonical record was not independently resolved in this pass; treat it as a search lead, not a formally verified citation.
- Harvey, Liu & Zhu, **“…and the Cross-Section of Expected Returns”**: https://doi.org/10.1093/rfs/hhv059
- McLean & Pontiff, **“Does Academic Research Destroy Stock Return Predictability?”**: https://doi.org/10.1111/jofi.12365
- Practical consequence: discovery metadata must be separated from outcome tests; keep an immutable ledger of all candidate concepts, source tests, failed hypotheses and decision rules. Do not select the best-looking candidate or horizon from the same data used to invent it.
- Limitation: literature replication results do not determine the proper numerical threshold for this project. That threshold must be predeclared by the project's own governance and sample-size design.

### 2.4 Government procurement and innovation are multi-stage processes

The project's Q221/Q191/Q197 neighborhood naturally suggests an ordered bridge: public R&D award → first public technical output → independently linked follow-on deployment/procurement. The sequence is only a distinct hypothesis if the third stage is demonstrably tied to the same technical effort. A later award to the same vendor is not enough. Studies and datasets linking federal awards, patents and scientific publications can help define joins, but patent-producing samples must not define the denominator because they condition on successful technical output.

- Public linkage scaffold: https://zenodo.org/record/3369582
- Related study: https://doi.org/10.1371/journal.pone.0218927
- Practical consequence: sample the full award universe first, freeze a deterministic sample, then measure whether output and deployment stages can be linked without hindsight. Keep the bridge nested under existing research until it demonstrates a decisive observable not already contained in Q221/Q191/Q197.
- Limitation: an observed stage transition does not by itself establish an investable return effect.

### 2.5 SEC/XBRL representation gaps need taxonomy and timing discipline

Q220's proposed mechanism is not merely “text differs from numbers.” It is a filing-level mismatch between narrative representation and structured reporting, conditioned on exact taxonomy, presentation, context and acceptance-time information. A generic text embedding or a current taxonomy lookup cannot substitute for the as-filed taxonomy and presentation state. The same concern applies to disclosure complexity and external-verification candidates: filing size, boilerplate, and later issuer identity mappings can produce spurious apparent effects.

- SEC developer documentation and filing data: https://www.sec.gov/edgar/sec-api-documentation
- XBRL specification hub: https://www.xbrl.org/standards/
- Practical consequence: preserve original filing bytes, accession/acceptance clock, taxonomy and context versions, the resolver hash, and a mapping receipt for each issuer/document. The population receipt must match the current gate-code and frozen-contract hashes before any historical prefix/PIT compiler can open.
- Limitation: taxonomy correctness is a prerequisite for measuring the construct, not evidence of predictive value.

## 3. Comparable agent architectures: what to borrow and what not to infer

The closest public reference systems are useful primarily as architecture comparisons. Their reported trading/backtest results are not directly comparable to this repository unless data versions, point-in-time constraints, transaction costs, universes, risk limits, and evaluation periods are aligned.

| System | Published design emphasis | Potentially useful transfer | Important non-transfer |
|---|---|---|---|
| **TradingAgents** (Xiao et al., arXiv:2412.20138, 2024/2025) | Role-specialized fundamental, sentiment and technical analysts; bull/bear debate; risk-management roles; trader synthesis | Structured adversarial review, explicit dissent, risk-focused handoffs, role-specific evidence requests | Do not treat a multi-agent debate or paper-reported backtest improvement as source/PIT validation, independent reproduction, or permission to trade |
| **FinRobot** (Yang et al., arXiv:2405.14767, 2024) | Layered platform spanning financial agents, LLM algorithms, LLMOps/DataOps and foundation models | Keep model orchestration replaceable; make deterministic tools and data contracts first-class; record model/tool versions | An agent platform does not itself guarantee immutable historical data, first-public timestamps, or statistically valid candidate selection |
| **FinMem** (Yu et al., arXiv:2311.13743, 2023) | Profiling, layered memory and decision modules | Persistent research memory, compact handoff state, provenance-linked retrieval, explicit separation of old observations from new evidence | Claims about improved simulated returns do not validate the current project’s data clocks or generalize across universes |

Primary references:
- TradingAgents paper: https://arxiv.org/abs/2412.20138 ; project page: https://TradingAgents-AI.github.io
- FinRobot paper: https://arxiv.org/abs/2405.14767 ; official repository: https://github.com/AI4Finance-Foundation/FinRobot
- FinMem paper: https://arxiv.org/abs/2311.13743

**Project-level synthesis:** the best differentiator is not adding more agent personas. It is combining (a) a deterministic, versioned evidence plane, (b) bounded specialist workers, (c) an adversarial reviewer whose findings must cite immutable artifacts, and (d) a fail-closed authority layer that cannot be overridden by model consensus. The existing two-lane Formal Readiness / Frontier Discovery structure is directionally consistent with this separation. The highest-value incremental test is to verify that every agent-generated claim is typed as *literature lead*, *source-feasibility result*, *PIT evidence*, *performance evidence*, or *authorization* and cannot silently cross those boundaries.

## 4. Orthogonal ideas worth cheap falsification — design only

These are research directions, not new active candidates or authorization.

### A. Physical-vs-broadcast discrepancy at ports

**Falsifiable hypothesis:** for a small frozen set of ports with independently documented disruptions, a predeclared discrepancy between satellite-measured physical activity and AIS-broadcast activity identifies a measurement state not captured by AIS alone.

**First cheap tests:** source coverage and quality; first-public release clock for each satellite product; stable port boundaries; validation against known disruptions; frozen port/commodity-to-issuer exposure with direct evidence. Stop if the public release time cannot be reconstructed, if the signal disappears under weather/seasonality/quality controls, or if issuer exposure requires narrative guesswork.

NASA Black Marble source: https://www.earthdata.nasa.gov/data/projects/black-marble  
Related research seed (arXiv): https://arxiv.org/abs/2604.15444

### B. Confirmed cyber exploitation × exact affected version × issuer exposure

**Falsifiable hypothesis:** a newly public confirmed-exploitation state is relevant to a listed issuer only when an exact affected software/product version is demonstrably present in that issuer's product or operational footprint.

**First cheap tests:** CISA KEV date-added and versioned source snapshot; exact CVE-to-CPE/version match; blinded product/vendor/issuer adjudication; independent advisory cross-check; keyword-only placebo. Stop if the link is based only on vendor name or fuzzy text, or if KEV date is not the first public boundary and cannot be reconstructed.

CISA KEV: https://www.cisa.gov/known-exploited-vulnerabilities-catalog  
NVD product/CPE APIs: https://nvd.nist.gov/developers/products

### C. Regulatory confirmation after an initial company-originated event

**Falsifiable hypothesis:** the *incremental official state transition* (confirmation, classification, recall class, or formal action) adds information beyond the initial company-originated event. Raw complaint/adverse-event counts are not treated as incidence or causation.

**First cheap tests:** freeze event identity and state machine; reconstruct both first-public clocks; map product to issuer before outcomes; include duplicate, withdrawn, reclassified and unresolved states; test whether official confirmation can be observed historically rather than only through the current dashboard. Stop if only current API snapshots are available or the second state merely repeats the first event.

FDA AEMS public dashboard and limitations: https://www.fda.gov/drugs/fda-adverse-event-monitoring-system-aems/fda-adverse-event-monitoring-system-aems-public-dashboard

### D. Innovation-to-deployment conversion bridge

Keep this as a sub-hypothesis under Q221/Q191/Q197 until the existing variables and decisive observable are audited. Sample from the full award universe, not a patents-only linked sample. Require direct award identity, technical-output publication boundary and independently linked follow-on realization. If the last join is “same vendor later won a contract,” reject it as insufficient.

## 5. Cheap falsifiers and project-wide controls

Before any expensive validation, each candidate should pass these controls:

1. **Source feasibility:** stable endpoint, bounded response size/time, deterministic pagination, reproducible schema and explicit failure counts.
2. **Temporal contract:** distinguish event date, filing/acceptance time, source publication time, first observed public time, download time and revision time. Missing public clocks remain unknown, never imputed.
3. **Entity contract:** freeze issuer/product/facility/recipient mapping before outcomes; record exact identifiers, match type, ambiguity and unmapped rows.
4. **Revision contract:** append-only source vintages, immutable snapshots and content hashes; future corrections cannot rewrite a historical prefix.
5. **Negative controls:** future-row mutation, shuffled entity map, unrelated-source placebo, duplicate/withdrawn events, and “same vendor later” placebo where relevant.
6. **Multiplicity:** retain every idea and negative result; prohibit selecting assets, horizons, thresholds or models based on the discovery sample.
7. **Independent reproduction:** use a separate implementation or independent parser for fixed controls before calling a source/PIT gate complete.
8. **Model provenance:** for text/LLM features, version the model and training-data cutoff; ordinary timestamp-safe joins do not prove model-level temporal non-interference.
9. **Resource discipline:** reuse validated compilers, block genuinely duplicate jobs, and never dispatch merely to occupy a runner.
10. **Authority boundary:** CI, source feasibility, literature, model reviews and compute capacity do not imply profitable performance or permission to trade.

## 6. Current execution implications

- **Q104:I19:** allow the existing historical 13F census to terminate. Reconcile all shard receipts, then recover only accession headers demonstrably missing from the frozen failure set. Do not restart the full census blindly.
- **Q220:** both source-gate jobs in run `38155914188` have completed successfully. The 55-record population receipt and eight-record route receipt were downloaded and their canonical fingerprints recomputed; both carry gate-code SHA-256 `2a455f02835b2d85308ac2c178777999fc059312218275a697204313de8cab0d` and frozen-contract SHA-256 `5014eb888a4e66502cb30c9ec5208caec1de65425dad3c1bd3feb8b17a29ac88`, matching current source bytes. Population fingerprint: `158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543`; route fingerprint: `78cd9beea6beed3aaeb7f8ba939673274754b452a046f7e78ab76eb0e9c27c6d`. Five original 10-K records have no observed TextBlock facts and are preserved as explicit missing states. The historical-prefix compiler had an obsolete fixed population pin (`0d2e179...`); a reviewable change updates it to the verified receipt so the existing compiler workflow can run. These are source/PIT-structure receipts only; the compiler's result and independent PIT reproduction remain separate gates.
- **Q221:** bounded archive inventory run `38161449892` parsed metadata for FY2019–FY2025 but failed closed with `ARCHIVE_LISTING_OK_NO_VERSION_SERIES_FOUND`: each fiscal year returned one full archive and the same single delta archive date, not a dated historical version series. Receipt flags `historical_first_public_observation_proven`, `event_level_public_boundary_proven`, and `recipient_to_issuer_mapping_frozen` are all false. No broad archive payloads were downloaded. Treat this as a source-feasibility negative—not scientific evidence or PIT proof. Do not rerun the same inventory or infer a PIT boundary; only investigate a source that independently establishes versioned public timestamps before revisiting this gate.
- **Q218:** excluded from active execution and successor selection. Historical artifacts remain preserved; no new Q218 job is authorized by this document.
- **No performance authorization:** this note creates no trial, result, ranking, tuning, holdout choice, promotion or live-execution permission.

## 7. Repository change included with this synthesis

The accompanying code change extends the Stage 4/5 overlap engine to form a deterministic candidate inventory from the current contract manifest, legacy candidate waves and discovery seed packs. The current manifest wins when an ID appears in multiple inventories. Two regression tests require Q157, Q227, Q231 and Q233 to appear in the comparison universe and verify deterministic review-only novelty output.

The change intentionally does **not**:
- merge or delete candidate IDs;
- change active execution priority or dispatch configuration;
- interpret overlap scores as scientific proof;
- modify frozen trials or source/PIT gates;
- enable live trading, orders or automatic promotion.

## References and verification note

Consensus search record for Borup & Schütte and He et al. was retrieved during this research turn. The citations above are literature leads; verify exact bibliographic metadata from publisher/author primary pages before using them in a formal manuscript. The Chen & Dim link above is explicitly flagged as unverified and must not be cited as a canonical reference until resolved. No literature result in this document is treated as project evidence or a performance claim.

**Safety:** `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False`, `AUTOMATIC_PROMOTION=False`.
