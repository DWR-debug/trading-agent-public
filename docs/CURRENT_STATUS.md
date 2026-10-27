# Trading Agent — Current Operational Status

**Current operational snapshot:** `31d48f1ee68210ede3a955b73ecde1433e79c24a`

> **BINDING PROJECT STATUTES:** `docs/TRADING_AGENT_PROJECT_STATUTES.md` — **Es darf keine künstliche Arbeit erzeugt werden. Es darf ausschließlich wertvolle und hilfreiche Rechenarbeit ausgeführt werden. Und das so viel wie möglich, kontinuierlich. Wir müssen immer besser werden.**

**Generated (UTC):** `2026-10-27T05:34:26.439563+00:00`

**Repository:** `DWR-debug/trading-agent-public`

> This file is the canonical current operational status. `PROJECT_STATUS.md` is historical reconstruction and must not override it for current operational facts. Scientific evidence remains governed by the trial ledger, immutable evidence/checkpoints and workflow artifacts.

## Current state

### Current next-research focus

Active execution focus is locked to exactly three candidates: Q104:I19, Q220 and Q221. Q104:I22 has a positive independent PIT receipt but remains a separate, non-dispatched mechanism-signature and non-overlap review; this does not authorize performance. Q104:I19: PR #1351 merged the strict raw SEC SGML header parser fix after the index-header versus .hdr.sgml format mismatch; both CI architectures and full-suite verification passed on its tested revision. Frozen census run #38168441086 is terminal; repair run #38231636160 reported 7,452 repaired/25 unresolved but undercounted residual accessions. Incremental run #38250105408 reused the exact six prior repaired-shard fingerprints and reports 53 unique unresolved accession keys, zero new attempts and zero repairs across 17 SEC archives (43 CIK/form/filing-date conflicts; 10 SEC_COMPLETE_SUBMISSION_HTTP_404). PR #1363 is merged (3c0f084405b3ccc293c16dd9f0bd5affa53d3ac1): it fixes recovery-receipt accounting without relaxing identity rules. Read-only residual lineage run #38255701998 completed LINEAGE_DIAGNOSTIC_COMPLETE (receipt c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7): 4/4 frozen accessions, 12/12 SEC header probes, both source ZIPs byte-identical to the original receipt pins, 91,535,030 aggregate bytes under the 150 MB cap. In all four samples accession, filer CIK and form agree across sources, but the SEC 13F bulk SUBMISSION.FILING_DATE differs from the EDGAR header date by one calendar/business day: 2015-02-18 vs 2015-02-17 in two samples and 2020-08-10 vs 2020-08-07 in two. The acceptance timestamps are present and consistent across all three header routes. SEC's own 13F data-set readme warns the extracted data may contain discrepancies with other publication formats and is not a substitute for the full filing; EDGAR's PDS specification identifies <FILING-DATE> as the assigned official filing date. Treat this as an unresolved cross-publication source-field conflict, not a license for date arithmetic or a blanket override. Keep all 53 residuals and historical/acceptance-time gates closed; do not repair the receipts or restart the census. R4 run #38574180245 (receipt 8be8fd68de0324a331d2b587a540b605ac5c6e9a71ec203fa9d2fc089450fb3c) added one separately pinned 2017 Q2 case: bulk filing date 2017-05-31 versus EDGAR header date 2017-04-21; acceptance 2017-05-31T14:33:43; DATE-OF-FILING-DATE-CHANGE 2017-06-01 appeared on index and raw-SGML routes but was absent from the bounded complete-submission header prefix. The archive matched its frozen hash and byte-length pins, and all three routes agreed on accession, CIK and form. This single preselected diagnostic does not change the immutable 14-row aggregate, establish prevalence or first-public time, choose production precedence, repair a receipt, or clear a gate. Continue source/PIT-only work only on additional frozen inputs that offer new information; do not restart the census. R5 run #38582684174 (receipt 3d9bc88c1f43e4efac88e4528d5ac2c4b6a017beccdbe2e0e821ff150b7cd8a5) added accession 0000950123-15-003183 from the already represented 2015 Q1 archive: frozen bulk filing date 2015-02-18 versus EDGAR header date 2015-02-17; acceptance 2015-02-17T18:51:10 agrees across all three routes; DATE-OF-FILING-DATE-CHANGE 2015-02-20 appears on index and raw-SGML routes but not the bounded complete-submission prefix. The archive matched the frozen 42,434,965-byte/SHA-256 pin and all 3/3 routes completed under the 50 MB cap. R5 is a distinct row, not a new archive vintage; it does not change the immutable 14-row aggregate, establish prevalence/first-public time, choose production precedence, repair receipts, or clear a gate. R6 run #38588100012 (receipt 5571f2a8c496d32583b4b7a6bd5d6fee71533e889a5e75b434d1d84031c59522; artifact 11905763813) added accession 0000950123-13-006989 from a separately pinned 2013 Q3 archive (36,457,022 bytes; SHA-256 aa20c79d552722cb7bae8cefe3e63cd61a0929a4d5234c0b5d9ce1c75309a616). Bulk filing date 2013-08-15 differs from EDGAR header date 2013-08-14; acceptance 2013-08-14T21:51:40 is consistent across the two successful header routes; DATE-OF-FILING-DATE-CHANGE 2013-08-26 appears on raw SGML but not the bounded complete-submission header prefix; the index-header route returned HTTP 404. The original census HTTP 503 and later recovery FILING_DATE_MISMATCH remain separate pinned states. Total downloaded bytes were 36,466,001 under the 40 MB cap. R6 is an additional diagnostic row, not a modification of the immutable 14-row aggregate; it does not establish prevalence/first-public time, choose production precedence, repair receipts, or clear a gate. Keep all 53 residuals and historical/acceptance-time gates closed. The frozen concept-specific PIT compiler/independent reproduction remains closed for the full residual set: the 36 verified date-mismatch rows are admissible only for a non-destructive sidecar; seven identity-conflict and ten complete-submission HTTP 404 branches remain unresolved, and historical first-public/PIT timing is unproven. Q220 historical prefix/PIT compiler is BLOCKED: Current compiler receipt reports 55 primary-document hash mismatches. The independent reproduction references a different compiler fingerprint and is not current; it cannot reopen this gate. Next gate: repair source hash mismatches or reconcile TextBlock/presentation mapping gaps before independent reproduction; performance authorization remains closed. Current compiler receipt fingerprint c8a8082e0226c1d978e428c3473948012b935229f5b8d32338cff1595710c991.  Q220: original SEC daily Feed forensic run #38233685159 ended fail-closed with FORENSIC_COMPARISON_INCOMPLETE: 0/3 comparisons, 2,829,769,099 bytes downloaded, and no original submission member found. The source-path correction preserves the frozen receipt, population fingerprint, all 55 expected hashes and three preselected sample keys: the daily .nc.tar.gz member is accession.nc; .dissem is a distinct PDS subscriber naming convention. PR #1364 corrected the source path; PR #1366 corrected bounded HTTP streaming, separated the 150 MB outer .nc wrapper limit from the unchanged 30 MB primary-document limit, and fixed pre-document <TYPE> parsing. Post-fix run #38254139755 is terminal FORENSIC_COMPARISON_INCOMPLETE (0/3; 2,829,769,099 bytes downloaded; receipt fingerprint 840f280cbcb1fdbe4b2fbaa88f8d7f02edf447799e13fe0171d37fcd57f3221b). All three Feed archives and .nc wrappers were completely fetched and identity fields accession/CIK/form/filing date matched, but each original Feed submission header lacks ACCEPTANCE-DATETIME; all 55 frozen primary-document hash mismatches also remain. Do not redownload these multi-GB Feeds. Read-only header-only run #38258251764 completed HEADER_EVIDENCE_COMPLETE: 9/9 official EDGAR header routes, receipt fingerprint 39bf95fa15bf149094d5b56c90e58622c2339d452fd138c6deb0a463668f85b4, 101,547 bytes; no Feed or primary documents downloaded. All three fixed samples have matching accession/CIK/form/filing-date and identical ACCEPTANCE-DATETIME values across index headers, raw .hdr.sgml, and header-only .txt prefixes. DATE-OF-FILING-DATE-CHANGE was also captured: for 0000064040-19-000059 the acceptance was 2019-02-12T18:15:22 before the EDGAR filing date 2019-02-13, and its change date is 2019-02-12; the other two samples show acceptance and change date on the filing date. This is supplemental timestamp evidence only; all 55 source-hash mismatches remain and both Q220 gates stay closed. Bounded five-request HTTP representation probe [run #38590133217](https://github.com/DWR-debug/trading-agent-public/actions/runs/38590133217) completed HTTP_REPRESENTATION_INVARIANT_AT_PROBE_TIME (receipt fingerprint 870aa4fdae7eda932bb8f50ebb9eab1a7781ee503fb5120dea5b0f099e4fd65c; request sequence 2026-10-14T15:29:01Z). All five complete HTTP 200 responses were byte-identical at 4,774,457 bytes with SHA-256 fc7dfedd605cdbc9e497bb0c0bc306c74e3f90493a68fb6025d762540ef600f3; total response bytes were 23,872,285 and response bodies were not persisted. The observed bytes match none of the frozen expected, prior-captured, prior-current, or Feed-extracted body hashes/lengths. This makes request-profile and repeatability variation unsupported as the explanation at probe time; it does not establish historical source vintage or clear any gate. Do not repeat this probe or fetch further primary documents. Next, trace the frozen expected versus observed primary-document hashes and their source-vintage provenance without redownloading multi-GB Feeds or fetching primary documents. Do not change source pins, population, sample keys, expected hashes or research gates to force a pass. Q221: the 348-row frozen public-boundary sample is complete under its bounded sample contract, but first-public-observation time remains unproven for all 348 rows and all 247 recipient identities remain unmapped to issuers. The archived five policy vintages do not prove an individual award/modification clock. A fixed exploratory exact-Wayback-CDX spot check of seven award-page URLs (one per frozen year window, derived from frozen generated_internal_id values) found one captured exact URL and six no-hit responses; the captured HTML responses were only 2,171–2,696 bytes and no row-level transaction payload was verified. This is low-coverage source discovery only; no-hit is not proof of historical absence. The official GSA/SAM Contract Awards API requires a SAM.gov API key; publicDeltaDate is documented as a filter over Last Modified Date or Reveal Date, not proof that the response exposes a reproducible transaction-level first-public timestamp or retained old versions. No authenticated request was made, and unrevealed DoD data has additional role restrictions. Treat it as a desk-check lead only, not a dispatch-ready source contract. Next: do not expand the exact-page route across the 348-key sample. Seek a source with timestamped transaction-level versions or a bounded archive whose transaction-row presence can be validated, and separately freeze transaction-class applicability and pre-event recipient-to-issuer mapping. Preserve DoD/USACE 90-day, FAR 30-day, and correction-lineage checks; never map from name similarity. Q221 FPDS public-Atom identity-bridge probe [run #38712516839](https://github.com/DWR-debug/trading-agent-public/actions/runs/38712516839) used exactly four preregistered PIID requests; all four returned HTTP 302 and were blocked without following redirects. No response body was retained, total response bytes were 0, and there were 0 exact record/UEI/name matches. The capture receipt and ARM64 offline validation agree on analysis fingerprint 732a23385f9a5346e7a0806e342647658e6a4f88ea3d1ee233b956ead4277309; this validates the bounded negative result, not historical identity. Do not repeat this route or follow its redirects. No SAM.gov API request was made because no API key is assumed. Q221 remains blocked: all 348 transaction public-clock rows remain unproven and all 247 recipient-to-issuer mappings remain unfrozen. Continue only with a separately reviewed, actually authorized historical record-level source; all performance and execution gates remain closed. [Persisted receipt](https://github.com/DWR-debug/trading-agent-public/blob/master/research/evidence/q221_fpds_public_atom_identity_bridge_latest.json). Q218 has been removed from active focus and automatic dispatch. Its consumed paper-only one-shot and existing eight-event disjoint replication remain archived descriptive evidence; do not repeat an outcome-bearing run.  Q218 primary one-shot and pre-registered fresh-symbol replication both completed in PAPER_ONLY; the immutable replication result covers 8 event pairs across GOOGL/META/ORCL/PFE (fingerprint bfed980b13d9640aece19d4ebb24ccf05b5ea4589772f64001eff29728f58bb7). The primary trial current-context revalidation remains a separate open gate. Replication output is descriptive evidence only; no holdout selection, tuning, ranking, promotion or live execution is inferred.  Q219 remains paused; its prior evidence is preserved. OpenRouter-Free Q220 CYD review (AI-2026-10-10-Q220-CYD-TAXONOMY-ADVERSARIAL; 2026-10-10T15:33:02Z; USD 0) returned repeated generic boilerplate without substantive findings. Classify it as transport-success/content-unusable, not a methods review or scientific evidence. Do not automatically repeat the unchanged prompt; retry only after changing the prompt or adding content-quality validation. Q217 remains discovery/PIT-only and merges into Q131 if empirical separability fails. No holdout selection, ranking, tuning, promotion or live execution is inferred from discovery outputs. Q104:I19 independent admissibility review [PR #1484] is current for exactly 36 frozen date-mismatch rows: all 36 pass identity/header/acceptance consistency and bulk-versus-header date-difference checks (31 have three successful header routes; 5 have two, including only the four frozen R7 index-header 404 exceptions). Persisted sidecar research/evidence/q104_i19_residual_filing_date_sidecar_latest.json contains 36 sorted, source-pinned rows and has been revalidated against the exact source receipt and independent review. Admissible scope is a non-destructive research sidecar only: preserve bulk FILING_DATE unchanged, retain the EDGAR header filing date as a separate field with a discrepancy flag, keep ACCEPTANCE-DATETIME separate from first-public-observation time, and retain DATE-OF-FILING-DATE-CHANGE as separate metadata (17 observed; 15 differ from header date and 2 match). The seven CIK/form-conflict and ten complete-submission HTTP 404 rows remain outside this review. Production precedence/joins, historical PIT and first-public-time clearance, performance, holdout, ranking, tuning, promotion and live execution remain blocked. Input R7 review receipt fingerprint de6c5feca4e27f020b77890a6b00e67a87735d6572070f263ba56d8ee24d0444.

