# Prioritized Cross-Domain Research Wave — 2026-10-14

**Classification:** literature/source synthesis; design-only; no performance authorization  
**Repository basis:** current master as of PR creation; technical truth remains master and immutable receipts  
**Discovery scope:** 15 targeted search calls across 10 distinct workstreams; 138 returned result slots before deduplication; selected sources were opened and checked against primary/official pages where available  
**Active execution lock:** Q104:I19, Q220, Q221 only  
**Safety:** PAPER_ONLY; no live trading, orders, performance, holdout selection, ranking, tuning, promotion, or paid data/API use

## 1. Executive decision

The highest-value operational finding was that the scheduled Literature Frontier Scout was failing before it could produce discovery evidence. Run [38559281959](https://github.com/DWR-debug/trading-agent-public/actions/runs/38559281959) lacked `pytest`; after [PR #1441](https://github.com/DWR-debug/trading-agent-public/pull/1441) restored that dependency, run [38570923825](https://github.com/DWR-debug/trading-agent-public/actions/runs/38570923825) exposed an undefined run-scoped output variable `OUT`. [PR #1443](https://github.com/DWR-debug/trading-agent-public/pull/1443) added a scoped smoke trigger, and [PR #1445](https://github.com/DWR-debug/trading-agent-public/pull/1445) defined the output path. The subsequent scout run [38571272581](https://github.com/DWR-debug/trading-agent-public/actions/runs/38571272581) completed all steps and uploaded an immutable artifact. This is a successful metadata-discovery receipt; metadata remains discovery-only, not project evidence.

The external research produced three useful dispositions:

1. **Q104:I19 — keep source-clock distinctions explicit.** SEC documentation says filings are often available on sec.gov 1–3 minutes after the EDGAR system timestamp, but the lag can increase significantly and is neither guaranteed nor predictable. Acceptance time therefore is not a verified public-availability timestamp. The observed filing-date field conflict must remain diagnostic until additional frozen archive vintages establish the scope and the formal source contract is reviewed.
2. **Q220 — the HTTP-profile hypothesis is now falsified for the tested sample, not the historical lineage question.** Five bounded responses had identical hashes and lengths across the preregistered request profiles. Do not repeat downloads or rewrite the 55 frozen expected hashes. Continue with offline extraction/source-vintage lineage.
3. **Q221 — the SAM.gov Contract Awards API is not yet a valid first-public-clock substitute.** The official documentation requires an API key, restricts unrevealed DoD data, and documents deleted-contract retrieval only for a rolling six-month window. The reviewed contract does not prove a durable transaction-level first-public timestamp plus historical-version/correction lineage. Keep it as a desk-research lead, not an executable connector.

A cross-market annual-report graph is the strongest external candidate-development lead in this pass, but it overlaps the existing Q088 textual-peer/network family. It should be **merged as a possible Q088 sub-design or killed on overlap**, not assigned a new candidate ID and not dispatched while the active three-candidate lock remains in force. Satellite/AIS/port activity is already documented in prior frontier work and is not reopened as a new family here.

## 2. Evidence and source assessment

### 2.1 SEC filing clocks: acceptance is not public availability

The SEC's [Webmaster FAQ](https://www.sec.gov/about/webmaster-frequently-asked-questions) states that filings are often available within 1–3 minutes of the EDGAR system timestamp, while the lag can grow under high server load and cannot be guaranteed or predicted. This is direct evidence that acceptance and website availability are distinct clocks. It does **not** provide an event-level timestamp for when a specific historical document first became publicly readable.

**Application to Q104:I19**
- Preserve the frozen bulk date, header filing date, acceptance timestamp, and `DATE-OF-FILING-DATE-CHANGE` as separate fields.
- Do not infer that the date-change field supersedes the header date or that either field proves the first-public clock.
- Extend header-only observations across additional already-frozen date-mismatch archive vintages only after the exact sample keys, routes, budgets, and source receipt fingerprints are preregistered.
- Keep the existing 14-row aggregate descriptive and unchanged; the R4 row is recorded separately and is not silently merged into that immutable receipt. Do not repair source receipts or restart the census based on this literature finding.



**Q104 R5 preregistration — distinct frozen 2015 Q1 accession (not a new vintage):** The immutable census artifact for shard `2013-2016` (run #38168441086; shard receipt fingerprint `dbe0651154dd4e34ee1aac729f48cf1536c99e28d17666e70178898ab198a27f`) records `0000950123-15-003183` as `FILING_DATE_MISMATCH` in the pinned `2015q1_form13f.zip` (42,434,965 bytes; SHA-256 `96ab4cb60063beb98317ce3e2558b3539546e54485fdb1c68adcd33b5634a6ee`). This accession is not in the immutable 14-row aggregate (which includes two other 2015 Q1 accessions), so it is a distinct frozen row but **not** a new archive vintage. R5 is designed to fetch that single exact archive once, require byte/hash equality before parsing, then capture the three established header routes for the one preselected accession. Source archive cap 50,000,000 bytes; total download cap 50,000,000 bytes; each header response cap 262,144 bytes; one-second request spacing. No census restart, repair, production precedence, performance use, or gate clearance. A missing/changed pin or incomplete route fails closed. The run request is frozen in `research/run_requests/q104_i19_residual_source_lineage_r5.trigger`; workflow is `.github/workflows/q104-i19-residual-source-lineage-r5.yml`.

**Q104 R5 result — run #38582684174:** Completed successfully with immutable receipt fingerprint `3d9bc88c1f43e4efac88e4528d5ac2c4b6a017beccdbe2e0e821ff150b7cd8a5` (artifact [q104-i19-residual-lineage-r5-38582684174-1](https://github.com/DWR-debug/trading-agent-public/actions/runs/38582684174/artifacts/11902804060), archive SHA-256 `db4a995d31dfc123c142bb22caa030cd714e88ffbda4ccd78287717d9ae36d8e`). The frozen 2015 Q1 ZIP matched the expected 42,434,965 bytes and SHA-256 `96ab4cb60063beb98317ce3e2558b3539546e54485fdb1c68adcd33b5634a6ee`; total network bytes were 42,447,464 of the 50,000,000-byte cap, and all 3/3 header routes completed. For accession `0000950123-15-003183`, the frozen bulk row says filing date `2015-02-18`, while index headers, raw SGML header and bounded complete-submission header prefix all report `2015-02-17`; all routes agree on accession, filer CIK `0000860656`, form `13F-HR` and acceptance `2015-02-17T18:51:10`. `DATE-OF-FILING-DATE-CHANGE=2015-02-20` appears in index and raw-SGML routes but not the bounded submission prefix. This is another source-field conflict from the already represented 2015 Q1 archive vintage, not a new vintage or evidence of first-public time. It does not establish prevalence, production precedence, historical/acceptance-time gate clearance, or authority to repair the 53 residuals. Census and all 53 residuals remain unchanged.


**Verified one-row R4 follow-up — 2017 Q2 archive:** [run #38574180245](https://github.com/DWR-debug/trading-agent-public/actions/runs/38574180245) completed with `LINEAGE_DIAGNOSTIC_COMPLETE`, receipt fingerprint `8be8fd68de0324a331d2b587a540b605ac5c6e9a71ec203fa9d2fc089450fb3c`, and [immutable artifact #11899236364](https://github.com/DWR-debug/trading-agent-public/actions/runs/38574180245/artifacts/11899236364). The sole frozen accession `0001008929-17-000008` was found in the pinned `2017q2_form13f.zip`; source archive length and SHA-256 matched the historical census pin. Three preregistered header routes completed without errors; the total bytes across the archive and header responses were 43,305,542 under the 50,000,000-byte budget.

- Frozen bulk row: `FILING_DATE=2017-05-31`, `13F-HR`, filer CIK `0001008929`.
- Index-header and raw-SGML routes agreed on EDGAR header `FILING-DATE=2017-04-21`, acceptance timestamp `2017-05-31T14:33:43`, and `DATE-OF-FILING-DATE-CHANGE=2017-06-01`. All three routes agreed on accession, filer CIK and form.
- The bounded complete-submission header prefix retained the 2017-04-21 filing date and acceptance timestamp, but the date-change field was absent from that representation. All three routes disagreed with the frozen bulk filing date.

This is one preselected observation, not a prevalence estimate. It reinforces that the bulk filed date, EDGAR header filed date, acceptance time, and date-change field are distinct, and that date-change observability depends on the header representation. It does not establish which date should control a production join or when the record first became public. No precedence was applied, no source receipt changed, the census was not restarted, and no historical/PIT/performance gate was cleared.

**Reusable infrastructure idea:** represent each event's information time as a *typed boundary with evidence quality*, not a single unqualified date. Where first public availability is not directly observed, store the known lower/upper constraints and the evidence supporting them; exclude events whose uncertainty interval crosses the decision cutoff. Do not manufacture an exact timestamp from an acceptance date, a date-only field, a later download, or a missing archive capture.

### 2.2 Q220: separate HTTP representation from historical provenance

The preregistered [Q220 HTTP representation design](https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q220_HTTP_REPRESENTATION_SENSITIVITY_2026-10-13.md) tested exactly five request profiles against one fixed SEC primary document. The resulting run [38568650121](https://github.com/DWR-debug/trading-agent-public/actions/runs/38568650121) recorded five complete HTTP-200 responses, each 4,774,457 bytes with the same SHA-256 hash. That differs from the frozen expected length/hash, so the classification is invariant at probe time, not a Q220 pass.

This rules against the specific explanation that the tested User-Agent/Accept profile variations caused the observed bytes to change. It does not identify which historical source version generated the frozen expectation.

**Next action:** offline lineage reconciliation only: compare immutable source receipts, extraction/member identity, original population inputs, exact archive member path, and code revision that created the frozen expected hash. Preserve all 55 failures and the closed PIT gate. No more Feed/primary-document requests until the governing next gate changes through a preregistered, independently tested route.

### 2.3 Q221: source semantics and retention boundaries

The [official GSA/SAM.gov Contract Awards API documentation](https://open.gsa.gov/api/contract-awards/) and its [published OpenAPI contract](https://open.gsa.gov/api/contract-awards/v1/openapi.yaml) were checked directly (documentation version v1.0; changelog updated 2026-08-25 to add `publicDeltaDate`). The API supports revealed records, while unrevealed DoD data requires a DoD-assigned access role and API key. The `deletedStatus=yes` route covers deleted contracts only within a rolling six-month window.

The contract has transaction identifiers (`PIID`, modification number, transaction number) and response metadata including `awardDetails.transactionData.createdDate`, `lastModifiedDate`, `approvedDate`, and `version`. However, the OpenAPI response schema does **not** define a record-level `revealDate` / first-public timestamp field, nor an endpoint for requesting an arbitrary historical version. The documentation defines `publicDeltaDate` only as a *search filter* matching Last Modified Date **or** Reveal Date; it does not state that the matched Reveal Date is returned as a per-record value or that old response versions can be reconstructed. A version property plus a query parameter named `documentVersion` is not a documented version-history retrieval contract.

Therefore, this route is not sufficient for Q221's first-public-clock and historical-lineage gates. It also does not resolve the frozen 348 rows' pre-event recipient-to-issuer identity mapping, nor the applicability/correction/supersession questions.

**Independent alternate-route check — legacy FPDS Atom Feed (2026-10-14):** the official [FPDS Atom Feed FAQ](https://www.fpds.gov/wiki/index.php/ATOM_Feed_FAQ) describes a daily-updated feed and directs consumers to filter by *Last Modified Date*. The published [Atom Feed specification](https://www.fpds.gov/wiki/index.php/Atom_Feed_Specifications_V_1.5.2) includes entry-level `modified` metadata, but neither that field nor FPDS's system-generated “Date/Time Stamp Accepted” establishes the first time the transaction was publicly observable. GSA's [decommission notice for the FPDS XML archives](https://fpds.gov/fpdsng_cms/index.php/en/newsroom/164-decommission-of-fpds-xml-archives.html) says those archives were decommissioned in 2021; the [old Atom-feed versions were also decommissioned](https://fpds.gov/fpdsng_cms/index.php/en/newsroom/163-decommission-of-old-fpds-atom-feed-versions.html). The reviewed documentation does not provide a durable, arbitrary historical-version retrieval contract or a transaction-level first-public timestamp. This is a **no-go for Q221's decisive gate**, not a reason to probe the live feed: no Atom/API request was made, and no additional records were downloaded. Do not repeat this desk check unless the source publishes a materially different documented history/version contract.

No authenticated API call was made and no API key was used. No data was downloaded from the API.

**Next action:** stop further desk research on this same API unless GSA publishes a materially different schema or explicit documentation of record-level Reveal Date return semantics and historical-version retrieval. Do not build or dispatch a connector, do not repeat the failed route, and do not expand Wayback checks across all 348 keys. Keep Q221 blocked pending a source with timestamped transaction-level versions or a bounded archive whose transaction-row presence can be validated, alongside separately frozen transaction-class applicability and pre-event recipient-to-issuer mapping.

### 2.4 Cross-market annual-report information graph: a Q088 merge-or-kill lead

The 2026 preprint [CrossAlpha: An Annual-Report Benchmark for Cross-Market Factor Research](https://arxiv.org/html/2605.29286) describes a public benchmark with approximately 3,600 firms, 10,700 firm-year reports, five markets, and about 19 million directed firm-pair scores. Its reported results include stronger cross-market disclosure-derived peer prediction in the US-to-Japan setting than domestic-text, industry-code, and return-correlation baselines. These are the paper's claims, not a result reproduced by this project.

The method's most transferable components are:
- standardized business-exposure descriptions rather than raw whole-report similarity;
- removal of common boilerplate components (the paper uses PCA whitening);
- a directed economic-link graph rather than an undirected generic similarity matrix;
- explicit cross-market calendars/time zones and feasible execution delays;
- event-conditioned filtering as a distinct mechanism from static peer comomentum.

**Overlap decision:** this is close to Q088's existing textual peer/network/comomentum design and to broader cross-channel disclosure work. Do not create a separate candidate merely because the source market is foreign. If revisited after the active execution lock clears, evaluate it as a Q088 sub-design with an explicit foreign-source mechanism, and first verify free data/license, historical annual-report vintages, delisting coverage, stable issuer/security mapping, and feasible target-market prices.

**Cheap falsifiers to preregister before any return evaluation:**
1. Compare text-derived edges with industry, return-correlation, and randomized degree-preserving graph baselines.
2. Remove common schema/boilerplate components and test whether links remain stable.
3. Freeze source reports and graph edges strictly as known at each decision time; use source-market close and target-market tradability calendars.
4. Use source-shock timing placebos and shuffled source-target links.
5. Kill the extension if it does not add stable information beyond the existing Q088 mechanism or if public historical coverage/identity resolution fails.

No performance experiment, universe search, horizon search, threshold search, or ranking is authorized by this note.

### 2.5 Satellite/AIS/port activity: do not rediscover an existing line

The IMF working paper [Nowcasting Global Trade from Space](https://www.imf.org/-/media/files/publications/wp/2025/english/wpiea2025093-print-pdf.pdf) and the public [Watching Trade from Space repository](https://github.com/yonggeun-jung/watching_trade_public) support the feasibility of combining vessel movements, satellite SAR, nighttime lights, and port characteristics to measure maritime activity. The repository notes that satellite extraction requires Google Earth Engine access; therefore, public code does not by itself establish a fully self-contained, free historical data path.

The project has already captured port/satellite-vs-AIS divergence as a frontier idea in [PR #1257](https://github.com/DWR-debug/trading-agent-public/pull/1257). This pass adds no new candidate. Any future continuation should remain attached to that existing lineage and first prove historical observation dates, sensor-quality controls, geolocation/entity exposure, free access, and incremental information beyond ordinary trade/commodity data.

## 3. Research methodology: useful ideas, not automatic adoption

- Bailey et al., [The Probability of Backtest Overfitting](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253), propose CSCV/PBO as a way to estimate selection overfitting in investment backtests.
- Bailey and López de Prado, [The Deflated Sharpe Ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551), explicitly address multiple testing and non-normal returns.
- The 2026 preprint [When Alpha Disappears](https://arxiv.org/abs/2605.23959) proposes a one-convention-at-a-time benchmark for measuring decision-time leakage.
- The 2026 preprint [What survives honest evaluation?](https://arxiv.org/abs/2608.27734) studies search-aware evaluation of LLM-generated strategies.

These sources reinforce the existing rule: discovery volume is not scientific evidence, and a large number of agent-generated hypotheses must not silently become a large, untracked number of trials. However, no paper's proposed statistic or threshold should be imported into the project without a method review, sample-size assessment, and an explicit governance change through the correct channel. This note makes no such change.

## 4. Prioritized work queue

| Priority | Workpack | Runner/resource fit | Done condition | Stop rule |
|---|---|---|---|---|
| P0 | Repair scheduled Literature Frontier Scout bootstrap (PR #1441) | GitHub-hosted Ubuntu; then scheduled scout | CI/full-suite pass, merged fix, next scheduled run reaches query steps and uploads a receipt | Do not count failed scout runs as literature coverage |
| P1 | Q104:I19 frozen-source lineage follow-up | R5 completed on one additional frozen accession from existing 2015 Q1 vintage; next sample only if independently justified by immutable census/receipt | R5 receipt preserved; any further step needs a distinct frozen row/source pin and preregistered bounded route | No production precedence, census restart, receipt repair, or performance use |
| P1 | Q220 offline source-vintage lineage reconciliation | Windows C + independent Linux analysis | Reproducible explanation of expected-hash provenance, or explicit unresolved lineage receipt | No source downloads, hash edits, or forced rerun |
| P1 | Q221 official contract/OpenAPI desk audit | Frontier lane; public docs only | Documented transaction-level timestamp and version-lineage semantics, or a precise no-go record | No API key/API call, identical route retry, or 348-key expansion |
| P2, parked | Cross-market disclosure graph sub-design under Q088 | Design/review only; no runner dispatch under current lock | Non-overlap decision, free-source/license/PIT feasibility and fixed cheap falsifiers | Merge into Q088 or kill; no new candidate ID |
| P2, parked | PortWatch/SAR/AIS evidence audit under existing port frontier | Design/review only; no duplicate discovery run | Verify access/licensing, historical vintage, and exact issuer/port exposure | Do not reopen as a duplicate candidate |

## 5. Orchestration notes

- The persistent research contract and two-lane model remain authoritative: Formal Readiness works on active gates; Frontier Discovery performs orthogonal source/PIT feasibility and cheap falsification; the third Windows slot is for long deterministic work or independent reproduction only when it is not duplicating A/B.
- The Literature Frontier Scout is scheduled every six hours. Its latest verified run failed before discovery; therefore, do not claim that the recurring scout is currently delivering results until a successful post-fix receipt exists.
- Q104 R5 was dispatched only after the exact frozen accession, archive pins, byte caps and three-route contract were preregistered and CI/full-suite passed. R5 completed with a pinned receipt; do not repeat this accession. No additional runner is justified until a different frozen row/source pin provides new information.
- All proposed work preserves the active execution lock Q104:I19 + Q220 + Q221. Other families remain design-only/parked unless the canonical registry and a fresh status check explicitly change that lock.

## 6. Source list

1. SEC, [Webmaster FAQ — EDGAR availability lag](https://www.sec.gov/about/webmaster-frequently-asked-questions).
2. GSA, [SAM.gov Contract Awards API](https://open.gsa.gov/api/contract-awards/).
3. Wang et al., [CrossAlpha (arXiv:2605.29286)](https://arxiv.org/html/2605.29286); code/data landing page: [4open.science](https://4open.science/r/crossalpha-7346/).
4. IMF, [Nowcasting Global Trade from Space, WP/25/93](https://www.imf.org/-/media/files/publications/wp/2025/english/wpiea2025093-print-pdf.pdf); [public code repository](https://github.com/yonggeun-jung/watching_trade_public).
5. Bailey et al., [The Probability of Backtest Overfitting](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253).
6. Bailey & López de Prado, [The Deflated Sharpe Ratio](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551).
7. Zhang et al., [When Alpha Disappears](https://arxiv.org/abs/2605.23959), 2026 preprint.
8. Gençay, [What survives honest evaluation?](https://arxiv.org/abs/2608.27734), 2026 preprint.
9. Project evidence: [Q220 HTTP representation design](https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q220_HTTP_REPRESENTATION_SENSITIVITY_2026-10-13.md), [Q220 run #38568650121](https://github.com/DWR-debug/trading-agent-public/actions/runs/38568650121), [successful Literature Frontier Scout #38571272581](https://github.com/DWR-debug/trading-agent-public/actions/runs/38571272581), [Q104 R4 2017 Q2 source-lineage run #38574180245](https://github.com/DWR-debug/trading-agent-public/actions/runs/38574180245), [Q104 R5 2015 Q1 frozen-accession diagnostic #38582684174](https://github.com/DWR-debug/trading-agent-public/actions/runs/38582684174), [existing port frontier PR #1257](https://github.com/DWR-debug/trading-agent-public/pull/1257).

**Decision:** preserve the three active candidates and their hard gates; the recurring literature scout has a verified successful receipt; Q104 R4 and R5 are bounded diagnostics and do not alter the immutable 14-row aggregate or resolve filing-date precedence; keep Q220 offline and Q221 documentation-only until their source contracts materially improve.
