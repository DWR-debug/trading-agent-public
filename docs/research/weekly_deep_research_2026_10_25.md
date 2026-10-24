# Weekly Deep Research — 2026-10-25

**Repository HEAD checked:** 5f690f2fa1f402a224c15285973baab78a814449 (2026-10-24 22:15:01 UTC; paper-forward MTM state update).  
**Canonical operational snapshot:** f32234cd64cbe87c3205a5fd89fce223f7960228, generated 2026-10-24 21:56:46 UTC. The later HEAD commit changes paper-forward state, not candidate registry or research gates.  
**Canonical files:** docs/CURRENT_STATUS.md; research/evidence/current_operational_state.json; docs/TRADING_AGENT_PROJECT_STATUTES.md.

## 1. Governance and live repository state

The active execution focus remains exactly Q104:I19 | Q220 | Q221. Q237 (trademark/product-intangible state) and Q238 (inventor mobility/tacit-knowledge transfer) remain open reserve issues #1155/#1156, not active Top-3 candidates. No candidate, workflow, trial, gate or authorization was changed in this round.

Current blockers:
- Q104:I19: 53 unresolved accession keys. Thirty-six verified filing-date discrepancies are admissible only in a non-destructive sidecar; seven identity-conflict rows and ten complete-submission HTTP 404 rows remain unresolved. Acceptance time is not first-public-observation time.
- Q220: 55 primary-document hash mismatches; historical prefix/PIT compiler remains blocked. Do not redownload multi-GB SEC Feeds or change frozen hashes/population.
- Q221: first-public-observation time remains unproven for 348/348 rows; 247 recipient-to-issuer mappings remain unfrozen. The tested FPDS Atom route returned four HTTP 302 responses and no matches; do not repeat or follow redirects.

Safety remains PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, ORDERS_ENABLED=False, AUTOMATIC_PROMOTION=False.

## 2. Evidence-graph limitation

Issue #1512 reports 122 candidates, 16,427 nodes, 23,226 edges and ten review-required bridge proposals, but 0/121 candidate comparisons are complete because reusable-component and source-domain metadata are missing. Novelty and convergence scores are therefore null. This is a metadata-coverage failure, not evidence of orthogonality or convergence. No automatic candidate ranking is valid until metadata coverage is repaired from existing source-grounded contracts.

Issue #1514 already quarantines the global physical-economy graph (PortWatch/AIS, asset ownership, Comtrade and satellite products) as HISTORICAL_PIT_BLOCKED_PENDING_DIRECT_RECHECK. Do not reopen it under another name.

## 3. Cross-domain research findings

### A. Finance/economics/market microstructure: AI compute commitments × local grid constraints

The Dallas Fed working paper by Kay, Reaser and Taylor, “Processing Power: The Effect of Data Centers on Wholesale Electricity Markets” (Working Paper 2606, revised October 2026), models a material wholesale-price impact from data-center loads and transmission constraints, including spillovers to regions without many data centers. These are model estimates, not Trading-Agent evidence.  
Publisher: https://www.dallasfed.org/research/papers/2026/wp2606

FERC’s large-load interconnection docket documents the public regulatory process around large electricity loads and warns that speculative or duplicated queue requests can distort load forecasts and market signals.  
Official docket: https://ferc.gov/rm26-4  
FERC background: https://www.ferc.gov/news-events/news/ferc-act-large-load-interconnection-docket-june-2026

EIA-930 supplies hourly demand, generation and interchange data for US balancing authorities from 2019. EIA explicitly states that submissions can be repeated and historical values corrected, so today’s series does not prove the exact value public at a past decision time.  
Official data contract: https://www.eia.gov/electricity/930-content/about.html

PJM publishes queue cycles/status and Data Miner feeds, but release notes document reloads, field changes and corrections. A current queue table is not a versioned historical status record.  
Sources: https://insidelines.pjm.com/over-600-projects-enter-phase-1-of-pjms-new-interconnection-process/ ; https://www.pjm.com/markets-and-operations/etools/data-miner-2/data-miner-2-release-notes

**Parked design idea, no candidate ID:** Compute-Commitment-to-Delivery Gap × Local Grid Constraint. The state would be the gap between a documented facility capacity commitment/milestone sequence and an independently dated interconnection/energization status, conditional on local grid constraints—not announcement size alone. The first stage would freeze document-to-facility/parent mapping and distinguish announced, queued, approved, under construction, energized and withdrawn states. Queue status, announced MW and actual load must never be treated as interchangeable.

**Gate assessment:** orthogonality 4/5; falsifiability 4/5; data feasibility 2/5; expected information gain 3/5. PIT/history risk is high: current pages and trackers do not establish the historical version or first-public clock, and EIA history can be revised. Aggregated balancing-authority load cannot identify an individual issuer by itself. Keep parked until a public, row-level, versioned historical status path is proven. No dispatch or new ID.

### B. Earth observation × accounting/disclosure: thermal infrared activity