---

### Historical research handoff checkpoint — 2026-10-12T10:17Z (superseded by live Actions and receipts)

This checkpoint preserves what was known at that time. It is historical context, not current status; the generated next-research focus, live Actions, and immutable receipts take precedence.

- **Q104:I19:** PR [#1351](https://github.com/DWR-debug/trading-agent-public/pull/1351) merged the strict raw SEC SGML header parsing fix (merge commit `87b6b547009ecd1f64ff4b03d20ffcd625268754`). Both CI architectures and full-suite verification passed on the tested revision. The existing targeted repair request run [#38231636160](https://github.com/DWR-debug/trading-agent-public/actions/runs/38231636160) was still in `Repair only unresolved frozen acceptance accessions` at the last check; **no terminal repair result was verified**. Follow the current run to its terminal immutable receipt; never restart the full census blindly.
- **Q220:** The canonical PIT/compiler receipt remains `Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED`, with **55/55 primary-document hash failures**, zero verified primary documents, fingerprint `c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075`. Independent reproduction from 2026-10-11 is tied to a different compiler fingerprint and cannot reopen this gate. Forensic run [#38233685159](https://github.com/DWR-debug/trading-agent-public/actions/runs/38233685159) failed closed with `FORENSIC_COMPARISON_INCOMPLETE`: 0/3 comparisons after 2,829,769,099 bytes downloaded. The run did not establish source vintage. The latest code review distinguishes PDS `.dissem` names from daily Feed TAR members `{accession}.nc`; the exact-member resolver and fixture were corrected in a bounded follow-up. Its first CI run found a literal-placeholder NameError in five status-generator tests (2,464 passed); the f-string escaping and regression assertion are now committed. Merge only after the newest two-platform CI and full-suite checks pass, then deliberately trigger a versioned three-accession rerun; do not change frozen hashes, population, concepts, or gates to force a pass.
- **Q221:** The bounded public-boundary source sample contains 348 rows across seven fixed windows and has no query failures; it is not a complete population census (`has_next=true` in each response). Historical publication boundary is unproven for **348/348** transactions, and **247/247** distinct recipient identity candidates remain unmapped to an issuer. The current API sample and five archived policy-document vintages do not prove an individual award/modification’s first public-observation time. A fixed exploratory Wayback CDX spot check of seven award-page URLs found one exact-URL capture and six no-hit responses; the captured HTML responses were 2,171–2,696 bytes and no row-level transaction payload was verified. No-hit is not proof of historical absence. The official GSA/SAM Contract Awards API is only a desk-check lead at present: it requires an API key, and `publicDeltaDate` filters by Last Modified Date or Reveal Date; the reviewed documentation does not establish a reproducible record-level first-public timestamp or historical-version retrieval. Unrevealed DoD data has additional access restrictions, and no authenticated request was made. Do not expand the Wayback route across all 348 keys; seek a timestamped transaction-level archive and retain the event-clock, applicability, agency-exception, correction-lineage and pre-event issuer-mapping gates.
- **Permanent safety boundary:** this checkpoint authorizes only source/PIT and engineering work. `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False`, `AUTOMATIC_PROMOTION=False`. No performance, holdout selection, ranking, tuning, promotion, or live execution is authorized.

### Engineering

- Paper/Shadow/Forward infrastructure: **MERGED** via PR #352, merge commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`.
- The Forward path contains closed-candle market-data ingestion, a persistent update loop and a schema-v2 per-candle MTM ledger.
- Canonical data-layer infrastructure is merged.
- Bounded agent routing uses two queue lanes with fail-closed task contracts.
- **Permanent two-lane research mode: ACTIVE.** Lane A = **Formal Readiness** (advanced Coverage/PIT/compiler/provenance/authorization readiness); Lane B = **Frontier Discovery** (orthogonal source/PIT feasibility and cheap falsification). The two Windows slots are isolated by candidate/trial identity, branches/workflows and output/provenance paths. Cross-lane findings cannot retroactively alter a frozen trial.
- Three physical research slots are capacity only: they **never** create performance authorization. A performance run remains individually fail-closed until an exact current formal authorization exists.
- Continuous QA is scheduled every 6 hours on GitHub-hosted Windows and uses only the bounded `repo_qa` lane; it consumes no self-hosted Windows research slot.
- The deterministic frontier loop runs every 10 minutes on free GitHub-hosted Ubuntu; its three 10-step packs cover all 30 frontier-worker steps.
- Windows Self-Hosted capacity is always routable for bounded local reproduction, data QA, local-AI and hardware-dependent work; three physical slots are intended to run in parallel, with Runner C reserved for long deterministic work and independent reproduction.
- Latest self-hosted capacity verification: two distinct Windows/X64 runner slots accepted concurrent jobs; see the timestamped capacity receipt.
- S10 phone capability receipt: **S10_UTILITY_ACCEPTED**; routing availability is **ASSUMED_ALWAYS_AVAILABLE** and is independent of receipt freshness.
- S10 current physical online state is intentionally not treated as a routing blocker; the OS availability policy assumes the configured S10 resource is always routable.
- Fresh S10 receipts remain mandatory to substantiate successful execution and device-derived evidence. Receipt freshness does not remove the resource from the routing pool.
- Universal pre-formal candidate robustness gate: **ACTIVE**; structural candidate robustness must pass before PREREGISTRATION, SOURCE_FEASIBILITY, COVERAGE, PIT or PERFORMANCE formal phases.
- S10 output remains non-scientific and cannot authorize performance or promotion.
- **PERMANENT LITERATURE-RESEARCH RULE — ACTIVE:** The Trading Agent continuously searches for new, genuinely orthogonal economic mechanisms, information channels and cross-disciplinary relationships. Discovery is run on a recurring daily/weekly research cadence plus an independent public-metadata scout. Every promising finding is verified against primary sources, separated from existing candidate lineages, cheap-falsified where possible, and scored by novelty, PIT feasibility, reproducibility and information gain per compute. Negative/insufficient findings are retained to prevent cyclic rediscovery. Literature claims never become project evidence by themselves and can never authorize performance, holdout selection, ranking, tuning, promotion or live execution.

### Permanent Capacity Saturation & Rolling Research Waves

- **STATUS: ACTIVE_AND_PERSISTENT.** Useful free compute is continuously routed whenever a real bounded backlog exists.
- **Current two-hour activation:** `TA-2H-2026-10-14-RUNNER-C-CANDIDATE-GATE-0840Z`, `2026-10-14T08:40:00Z–2026-10-14T10:40:00Z`.
- **Scheduler:** every 10 minutes; active duplicates are skipped, phase-successful work is not rerun, and only one bounded retry is permitted after failure/cancellation.
- **Wave order:** W1 source/PIT/clock closure -> W2 candidate/contracts and information timing -> W3 next-gate compilation and independent reproduction -> W4 literature discovery/consolidation.
- **Utilization rule:** maximize useful occupancy across Windows A/B/C, hosted Linux, bounded free-AI lanes and S10/mobile support when those resources are reachable and the work is independent and useful. Never manufacture work to consume quota.
- **Continuous background:** the permanent Windows/hosted 10-minute loops remain active; Runner C uses long deterministic research when useful and the bounded 20-minute capacity pulse otherwise.
- **Scientific boundary:** capacity allocation never creates performance authorization, holdout selection, ranking, tuning, promotion or live execution.

### Evidence Knowledge Graph + Hypothesis Convergence — 2026-10-06

- **Stufe 4 ACTIVE:** `automation/evidence_graph_stage4_stage5.py` ingests current Evidence/Governance/Candidate/Preregistration records into a provenance-bearing metadata graph and preserves explicit negative/revision relations.
- **Stufe 5 ACTIVE:** the same engine computes deterministic mechanism-signature overlap and emits `POTENTIAL_CONVERGENCE`, `AMBIGUOUS` and `LIKELY_ORTHOGONAL` review classes plus non-authoritative bridge-hypothesis proposals.
- **Continuous wave:** `.github/workflows/evidence-graph-stage4-stage5-wave.yml` runs four parallel analyses and a 70-minute material-change-driven event-bus window. The event bus recomputes only after a material input change; there is no runtime padding.
- **Scientific boundary unchanged:** graph relations and novelty/convergence outputs cannot authorize performance, holdout selection, ranking, tuning, promotion or live execution and cannot mutate frozen trials.

### Persistent Literature & Discovery Engine

- **Status: ACTIVE_AND_PERSISTENT.** Literature discovery is a permanent OS capability, not a one-off chat task.
- Recurring assistant research: **daily literature radar** plus **weekly deep research**.
- **Active literature frontier (registry):** 084, 088, 082, FRONTIER-20260928, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, H06-P2, 120, 121, FRONTIER-Q171-Q178, FRONTIER-Q133-Q170-PIT-R1, Q131-R1, Q121-R1, Q121-R2, Q127-R1, Q130-R1, FRONTIER-Q187-Q192, FRONTIER-Q202-Q204, Q205, LITERATURE-DISCOVERY-PLANE, Q214, Q215, Q216, Q217, Q218, Q219, Q220, Q221, Q224, Q230, Q229, Q231.
- Repository metadata scout: **every 6 hours** on free GitHub-hosted compute.
- Search domains include information arrival/latency, disclosure breadth and networks, semantic novelty, disagreement, market microstructure, institutional behavior, data revisions/vintages, corporate event sequences, patent/innovation networks, unusual public-domain channels and forward-risk structure.
- Selection rule: maximize genuine mechanism novelty and orthogonality first; then cheap falsifiability, source/PIT feasibility, independent reproducibility and information gain per compute. Maximum shortlist = 4.
- The engine explicitly records **PRUNED / UNVERIFIED / DATA_INSUFFICIENT** paths to prevent rediscovering the same dead ends.
- Literature discovery is quarantined from scientific authority: no performance, holdout selection, ranking, parameter/asset/threshold/horizon search, promotion or live execution.

### Scientific status

- Latest recorded formal result: **performance_completed_no_arm_passed_all_13_gates** for `T-2026-10-01-H06P2R3-PERFORMANCE-01`.
- Q026 is recorded as **DATA_INVALID / NO_SCIENTIFIC_OUTCOME**; it did not produce performance evidence.
- Q023 is recorded as **COVERAGE_VALIDATED** and Q025 as **DATE_PIT_VALIDATED**; these are data-contract findings, not promotion evidence.
- No current candidate is authorized for promotion or live execution.
- Q091 fixed-portfolio performance is **AUTHORIZED** only when the active registry says so; the one-shot performance workflow remains fail-closed and consumes authorization only through immutable reconciliation.

### Active research registry

#### Permanent literature frontier

- **LITERATURE-DISCOVERY-PLANE:** ACTIVE_AND_PERSISTENT; daily/weekly assistant research plus a free 6-hour public-metadata scout. Discovery only.
- **Q211:** patent semantic information state — P1 source/PIT feasibility; distinct from patent publication/citation timing and price-only momentum.
- **Q212:** supply-chain disclosure sentiment propagation — P1 feasibility; network disclosure information only, with historical relationship/PIT requirements explicit.
- **Q213:** news-disagreement elasticity — P2 contingent; remains blocked until multi-year public intraday equity/news PIT feasibility is proven.
- **Q214:** disclosure-implied forward-beta/risk-structure state — P1-RISK; risk-state only, deliberately separated from Q088 peer-return/comomentum.
- All four are discovery-only. Literature claims are not project evidence; no performance, holdout selection, ranking, tuning, promotion or live execution may be derived from them.

- Q081-R2: **HISTORICAL_IMPLEMENTATION_INVALIDATED**; infrastructure-rebased corrective reproduction; no performance authorization.
- Q089: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fresh symbol-disjoint successor to quarantined Q086; separate performance authorization remains required.
- Q077-R1: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; coverage-only repair after the original Q077 pool left insufficient unused symbols; no performance authorization.
- Q091: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fixed portfolio architecture on the fresh symbol-disjoint universe; performance authorization flag = **False**.
- Q092: **DIAGNOSTIC_COMPLETED_ONLY**; post-performance Q091 failure-mechanism diagnosis; no performance authorization.
- Q093: **COMPLETED_DIAGNOSTIC_ONLY**; Q091 turnover/cost attribution diagnosis; no performance authorization.
- Q094: **PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES**; fixed monthly-rebalance successor to the Q091 low-turnover diagnosis; performance authorization flag = **False**.
- Q084, Q088 and Q082 remain **design/feasibility tracks** for unusual market-state, textual-network, rebalance-demand and SEC information channels.
- The unusual-strategy frontier is maintained in `docs/research_design/RESEARCH_FRONTIER_UNUSUAL_2026-09-28.md` and is design-only until feasibility and provenance are established.
- Research OS capability lattice: `research/governance/research_os_source_registry_2026_09_30.json`; it is metadata only and cannot authorize performance.
- Q104 orthogonal candidate wave: **SOURCE_FEASIBILITY_COMPLETED_DUAL_ARCH**; 5/6 data-backed candidates are source-feasible and Q104:R9 is synthetic-only. The archived receipt is `research/evidence/q104_source_feasibility_2026_10_01.json`.
- Q105 historical archive/PIT feasibility: **COMPLETED**, with I21 remaining historically window-limited.
- Q106 shared SEC/Treasury PIT join integrity: **COMPLETED_DUAL_ARCH**.
- Q107 fresh Q104 equity coverage: **COMPLETED**; 8/8 symbols and 3,704 common sessions.
- Q108 real SEC/XBRL/13F/Treasury PIT integration: **COMPLETED_DUAL_ARCH**; 8/8 issuer filings and 8/8 XBRL lineage verified, 13F sample and Treasury chain verified.
- Candidate-specific next gates: I19/I20 = full 13F security coverage; I22 = frozen event-state compiler; M6 = fixed Treasury state reuse; I21 = explicit bounded historical horizon; R9 = synthetic-only.

### Q129 Options Source / PIT

- Q129 historical options source-feasibility: **COMPLETED** on hosted Linux with pinned release hashes verified.
- Independent Q129 PIT/structural reproduction: **REPRODUCED**; workflow run `37123847841`, receipt fingerprint `41d723734f030d1a212f5eb4b3e6467223a5cfcdeb97c77ffa9713f8889c7587`.
- The fixed downstream view preserves raw rows and quarantines quote/calendar anomalies deterministically; same-day use remains **False**.
- This receipt does **not** authorize performance, holdout selection, ranking, tuning, promotion or live execution.

### Verified Source/PIT Frontier Outcomes — 2026-10-03

- **Q121-R1:** `Q121R1_SOURCE_ROUTE_FALSIFIED`; the preregistered SEC browse route failed its subject-issuer identity contract. The verified workflow receipt records 93 discovered entries and 15 deterministic identity checks; receipt fingerprint `9c9a3a4fa05ccc5aa8e59d254c75577abb60b869dd53ff35505b335424cfbf8e`.
- **Q121-R2:** `Q121R2_BLOCKED_BY_Q121R1_FALSIFICATION`; no independent reconciliation was claimed. Receipt fingerprint `fd7b63d9f05e0cf9abf588c9c2d6c2ff02e2ea413927218de6f4e1c29f9fff97`.
- **Q121-R3:** `Q121R3_FORM_INDEX_ROUTE_FEASIBILITY_COMPLETED`; official SEC quarterly form-index route completed for 7 quarters with 61,818 relevant form rows and 3 frozen controls. Receipt fingerprint `a18abdffe2fde48dc4084d420f0a8d5c6ade92727baa23dcecaad481e9452dc1`.
- **Q121-R4:** `Q121R4_MASTER_INDEX_ROUTE_FEASIBILITY_COMPLETED`; independent SEC quarterly master-index route completed for the same 7-quarter window with 61,818 relevant form rows and 3 frozen controls. Receipt fingerprint `3f5616d6ddc18c0f39a10316fe3cbf69e98be2911741552f8a70d133ba94c076`.
- **Q121-R5:** `Q121R5_DUAL_INDEX_POPULATION_RECONCILIATION_COMPLETED`; the form-index and master-index populations are exactly equal as multisets on the frozen window/form scope: 61,818 rows, 61,818 unique canonical keys, zero left-only/right-only keys. Receipt fingerprint `897bc13c5f722d9a701ae7994b237fe7afd233f15cdc5e644061aa674b8f26c1`. This is source-population evidence only; acceptance timestamps, revision lineage and same-day PIT safety remain unproven.
- **Q127-R1:** `Q127R1_SOURCE_PIT_FEASIBILITY_COMPLETED`; four fixed historical dates were retrieved and parsed. Revision lineage and same-day PIT safety remain unresolved. Receipt fingerprint `60815a092421762ac1da2a96d003865b72f25eb640778287964a9648cdfc5b74`.
- **Q130-R1:** `Q130R1_SOURCE_FEASIBILITY_COMPLETED`; the frozen historical Wikimedia source probe passed, while publication/revision timing remains outside formal same-day PIT safety.
- **Q131-R1:** `Q131R1_FIXED_WINDOW_NO_MATCHING_FILINGS`; the fixed 2025-09-22 through 2025-09-24 issuer/form window yielded zero matching filings, so no complexity vector was inferred. Receipt fingerprint `e5d5077874d3eaa06b688c7294e83c42d3797da1c9cffdfdb98e067112d07a70`.
- These are discovery/source/PIT findings only. They do not authorize performance, holdout selection, tuning, ranking, promotion or live execution.

### Q171–Q178 Public Source Frontier

- Source-feasibility run: **COMPLETED** on master; Q171, Q172, Q174–Q177 and Q178 passed source probes; Q173 remains license-blocked.
- PIT-readiness: Q171 has a sample historical Common Crawl reconstruction receipt; Q174–Q177 have source-clock/version/revision semantics confirmed but are **not yet candidate-specific PIT-valid**.
- No member of this wave is performance-authorized; no holdout selection, tuning, ranking, promotion or live execution is permitted.

### Q179–Q184 Orthogonal Source/PIT Frontier

- Source-feasibility latest receipt: **DISCOVERY_SOURCE_FEASIBILITY_COMPLETED**.
- Q179 ClinicalTrials.gov, Q180 NHTSA, Q181 OSHA/DOL, Q183 NTSB and Q184 FCC currently pass the bounded source probe; Q182 FERC eLibrary remains **runner-access blocked** where the GitHub-hosted probe receives HTTP 403.
- PIT Readiness R1 latest receipt: **PIT_READINESS_R1_COMPLETED_NO_PERFORMANCE**.
- Latest Q179–Q184 PIT receipt fingerprint: `66d3082c07d6fd824484ddb06167146de013f1b9757e18a4aa03733ae570c193`.
- Candidate-level PIT status remains non-authorizing; all six current statuses are surfaced directly in `research/evidence/q179_q184_pit_readiness_r1_latest.json`.
- Remaining gates are historical archive reconstruction, exact public-clock proof where not yet established, fixed entity mapping, revision/amendment lineage and independent reproduction. No performance, holdout selection, tuning, ranking, promotion or live execution is authorized.
### Q197–Q201 Orthogonal Information Frontier

- Q198 Federal Register: **SOURCE_COMPONENT_READY**; source receipt `1d9b6b1bd0a6138ffa2f7d8a981367a2f5b4cb9647ff803c46bf4abb97247d7f`. Next gate: fixed historical Public Inspection filing clock, correction/withdrawal lineage, immutable reconstruction and independent PIT reproduction.
- Q197 USAspending: **SOURCE_COMPONENT_READY**; source receipt `1d9b6b1bd0a6138ffa2f7d8a981367a2f5b4cb9647ff803c46bf4abb97247d7f`. Next gate: historical award-state revision/public-observation boundary, frozen pre-event relationship network and independent event-time reproduction.
- Q199 USPTO: **HISTORICAL_SOURCE_COMPONENT_READY**; source receipt `4a67518bfcfb51dcd92edc99c5fd7d6bff1ad2340a387bc880e050d6ad7b8ce7`. Next gate: historical publication-state archive, frozen assignee/technology exposure and independent PIT reproduction.
- Q201 ClinicalTrials.gov: **SOURCE_COMPONENT_READY**; source receipt `4a67518bfcfb51dcd92edc99c5fd7d6bff1ad2340a387bc880e050d6ad7b8ce7`. Next gate: historical results-state revision lineage, explicit posted-time semantics, frozen sponsor/exposure mapping and independent PIT reproduction.
- Q198 historical PIT clock census: **Q198_PIT_CLOCK_CENSUS_COMPLETED**; pages parsed **4** / **4**, with fixed dates **2020/01/10, 2020/04/22, 2020/12/16, 2026/10/02**.
- All four frontier candidates remain non-authorizing: performance/holdout selection/ranking/tuning/promotion/live execution are closed. Source readiness is not PIT validation.
### Q202–Q204 Information-Timing Frontier

- Q202 ClinicalTrials.gov: **SOURCE_COMPONENT_READY**; source receipt `b554c0d649e1d3de2bcec87b284b8eed9184dbe1eeba391894ea348269769bb5`. Next gate: immutable historical record-version snapshots at the applicable reporting boundary, applicability/certification/extension lineage, frozen sponsor-to-issuer mapping and independent PIT reproduction.
- Q203 Federal procurement × ex-ante financing constraint: **SOURCE_COMPONENT_READY**; source receipt `b554c0d649e1d3de2bcec87b284b8eed9184dbe1eeba391894ea348269769bb5`. Next gate: immutable historical award-state/public-observation boundary, frozen pre-event financing vintage and entity mapping, correction/amendment lineage and independent PIT reproduction.
- Q204 Public-information release latency: **SOURCE_COMPONENT_READY**; source receipt `b554c0d649e1d3de2bcec87b284b8eed9184dbe1eeba391894ea348269769bb5`. Next gate: immutable public-observation/process-stage timestamps, fixed event-class semantics, pre-event-only latency calibration and correction/withdrawal lineage.
- Q202–Q204 remain source/PIT discovery tracks only: performance, holdout selection, ranking, tuning, promotion and live execution remain closed. Source feasibility is not PIT validation.

### Q148-R1 EIA WPSR Source/Clock Gate

- Receipt status: **Q148R1_WPSR_SOURCE_CLOCK_CONTRACT_COMPLETED**.
- Persistent receipt fingerprint: `30e29926cd9a05d803426765a64d0c13354f824fbfc3d9abc430a379d4569cd0`.
- Frozen controls: **3**; exact first-public-availability timestamp proven = **False**.
- Candidate-specific revision lineage proven = **False**; same-day PIT safe = **False**.
- This gate is source/clock evidence only; performance, ranking, holdout selection, tuning, promotion and live execution remain closed.

### Q137/Q144 Historical Micro-PIT

- Micro-PIT receipt status: **MICRO_PIT_SAMPLE_COMPLETED_NO_PERFORMANCE**.
- Q137 SEC all-symbols reconstructable = **False**.
- Q144 Wikimedia all-symbols reconstructable = **False**.
- This bounded sample produced feasibility evidence only; unresolved archive/entity coverage stays fail-closed.

### Q169 R4 Independent NOAA Reproduction

- Independent reproduction status: **Q169_R4_INDEPENDENT_REPRODUCTION_COMPLETED**.
- Persistent receipt fingerprint: `7b6b36a207023d82fac0990872a10203d022bae5421ab58cf417b69c15784031`.
- All fixed R3 archive samples reproduced = **True**.
- Candidate-specific exposure map frozen = **False**; revision lineage reconstructed = **False**.
- This strengthens NOAA source/archive provenance only; candidate PIT validation and performance remain closed.

### Q133–Q170 Public Source Frontier

- Hosted discovery/source-feasibility run: **COMPLETED**; 25 source probes passed across Q133–Q170.
- Newly source-feasible candidates include Q137, Q144, Q147–Q151, Q153–Q155, Q157–Q158, Q161–Q169; remaining candidates stay blocked or design-only pending further source/PIT work.
- **PIT-readiness R1 is now ACTIVE** for the 21 source-feasible candidates; it audits candidate-specific clock, revision/version, entity-mapping and historical-archive requirements without evaluating returns or ranking candidates.
- Source-feasibility and PIT-readiness are not performance evidence and do not authorize performance, holdout selection, ranking, tuning, promotion or live execution.

### H06 independent PIT

- Status: **PIT_REPRODUCED_RECONCILED**.
- Independent reproduction workflow: `36843059301`.
- Canonical coverage workflow: `36842998210`.
- Checked PIT decision points: **2545**.
- Semantic check fingerprint: `658ed9e58edb457bf42337fc3ebf081178d157ae88ca0bcca5745112eb60aae7`.
- This is PIT/data-contract evidence only; it does not authorize performance or promotion.

### Q067 execution pipeline

- Operational state: **RETIRED**.
- Coverage receipt: **MISSING**.
- PIT receipt: **MISSING**.
- Performance authorization: **False**.
- Performance evidence: **MISSING**.
- Ledger reconciled: **False**.
- Blocking reasons: **obsolete execution path retired; historical evidence preserved**.

This is an operational pipeline summary only; it does not create scientific evidence or select a candidate.

### Q068 execution pipeline

- Operational state: **RETIRED**.
- Coverage receipt: **MISSING**.
- PIT receipt: **MISSING**.
- Performance authorization: **False**.
- Performance evidence: **MISSING**.
- Ledger reconciled: **False**.
- Blocking reasons: **obsolete execution path retired; historical evidence preserved**.

Q068 is a fresh symbol-disjoint validation of the unchanged Q067 E1/E2 mechanisms. This operational summary does not create scientific evidence or select an arm.

### Q070 execution pipeline

- Operational state: **PERMANENTLY_BLOCKED**.
- Coverage receipt: **COVERAGE_PASSED**.
- PIT receipt: **PIT_PASSED**.
- Performance preregistration: **PERMANENTLY_BLOCKED**.
- Performance authorization: **False**.
- Performance evidence: **MISSING**.
- Ledger reconciled: **False**.
- Blocking reasons: **frozen snapshot unrecoverable; execution workflows retired**.

Q070 is the fresh symbol-disjoint validation pipeline for the fixed Q069 OHLCV candidate bank. This operational summary does not create scientific evidence or rank candidates.

### Operator action when runner capacity is being (re)activated

- Open **two PowerShell windows** on the Windows research PC.
- Keep the existing Runner #1 process running in window 1.
- Use window 2 for Runner #2 (LHT-N133732-2).
- When activation/reconfiguration is needed, paste the resulting **non-secret** commands/output into the current "trading agent" chat so the orchestration can verify the live state.
- **Never paste registration tokens, API keys, OAuth tokens or passwords into chat.**
- Do not switch a runner to Windows service mode until local AI authentication has been verified; Windows service mode requires administrative privileges and can change the user/keyring context available to local AI CLIs.

### Resource policy

- Paid agent/API budget: **0 USD**.
- Actual available capital: **0 EUR**.
- Hypothetical reference capital: **2000 EUR**, simulation/planning only.
- Legacy 500-EUR operational canary remains separate.
- Deterministic research stays on reproducible runner paths.
- Agent output is never scientific evidence by itself.
- Protected Copilot reserve starts **2026-10-01T00:00:00Z**: at most 4 sessions/month, 30 AI credits/session, 1 concurrent session; actual entitlement is verified at dispatch and no paid fallback/overage is permitted.
- Permanent research continuity uses the two self-hosted Windows lanes every 30 minutes, event-driven free-AI review only when a new high-value task contract or material research-state change warrants it, always-routable S10/Android utility capacity, and bounded agent dispatch every 2 hours. Hosted research failover is manual-only.

## Safety

`PAPER_ONLY=True`

`LIVE_TRADING_ENABLED=False`

`ORDERS_ENABLED=False`

`AUTOMATIC_PROMOTION=False`

## Canonical source order

1. Current operational facts: `docs/CURRENT_STATUS.md` and `research/evidence/current_operational_state.json`
2. Technical truth: current `master`
3. Scientific evidence: trial ledger, immutable evidence/checkpoints and workflow artifacts
4. Project intent: `docs/PROJECT_CONTEXT.md`
5. Historical reconstruction: `PROJECT_STATUS.md`

## Continuity protocol

Every relevant `master` push triggers the status synchronizer. It records the exact source commit being synchronized and updates these two operational-status files in a documentation-only commit. Those files are excluded from the synchronizer trigger, preventing recursive commits.

A future `trading agent` chat must read this file first, then verify live GitHub state before acting.
