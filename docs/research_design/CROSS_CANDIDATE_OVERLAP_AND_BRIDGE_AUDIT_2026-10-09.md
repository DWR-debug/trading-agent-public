# Cross-Candidate Overlap Audit and Innovation-to-Deployment Bridge

**Date:** 2026-10-09  
**Classification:** design-only / discovery-only  
**Master basis:** `482aadabac5a29dd6fbf382cfdaf1d007c0768f8`  
**Purpose:** Reduce duplicated research, preserve genuinely distinct mechanisms, and test one cross-family relation without widening the active execution queue.

## Executive decision

1. Keep the active execution lock unchanged: **Q104:I19** (historical 13F/source-PIT closure) and **Q218** (mandatory/voluntary SEC disclosure source/PIT work). This note authorizes no run.
2. Treat **Q227 and Q231** as a likely duplicate pair: both are defined as SEC FOIA information-acquisition state. Consolidate to one canonical mechanism and preserve the non-canonical ID as a historical alias after a provenance check.
3. Keep Q204, Q215 and Q223 separate only if the observation they measure remains demonstrably distinct: generic stage latency; an external state preceding issuer disclosure; and independent corroboration/contradiction, respectively. A scalar “time between two sources” alone is not enough to justify a separate candidate.
4. Record one dormant bridge hypothesis: **public R&D award → public technical output → independently documented follow-on procurement/deployment**. It links existing Q221, Q191 and Q197 work but must initially be tested as a sub-hypothesis, not promoted to a new top-level candidate.
5. Fix the research OS’s overlap registry and status freshness before increasing candidate count. The objective is more information per unit of compute, not more candidate IDs.

## Audit basis and boundaries

The current project files define Q104:I19 and Q218 as the focused execution wave, while the wider candidate contracts are design-only. This audit compared the current candidate-specification file, the 2026-10-06 discovery seed pack, the 2026-10-05 synthesis, the canonical OS routing state and the binding project statutes. It did not inspect outcomes or change a trial contract.