Xue, Zhang and Zhao, “Nowcasting Firms’ Operating Activities from Satellite Data on Thermal Infrared Radiation,” appeared online at Cambridge University Press on 2025-09-08 and in JFQA 61(3), May 2026. It reports associations between thermal infrared radiation and factory operating activity for 28,236 factories of Chinese listed firms. The publisher page acknowledges data support from Alt Data Tech; it does not establish a free, reusable historical source archive with a reproducible first-public clock.  
Publisher: https://www.cambridge.org/core/journals/journal-of-financial-and-quantitative-analysis/article/abs/nowcasting-firms-operating-activities-from-satellite-data-on-thermal-infrared-radiation/9298EBE11C14AAF091E261E286536DD1

USGS publishes Landsat surface-temperature products, but acquisition time is not the first-public time of a particular processed product version; cloud cover, revisit intervals, product changes and facility mapping also matter.  
Official source: https://www.usgs.gov/centers/eros/science/usgs-eros-archive-landsat-archives-landsat-level-2-provisional-surface

This could theoretically compare independent physical activity with company operating disclosures, but it overlaps facility-nightlight anomalies in PR #1257 and the physical-activity/ownership frontier in issue #1514. TIR is a different measurement modality, not yet a separate candidate family.

**Decision:** do not add a candidate. Retain only as a source note for the existing physical-data frontier; do not import the paper’s return results.

### C. Accounting standards × internal information acquisition

Christensen, Mittendorf and Partridge examine how a mandated information-quality standard can improve information acquisition for targeted and related untargeted activities, using ASC 606 as the archival setting. The publisher page lists the journal issue as November 2026, after this round’s cutoff; an SSRN version has existed since January 2024, so this is not a newly published October discovery.  
Publisher: https://doi.org/10.1016/j.jacceco.2026.101900  
Earlier version: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4697367

The study motivates an internal-information mechanism but does not establish a new publicly observable project event. Its likely observable outputs overlap Q218/Q220 disclosure structure and operational consequences. Internal information quality itself is not directly public.

**Decision:** literature anchor only; no new candidate.

### D. Market microstructure × dealer networks

Huber, Watts and Zhu, “Information Flows in Trading Networks,” Journal of Accounting and Economics 82(1), 2026, use detailed OTC corporate-bond transaction data and report that investors with larger dealer networks make better trading decisions before credit-fundamental changes. The key identification object is the transaction-level investor/dealer network; no free, historically complete public substitute with the same identities was established.  
Bibliographic/publisher record: https://doi.org/10.1016/j.jacceco.2026.101876

This overlaps Q230 and existing network/information-diffusion families. Public aggregate prices or bond issuance records would not reproduce the study’s identification.

**Decision:** reject as a public-data Discovery candidate.

### E. Data revisions and source history

Macro-vintage revision × issuer exposure remains Q216. EIA-930’s repeated submissions and historical corrections are a useful warning for any energy-state design, not a new mechanism. Current revised histories must not be substituted for archived as-known vintages.

The acoustic earnings-call idea parked in the 2026-10-18 round remains source-gated: this round did not establish a freely reusable historical audio archive or a first-public clock. Do not dispatch it automatically.

## 4. Ranked design review

Scores are qualitative source/design judgments, not return estimates or candidate-performance scores.

| Design | Orthogonality | Falsifiability | Data feasibility | Expected information gain | Decision |
|---|---:|---:|---:|---:|---|
| Compute commitment-to-delivery gap × local grid constraint | 4/5 | 4/5 | 2/5 | 3/5 | Park; first prove historical public status versions |
| Thermal infrared activity × corporate disclosure | 3/5 | 4/5 | 1/5 | 2/5 | No new candidate; overlap and commercial-source risk |
| ASC 606 × internal information acquisition | 2/5 | 3/5 | 2/5 | 2/5 | Q218/Q220 overlap |
| Dealer-network information diffusion | 3/5 | 4/5 | 0/5 | 2/5 | Reject without public investor/dealer identities |
| Macro/energy revisions | 1/5 | 5/5 | 3/5 | 1/5 | Q216/PIT infrastructure only |

## 5. Negative results and anti-cycling register

1. No new top-level candidate passed the combined orthogonality, falsifiability and public historical-data gates.
2. Do not admit the grid/compute path until a row-level, versioned public interconnection/energization history with defensible publication timestamps exists. Aggregate EIA demand and current queue pages are insufficient.
3. Do not split thermal infrared from the existing physical-data frontier without an open source contract and stable historical product/publication timestamps.
4. Do not turn ASC 606 spillovers into a new disclosure ID while the observable mechanism remains inside Q218/Q220.
5. Do not proxy the dealer-network paper with aggregate market prices; that removes the key identification variable.
6. Do not automatically dispatch the acoustic earnings-call idea; its archive/license/PIT gate remains open.
7. Do not compute novelty scores from issue #1512’s incomplete graph metadata.
8. Do not repeat already blocked or completed source probes without a new source, version, or independently justified question.

## 6. Outcome

- New candidate IDs: 0.
- One parked sub-hypothesis: Compute-Commitment-to-Delivery Gap × Local Grid Constraint; no task dispatched.
- Active Top-3, workflows, trials, evidence gates, holdout blindness and safety flags: unchanged.
- No performance selection, holdout tuning, promotion or live trading.

Next admissible step for the parked grid idea is read-only source-contract verification only. If a versioned public row-level history cannot be established, classify DATA_INSUFFICIENT and stop. Literature findings and published return results are not Trading-Agent evidence.