Current live status must continue to be checked against Actions receipts. At the time of this audit, I19 run [37931811984](https://github.com/DWR-debug/trading-agent-public/actions/runs/37931811984) was still in progress: completed shards reported acceptance-join failures, while two shards remained active. Do not cancel/restart the run or start a retry until all six shards terminate and their receipts/artifacts are reconciled. See the operational follow-up in [issue #1256](https://github.com/DWR-debug/trading-agent-public/issues/1256).

## 1. Overlap map

| Candidate family | Relationship | Decision |
|---|---|---|
| **Q227 / Q231 — SEC FOIA information acquisition** | **Likely same mechanism and same primary source.** Both concern explicit requests for otherwise non-public SEC records and requester/topic composition. Their detailed features can be combined into one contract. | Consolidate to one canonical ID after checking whether either ID has separate frozen trials or receipts. Preserve the other as an alias; do not independently dispatch both. |
| **Q204 / Q215 / Q223 — source timing and corroboration** | Adjacent, not automatically identical. Q204 measures release/process-stage latency; Q215 asks whether an external public state pre-existed issuer disclosure; Q223 asks whether an independent source later corroborates or contradicts an already public event. | Define the distinguishing observable in each contract. Merge Q223 into Q204 if it reduces to a second-source timestamp; merge it into Q215 if it reduces to “external state first.” Keep it distinct only if source independence and confirmation content are mechanically observable and historically reproducible. |
| **Q217 / Q220 / Q222 — information processing, representation and verification** | Related, but the object differs: complexity/friction adjusted for size and boilerplate; mismatch between narrative and structured XBRL within a filing; divergence between a corporate implementation claim and independently observable implementation evidence. | Share common filing, text-block and provenance compilers; preserve separate event objects. Require Q222’s external implementation evidence to have a defensible historical public clock. |
| **Q197 / Q203 / Q221 — federal awards** | Shared USAspending/award lineage, but different claims: demand propagation through a frozen network; award conditional on a pre-event financing constraint; R&D award option value and competition/capability state. | Share award identity, amendment lineage and public-observation-boundary code. Keep candidate-specific features and falsifiers separate. Award/action date is not silently substituted for first public observation. |
| **Q176 / Q191 / Q196 / Q199 — science and patents** | Shared bibliographic/patent entities and chronology; different objects: publication burst, science→patent stage order, examiner/applicant citation provenance, and first patent publication. | Reuse identifiers, family/assignee maps and revision controls. Do not equate counts, stage gaps and citation provenance. |
| **Q192 / Q194 / Q233 / Q235 — product supply and regulatory state** | Same broad FDA/product/manufacturer neighborhood, but distinct states: shortage/substitution, cross-product therapeutic pressure, regulator-confirmed recall severity, and import-access restriction. | A common product/manufacturer identity layer is valuable. Any combined state must be a preregistered chronology, not a post-hoc blend of four signals. |
| **Q190 / Q195 / Q205 / Q228 and related state-transition candidates** | Repeated “public state moves from stage A to stage B” structure across different institutions and event objects. | Build reusable, typed state-machine infrastructure—effective date, first-public clock, correction/appeal/withdrawal lineage and unresolved state—without declaring the economic mechanisms duplicates. |
| **Q224 / Q226 — EDGAR access logs** | Related source and population; Q224 is acquisition intensity while Q226 is the age composition of requested filings. | Share the access-log parser and traffic-quality controls. Q226 survives only if age composition adds a distinct observable beyond total demand, and the SEC’s known missing interval/schema differences remain explicit. |

### Important distinction: shared data are not proof of duplication

A common source, entity graph or date field is often an opportunity to save engineering effort—not a reason to combine research questions. Conversely, a different candidate number or feature name does not make two hypotheses independent. The decision must be based on the economic object, information boundary and decisive falsifier.

## 2. Dormant bridge hypothesis: innovation-to-deployment conversion sequence

**Research question.** Among a source-defined population of public R&D awards, can a mechanically linked chronology distinguish awards that progress through a first public technical output and then into independently documented follow-on procurement/deployment from awards that remain at an earlier public stage? The object is the **conversion sequence and its observable stage order**, not award size, patent count, paper count or a generic government-contract shock.

### Proposed sequence

1. **Public R&D award:** the exact award/recipient and the first defensible public-observation boundary. Award/action date is separate metadata; it is not automatically the public clock.
2. **Technical output:** the first admissible public patent-application publication or scientific-publication boundary, linked by a direct identifier or a frozen recipient/technology relationship. Patent priority/filing dates must not be treated as public knowledge before publication.
3. **Follow-on realization:** a separate public contract/procurement/deployment event tied to the same technical effort by contract lineage or a predeclared and independently verifiable technology/recipient relationship. A later award to the same vendor, by itself, does not prove conversion.

The primary state would be a small fixed state machine such as `AWARD_ONLY`, `TECHNICAL_OUTPUT_PUBLIC`, and `FOLLOW_ON_REALIZATION_PUBLIC`, plus an explicit `UNKNOWN/UNRECONSTRUCTABLE` state. Stage lags are derived only when both endpoint clocks are admissible. Do not select lags, thresholds, technologies, agencies or issuers based on market outcomes.

### Why this is not simply Q221, Q191 or Q197

- **Q221** examines the option value and competitive/capability context embedded in a public R&D award.
- **Q191** asks about the relative public timing of scientific publication and patent disclosure.
- **Q197** examines a newly public procurement award and propagation through an ex-ante network.
- The bridge asks whether these observables form a reproducible **ordered conversion path** from funded technical work to independently visible technical output and then external demand.

This remains a bridge/sub-hypothesis under Q221/Q191 until separability is shown. It must be merged or rejected if it merely recombines their existing variables without a distinct, preregisterable state.

### Existing prior art and a critical sampling trap

The open 3PFL dataset links federal procurement contracts/grants to associated patents and scientific publications. The underlying 2019 study reports a long and heterogeneous R&D-to-patent process, including an average contract-to-patent gestation lag of roughly 33 months in its study population ([PLOS ONE paper](https://doi.org/10.1371/journal.pone.0218927); [public 3PFL dataset](https://zenodo.org/record/3369582)).

**The dataset must not define our primary denominator.** Its described contract tables include contracts that generated at least one patent. Sampling only from it would condition on observed technical output and exclude non-converting awards, creating selection bias. Use 3PFL only as a linkage scaffold and prior-art check; define the eligible population from the full source-side award universe and reconstruct each decision-time state from primary sources.

### Cheapest falsification gate — no returns and no new runner job

1. Freeze one source-defined award population and time window before examining outputs; select a deterministic hash sample from the **full award universe**, not from patent-producing records.
2. Test direct contract/award ID and recipient identity joins first. Record exact match type, ambiguous joins and false matches. Keyword-only semantic joins cannot establish event identity.
3. For the sample, reconstruct the first public clocks from source-side artifacts and version/revision records. A current API response alone is not historical evidence.
4. Verify that a purported follow-on contract is linked to the same technical effort. “Same vendor later received money” is a negative control, not a successful conversion join.
5. Apply future-row/revision mutation tests and a frozen identity-map shuffle. Preserve failed matches and `DATA_INSUFFICIENT` as first-class outputs.

**Stop immediately** if first-public award time cannot be established, source history has been overwritten, award-to-output identity requires hindsight, follow-on procurement cannot be distinguished from unrelated same-vendor work, or only patent-producing awards can be reconstructed. No performance, holdout, ranking, tuning, asset/horizon selection, promotion or live execution is part of this gate.

### Public, zero-paid-cost source leads

- [USAspending.gov](https://www.usaspending.gov/) — award/transaction lineage; first-public historical boundary still needs proof.
- [USPTO Open Data Portal](https://data.uspto.gov/) — patent/publication and bulk-data discovery; product access/API terms and release clocks must be verified for the exact route.
- [OpenAlex](https://api.openalex.org/works) and [Crossref](https://api.crossref.org/works) — scientific metadata; deposited/indexed/publication clocks remain distinct.
- [3PFL on Zenodo](https://zenodo.org/record/3369582) — public linkage scaffold only, not the universe or PIT authority.

## 3. Project-level improvements with the best leverage

### A. Add a canonical relation registry

For every candidate, persist these fields alongside the existing scientific contract:

- `canonical_mechanism_id`
- `relation_type`: `SAME_MECHANISM`, `SUBTYPE_OF`, `BRIDGE_TO`, `SHARED_SOURCE_ONLY`, or `ORTHOGONAL_BY_OBSERVABLE`
- `shared_pipeline_ids`
- `decisive_distinguishing_observable`
- `merge_or_kill_rule`
- `source_clock_status` and `entity_linkage_status`
- `canonical_id / alias_of` where needed
- `active_execution_allowed` derived from the existing policy, never authored by a discovery note

The evidence graph should distinguish “shared source” from “shared mechanism.” Overlap suggestions remain non-authoritative until reviewed; a graph edge must never change candidate status, trial inputs or authorization.

### B. Put duplicate control before capacity dispatch

Before dispatch, compare the proposed workpack with active/running and recently successful work by canonical mechanism, source window, input fingerprint and next gate. Block only genuine duplicates; allow distinct candidates to reuse a validated source compiler. Require a written distinguishing observable when two candidates share the same primary source and economic event.

### C. Make snapshot freshness explicit

The current `docs/CURRENT_STATUS.md` and `research/evidence/current_operational_state.json` snapshot is generated at `2026-10-09T14:14:25Z`; the master commit used for this audit is `482aadabac5a29dd6fbf382cfdaf1d007c0768f8`, committed at `2026-10-09T18:30:25Z`. The snapshot therefore predates that master commit by at least 4 h 16 min. Display this as **STALE_RELATIVE_TO_MASTER** until refreshed, and keep “latest master,” “live run state,” “latest receipt,” and “snapshot generation time” as separate fields. A successful evidence-publishing commit does not by itself prove that the current operational snapshot has been regenerated.

### D. Diversify free literature discovery without confusing metadata with evidence

The current scout searches OpenAlex metadata plus public GitHub repositories and web-linked/Hacker News results. Add Crossref and arXiv metadata as additional free discovery lanes only with bounded queries, DOI/arXiv deduplication, primary-source verification and an explicit source timestamp. HN/GitHub popularity is a discovery cue, not a scientific quality or market-edge score. Search novelty against our own candidate/evidence graph before creating a new seed. Literature output remains advisory.

## Recommended order

1. Finish and reconcile the current I19 census; then recover only accession headers missing from completed shard receipts and any unresolved sets in the remaining shards.
2. Continue Q218’s already active source/PIT gates without re-running successful work.
3. Create the Q227/Q231 canonical-alias decision after checking existing IDs, artifacts and trials.
4. Implement relation-registry and stale-snapshot checks as separate, tested engineering changes.
5. Run the bridge’s cheap source/identity/clock falsification only after the active execution lock has free capacity and the gate is independently assigned. If the gate fails, persist the negative result and stop.

## Sources and provenance

- Candidate contracts: `research/candidates/orthogonal_candidate_specs_2026-10-05.json`
- Discovery seeds: `research/frontier/orthogonal_discovery_seed_pack_2026_10_06.json`
- Research synthesis: `docs/research_design/DEEP_CANDIDATE_RESEARCH_SYNTHESIS_2026-10-05.md`
- Binding statutes: `docs/TRADING_AGENT_PROJECT_STATUTES.md`
- 3PFL dataset and study linked above.
- SEC EDGAR log limitations: https://www.sec.gov/data/edgar-log-file-data-set.html

## Safety

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`ORDERS_ENABLED=False`  
`AUTOMATIC_PROMOTION=False`

This document is a design audit only. It creates no scientific evidence, changes no frozen trial, dispatches no research workflow and grants no authorization.
