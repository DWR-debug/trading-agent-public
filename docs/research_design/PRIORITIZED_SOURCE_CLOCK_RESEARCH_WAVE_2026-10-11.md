# Prioritized source-clock research wave: Q221 disposition, Q224 and Q228 preflight

**Date:** 2026-10-11 UTC  
**Source baseline:** merge commit 22ab0e28913b717d638302837b2b912d1833225b; latest verified master during preparation includes subsequent ops status-sync commit e22921a829ddfa2ab71489dc44002f80cff9e0d8  
**Classification:** research operations / source feasibility / no performance authorization  
**Purpose:** preserve the Q221 archive inventory result and sequence the next highest-information source/PIT checks without changing candidate contracts, dispatch allow-lists or scientific gates.

## Executive decision

1. **Q221 is not cleared and must not be retried against the same monthly-listing endpoint without a new, independently justified source hypothesis.** The user-started run completed the bounded catalog request and uploaded a receipt, then failed closed because it did not find a dated version series. This is a valid negative feasibility result, not proof that historical snapshots do not exist elsewhere.
2. **Keep Q104:I19 and Q220 ahead of reserve exploration.** Q104's historical census remains in progress, with some shards failing at acceptance-time joins and other shards still running. Q220's 55-record population subgate succeeded, but its route probe remains pending. Neither full run is terminal; do not duplicate either.
3. **Rank Q224 first among reserve source-feasibility preflights, Q228 second.** Q224 has a distinct observable—post-publication EDGAR document acquisition—and a focused modern log archive with a known gap. Q228 observes a distinct regulatory scrutiny/response state, but first needs deterministic review-cycle linkage and strict separation between latent review time and the public correspondence filing time.
4. **Q224 and Q228 remain reserve preflight work only.** This prioritization does not activate candidates, expand the active dispatch allow-list, authorize market-outcome tests, or replace Q104:I19, Q220 or Q221.
5. **Q218 remains excluded** from active execution, candidate dispatch and successor selection. Q227 and Q231 remain one conceptual SEC FOIA family pending a proof of orthogonality; no duplicated parallel wave is justified.

## 1. Q221 archive inventory: verified disposition

### Run and durable receipt

- Workflow run: https://github.com/DWR-debug/trading-agent-public/actions/runs/38161449892
- Run ID: 38161449892; dispatched commit: 99ece057f143582710b8ecce1dd050a5f6b74185
- Result: workflow conclusion **failure**, by design at the final fail-closed step after a receipt was uploaded.
- Artifact ID: 11710356527; artifact digest reported by GitHub: sha256:dad1cc8396e75df1482a32f01380dfecc3a048158e299a1ab1d0fe955351fb45
- Receipt path proposed for permanent evidence: research/evidence/q221_monthly_archive_inventory_run_38161449892.json
- Receipt status: ARCHIVE_LISTING_OK_NO_VERSION_SERIES_FOUND
- Receipt fingerprint: 78e8bca54e70724c44d0c32bf092cde60d7c02cda59838de37f766fe4115be7e
- Canonical receipt JSON SHA-256: 9c25069d7f1fe2b09e96f5fe5376ddf93e3539f868c195d81be00dccb8945872
- Fixed input manifest SHA-256: e1f04145d19e032b435e283b171e79f9f569d97b0ee903d58bae25ba889c185a

The probe parsed 14 catalog rows across fiscal-year requests for FY2019–FY2025: seven fiscal-year Full-file rows and the same all-fiscal-year Delta file repeated in each of the seven responses. The seven Full files all carry the current generation date 2026-09-06; the repeated Delta file carries 2026-09-24. The receipt records no dated version series.

The important distinction is that **14 response rows are not 14 independent archive vintages**. The returned catalog describes current available archive versions; it did not produce a chain of successive historical snapshots for the same fiscal-year data. The receipt also marks transaction presence/absence tests, historical first-public-observation, event-level public boundary, historical applicability and recipient-to-issuer mapping as unproven/false. It is source-feasibility evidence only, not scientific evidence.

### What the result does and does not mean

**Established:** the bounded read-only catalog calls completed successfully, produced parseable catalog responses and did not find the required historical version series.

**Not established:** that old archive payloads never existed, that the underlying FPDS or agency systems lack revision history, that an award was or was not public at a historical date, or that a transaction's Action Date / Last Modified Date equals its first public-observation time.

USAspending's official Award Data Archive page says Full files contain fiscal-year data through the file's preparation date and Delta files contain changes since the previous month's generated files. Its analyst guide describes the ordinary procurement reporting path and a separate 90-day delay for DoD and U.S. Army Corps of Engineers (USACE) data. These are important source-system timing rules, but they are not transaction-specific historical first-public timestamps and do not override the candidate's agency/transaction exception checks.

Sources:
- USAspending, Award Data Archive: https://www.usaspending.gov/download_center/award_data_archive
- USAspending, Analyst's Guide to Federal Spending Data: https://www.usaspending.gov/federal-spending-guide
- USAspending API endpoint index: https://api.usaspending.gov/docs/endpoints
- USAspending API transaction-history contract: https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/transactions.md

### Q221 next gate: alternate-source desk check, not a duplicate probe

The next work is a **bounded research question**, not an automatic new workflow dispatch:

1. Establish whether official release notes, a retained versioned download source, a database snapshot series, or a documented historical source endpoint exposes successive dated versions for the *fixed frozen transaction keys*.
2. For each plausible route, record exact source owner, retrieval mechanism, date/version semantics, retention coverage, immutable content hash and whether it can prove a transaction was present/absent at a historical public boundary.
3. Treat web-archive captures as discovery leads only unless the captured object and capture timestamp can be tied to a reproducible original source response. A page capture or filename date alone is not event-level proof.
4. Stop if the only fields available are Action Date, Issued Date, Last Modified Date, the current transaction API, or a current archive listing. Do not turn them into a first-public timestamp by assumption.
5. Only if an alternate source gives an identifiable, immutable historical vintage should engineering resume: freeze the access contract, test fixed-key presence and absence against vintage cutoffs, preserve correction/delete semantics, then address agency exceptions and recipient-to-issuer mapping. Keep all later PIT and scientific gates closed until their own receipts are positive.

No second Q221 run was dispatched. The exact endpoint just tested should not be repeated without a change that is expected to yield new evidence.

### Official SAM.gov alternative: useful lead, not a first-public clock

The official [GSA/SAM.gov Contract Awards API documentation](https://open.gsa.gov/api/contract-awards/) provides a specific alternate source worth examining before closing the procurement-data family:

- The documented `publicDeltaDate` parameter filters contracts using **Last Modified Date or Reveal Date**. It is therefore a retrieval filter over two possible clocks, not an explicit statement that the returned value is an event-level first-public timestamp.
- The response schema documents `createdDate`, `lastModifiedDate` and `approvedDate` in transaction data. None should be substituted for a historical first-public-observation boundary without field-specific, transaction-level evidence.
- The API requires a SAM.gov API key for revealed data. Unrevealed data is permission-restricted to DoD-assigned users; it is not an anonymously available general-purpose history source.
- The documented 90-day DoD reveal rule describes a policy for whether records are revealed. It does not, by itself, prove the exact public-appearance timestamp for a particular transaction or that earlier public versions can be reconstructed.
- No API key was provided or used, and no live SAM.gov API request was made in this preflight.

**Next bounded Q221 desk check:** inspect the official OpenAPI/response contract and any publicly accessible examples or source documentation to establish whether Reveal Date is returned at transaction level, what exactly it represents, whether old versions can be queried/retrieved, and how deletion/correction lineage is represented. Do not build a connector or dispatch a new probe until the field/version semantics and access mode are concrete. A successful query that returns a contract based on `publicDeltaDate` is not enough unless it also supplies a reproducible record-level public clock and a historical vintage/presence-absence proof. The FPDS “Date/Time Stamp Accepted” field is a separate possible diagnostic, but acceptance by FPDS is not automatically publication to the public.

Official source references:
- [SAM.gov Contract Awards API](https://open.gsa.gov/api/contract-awards/)
- [USAspending monthly-file API contract](https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/bulk_download/list_monthly_files.md)
- [FPDS Data Element Dictionary](https://dodprocurementtoolbox.com/uploads/FPDS_Data_Dictionary_V15_OT_17a47e9af5.pdf)

Q221 remains source-blocked until the alternate route provides a versioned, immutable and transaction-specific history capable of testing both presence and absence at historical cutoffs.

## 2. Active lanes: operate the existing work, not duplicate it

| Lane | Latest verified state | Next action |
|---|---|---|
| Q104:I19 | Run 38168441086 remains active; source snapshot and recovery guard passed, and all six shards were still running at 21:55 UTC. | Let the existing census reach terminal state. Reconcile all six shard receipts; repair only proven header/identity gaps; do not restart the entire census. |
| Q220 | Population, historical-prefix compiler and independent retrieval/parser receipts now validate as one pinned 55-record chain with zero hash, identity, prefix, structured-fact, TextBlock or change-state mismatches. Five no-TextBlock states remain explicit. | Freeze a bounded adversarial robustness + formal trial-governance reconciliation workpack. No performance authorization, ETA or automatic dispatch until the workpack is explicit. |
| Q221 | Five fixed-window historical policy-document vintages have been reconstructed, but award-level first-public observation and historical applicability remain unproven. | Define a new award-level boundary and recipient-to-issuer workpack with fixed transaction classes, DoD/USACE/FAR semantics and correction lineage. No reuse of the completed policy-vintage probe as transaction proof. |

## 3. Reserve wave A — Q224 EDGAR document-acquisition demand

### Why first

Q224's object is observed filing-acquisition activity strictly **after** an issuer's frozen SEC filing public boundary. That is distinct from filing text/complexity (Q217/Q220), generic attention, release latency (Q204), and institutional ownership/demand (Q104). The current fixed candidate contract already specifies a modern-schema feasibility gate and relevant falsifiers; this wave must implement that contract, not invent a new one.

The primary literature supplies a construct rationale, not transferable evidence for this project. Li and Sun (2022), using the earlier January 2003–December 2014 EDGAR log sample, report that abnormal counts of IP addresses searching company filings are associated with subsequent returns and fundamentals. The published sample does not cover Q224's modern 2020–2025 archive window, and the reported portfolio result is not validation of the current candidate or a performance authorization.

- Li and Sun (2022), *Information acquisition and expected returns: Evidence from EDGAR search traffic*, Journal of Economic Dynamics and Control 141, 104384: https://doi.org/10.1016/j.jedc.2022.104384
- Author/publication record: https://research.polyu.edu.hk/en/publications/information-acquisition-and-expected-returns-evidence-from-edgar-

### Fixed source boundary

The SEC's official log-data page lists two distinct availability ranges: January 1, 2003–June 30, 2017, and May 19, 2020–June 30, 2025. It explicitly says log data for July 1, 2017–May 18, 2020 are no longer available. The legacy and modern datasets also have schema and quality differences, and the SEC warns that lost/damaged files mean the assembled data may not capture all traffic.

For this preflight, use only the explicitly documented modern range **2020-05-19 through 2025-06-30**. Do not silently splice across the 2017–2020 gap or join the older schema into the modern one.

Official source: https://www.sec.gov/data-research/sec-markets-data/edgar-log-file-data-sets

### Existing Q224 source-gate receipt: useful but deliberately incomplete

The repository already ran the fixed-control gate on 2026-10-11:

- Run: https://github.com/DWR-debug/trading-agent-public/actions/runs/38160521620
- Status: SOURCE_ARCHIVE_INTEGRITY_COMPLETED_NO_PERFORMANCE
- Receipt fingerprint: 0aa0c2ecd38f2f39d0cf4cbf8d391d0e08a1eb38631424b004499c6404e20865
- Latest evidence path on master: research/evidence/q224_edgar_modern_source_gate_latest.json

All three fixed controls returned HTTP 200, were valid ZIPs and included both request-time and URI columns. The probe read at most 250 rows from each archive; request-time parsing was 100% for the 25 retained sample rows. The URI pattern matched 215/250 rows (0.860) for 2020-05-19, 193/250 (0.772) for 2022-12-30, and 226/250 (0.904) for 2025-06-30. Download sizes were 3,887,187 bytes, 294,991,286 bytes and 1,159,445,743 bytes respectively. Thus the late-window archive is large; scale-out must be bounded and avoid redundant full downloads.

The check also established two important blockers:

- The request-time column changes from _time in the 2020 control to time in the 2022 and 2025 controls. A deterministic alias normalizer is required.
- The modern schema exposes only time and uri_path in these controls; legacy crawler/IP/status fields are absent. The receipt explicitly says traffic contamination is not fully resolvable from this schema. The filing acceptance/public-boundary join is not complete, and same-session use remains false.

So this success is **a three-date archive-integrity smoke test**, not evidence that every daily file in the declared window exists, not a full traffic-quality solution, and not a positive historical PIT gate.

### Ordered gate sequence

**Q224-A — archive and schema census**
- Build an inventory from the SEC's actual published object/listing conventions for the entire modern range; distinguish observed missing objects from weekends, holidays or undocumented naming exceptions rather than assuming every calendar date has a file. Record URL, date/period, byte size, ETag and SHA-256 for each observed object.
- Record missing months, unexpected schema/header changes, failed downloads, damaged files and SEC-documented traffic limitations.
- Do not call the archive complete merely because all currently linked files downloaded.
- Emit a machine-readable receipt with exact ranges, source URLs, counts, gaps, header variants and hashes.

**Q224-B — deterministic timestamp and filing identity**
- Resolve timestamp units/time zone from source documentation and observed schema; reject ambiguous timestamps.
- Map the log's CIK/accession or URI path to a frozen filing identity deterministically.
- Join to the exact SEC filing acceptance/public boundary and ensure counted requests occur strictly after that boundary.
- Preserve failed/unmapped rows and exclusion reasons; no fuzzy issuer assignment or manual outcome-aware patching.

**Q224-C — measurement and non-interference tests**
- Report human/automated/bulk traffic controls and the distribution of repeat requests, including artifact patterns caused by repeated interactive XBRL/filing-page visits.
- Apply future-row mutation invariance: adding or altering log rows after a cutoff must not change the closed historical prefix.
- Test cutoff-edge timezone/session handling and ensure that filing-day traffic is not assigned before its public boundary.
- Compare raw-source totals with filtered totals so exclusion rules cannot silently create coverage.

**Stop conditions**
- If archive completeness or damaged-file scope cannot be established, stop with source coverage unresolved.
- If timestamps or accession mapping are ambiguous, stop rather than infer.
- If traffic quality cannot be bounded deterministically, do not interpret counts as investor demand.
- Do not run market outcome tests, select windows/horizons, tune thresholds or promote the candidate in this wave.

### Additional confound from the literature

Li and Sun's approach requires explicit filtering for robots/crawlers and excessive IP activity. A separate 2026 article, Lee, *Observable Versus Unobservable Information Acquisition* (Accounting & Finance), studies the change in observability of SEC search behavior and reports that some investors reduce information acquisition when they expect that behavior to be observable. Thus observed log volume is an **observable trace**, not a monotone measure of latent information demand; changes in observability regime may alter the measurement itself.

- Lee (2026), *Observable Versus Unobservable Information Acquisition*: https://doi.org/10.1111/acfi.70275

This adds a source-regime diagnostic; it does not create a new feature or relax any predeclared gate.

## 4. Reserve wave B — Q228 SEC filing-review dialogue

### Distinct object

Q228 observes public regulatory scrutiny and issuer response: official comment letters, response correspondence, successive rounds, amendments and an unresolved/closed review state. It should not collapse to filing complexity, generic latency, enforcement, mandatory-versus-voluntary disclosure, or raw comment counts disconnected from a review cycle.

The SEC states that filing-review correspondence has been publicly released through EDGAR since 2005. Its 2011 announcement says that, beginning January 1, 2012, correspondence would be released no earlier than 20 business days after completion of review; the earlier stated target was no earlier than 45 days. These policy statements concern the relation between the latent review process and public release; they do **not** justify backdating the observable to a review start or assumed review-completion date.

- SEC, Comment Letters FAQ: https://www.sec.gov/answers/commentletters.htm
- SEC, release-timing announcement (2011): https://www.sec.gov/newsroom/whats-new/divisionscorpfincfannouncementsedgarcorrespondence
- Johnston (2017), *Regulatory Oversight of Financial Reporting: Securities and Exchange Commission Comment Letters*, Contemporary Accounting Research: https://doi.org/10.1111/1911-3846.12297
- Bozanic, Dietrich and Johnson (2017), *SEC Comment Letters and Firm Disclosure*: https://doi.org/10.1016/j.jaccpubpol.2017.07.004

The cited studies support the importance of SEC scrutiny and its potential effect on disclosure/information environment. They do not establish a short-horizon return effect from the first public correspondence filing.

### Existing Q228 implementation: current source-page check only

The repository defines workflow .github/workflows/q228-sec-correspondence-source-gate.yml and automation/q228_sec_correspondence_source_gate.py. The script currently fetches two present-day SEC pages (correspondence guidance and EDGAR search), hashes each response and checks for a small set of text markers. That is a current-page structure check; by construction it does not census historical letters, link comment/response cycles, prove each record's first public timestamp, or validate an issuer-level PIT join.

### Verified Q228 run 38165018398: technical success, source gate incomplete

The master-push run [38165018398](https://github.com/DWR-debug/trading-agent-public/actions/runs/38165018398) completed its source script and all four Q228 unit tests. The downloadable [workflow artifact](https://github.com/DWR-debug/trading-agent-public/actions/runs/38165018398/artifacts/11711498525) has ZIP digest `sha256:e7d1ec70bbbe3e9003b674dfc3dc5716507c8fcfc3504b7884850cd2f3191892`. The receipt is preserved as [q228_sec_correspondence_source_gate_run_38165018398.json](../../research/evidence/q228_sec_correspondence_source_gate_run_38165018398.json) with fingerprint `ea37489023cdef279c00495eeee93b814027519988d9ef284066886fb5b0d28c`.

The receipt status is **SOURCE_STRUCTURE_INCOMPLETE**:
- The correspondence guidance page was HTTP 200 and all configured markers were found.
- The EDGAR search page was HTTP 200, but the response consumed by the workflow did not contain the exact `Filing review correspondence` marker. It recorded 30,813 bytes and SHA-256 `2f031e75c5a1186f95111950d51b5ef35e6846df6f4663d589421061327eb4f3`.
- A separate live raw-HTML fetch performed during follow-up did include the filing-category dropdown entry with that exact label (including CORRESP/DOSLTR/DRSLTR/UPLOAD codes), and the response was materially larger than the workflow-captured body. The reason for this response variance is **not established**; do not assume missing functionality, a transient challenge, or a permanent SEC page change based on one response.

The distinction matters: the GitHub Actions job's conclusion was success because the bounded script wrote an explicit incomplete receipt and returned normally. The *source gate* did not pass. All PIT and scientific-authority booleans remain false. The next step is a low-volume, bounded response diagnostic (status, content type, final URL if exposed, title/H1, a short marker context, size and hash; protect against logging unbounded page contents), then a focused decision whether the current marker is stable and semantically appropriate. Keep the gate incomplete until that is resolved. Do not weaken the marker to generic navigation text. Only after response/source structure is reproducible should work proceed to historical correspondence census, deterministic review-cycle links, public filing clock, amendments/closure lineage and independent PIT mutation tests.

### Ordered gate sequence

**Q228-A — historical archive census**
- Establish correspondence coverage from the officially documented start and identify every source/form class and period.
- Preserve raw accession, acceptance timestamp, filing/form type, document URLs, issuer CIK and original bytes/hash.
- Keep SEC-originated comment-letter provenance distinct from registrant CORRESP responses (and preserve any original UPLOAD/type metadata rather than flattening all correspondence into one class).

**Q228-B — deterministic review-cycle linkage**
- Link comment letters, filer responses, subsequent comment rounds and amendments using predeclared identifiers/rules.
- Measure the ambiguous/unmatched rate and retain ambiguous cases as exclusions; do not hand-map firms based on outcomes.
- Keep latent review start/completion and response delays as metadata unless those timestamps are independently documented and available historically.

**Q228-C — admissible public clock and mutation test**
- Use the public EDGAR acceptance/publication boundary of the correspondence filing itself; if exact intraday admissibility is not proven, use the next regular session under the frozen rule.
- Future correspondence, later responses, review closure and later amendments must not rewrite an earlier public prefix.
- Test deterministic topic taxonomy only after source identity/linkage is stable; preserve a null/unclassified state rather than reassigning topics after seeing results.

**Stop conditions**
- Stop if public correspondence coverage or historical form semantics are not reproducible.
- Stop if review-cycle links require hindsight or issuer names without frozen identifiers.
- Stop if latent review dates are being used as a proxy for the public filing timestamp.
- No performance, tuning, holdout selection, trading ranking or promotion in this preflight.

## 5. Orchestration and governance boundary

- Use the current GitHub repository as the source of truth and preserve all evidence through a reviewable branch/PR.
- Keep Q104:I19, Q220 and Q221 as the current active focus. Q224 and Q228 are reserve source-feasibility priorities only.
- Do not duplicate running jobs merely to consume capacity; do not enqueue artificial work.
- Share deterministic source/identity/timestamp infrastructure where appropriate, but do not infer that shared infrastructure makes hypotheses economically equivalent.
- The Q227/Q231 FOIA family should be consolidated before compute; Q218 remains excluded.
- Literature searches, model output and data-availability receipts are not return evidence. Strategy-success probabilities remain “Nicht schätzbar” without the required preregistration, valid PIT, independent out-of-sample testing, realistic costs, robustness and independent reproduction.

Safety and authority remain unchanged: PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; ORDERS_ENABLED=False; AUTOMATIC_PROMOTION=False. No dispatch, promotion, order, live execution or scientific gate is authorized by this document.



## 6. Incremental source-provenance findings — 2026-10-11

**Classification:** bounded data-quality and orchestration delta only. The [project-wide synthesis](PROJECT_WIDE_RESEARCH_SYNTHESIS_2026-10-11.md) already defines the general multi-clock/vintage principle; the [Q121 timing memo](Q121_SEC_BENEFICIAL_OWNERSHIP_TIMING_2026-10-03.md) already covers the 5:30 p.m. EDGAR rule and the distinction between acceptance and exact public availability; Q221's existing sections above already document the USAspending archive-vintage failure. This section records only the additional implementation-level findings.

### 6.1 SEC 13F bulk-extract vintage versus accession-level filing

The SEC's official [Form 13F Data Sets page](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets) records that the March 12, 2024 refresh reformatted the quarterly sets and applied processing fixes, including missing information-table records. The [Form 13F readme](https://www.sec.gov/files/form_13f_readme.pdf) says the data are “as filed” but warns of inconsistencies versus earlier submissions and other publication formats; accession number is the submission key and amendments remain separate.

This is **not evidence that any current Q104 row is wrong**. The incremental risk is that a quarterly ZIP is a derived extraction vintage, not the original accession document. A later extraction fix may change a bulk package without changing what was publicly present in the original filing. Keep accession-level content and each bulk package's generation/version/hash separate; do not infer a later public date from a later extraction refresh.

After run [38168441086](https://github.com/DWR-debug/trading-agent-public/actions/runs/38168441086) is terminal and the existing six-shard/header reconciliation is complete, run a fixed, outcome-blind QA sample across predeclared early-, middle- and modern-format strata. Compare frozen target CUSIP/issuer/class rows in the bulk extract to the exact accession's official information-table document. Preserve source URLs, hashes, parser version, missingness and mismatches. This bounded sample is not proof of whole-archive completeness and does not replace or relax the frozen PIT gates.

### 6.2 Evidence Bus v2 correction — implemented

The gap identified during this audit was closed by [PR #1325](https://github.com/DWR-debug/trading-agent-public/pull/1325), merged at 2026-10-11 21:18:35 UTC. Current `master` recomputes the canonical receipt digest (excluding only `receipt_fingerprint`) and fails closed on payload mutation. Opt-in schema v2 adds `availability_basis`, `availability_evidence_url`, `vintage_id` and `revision_parent_fingerprint`; a claimed non-null availability time requires HTTPS evidence, while unknown availability must remain explicitly `UNKNOWN`. Schema-v1 shape remains compatible and existing receipts are not rewritten.

The production caller inventory confirmed that `research_os_source_probe.py` is the only production caller of `build_receipt`; it remains on v1 because HTTP reachability does not establish the historical first-public time of a dataset. This is intentional rather than an unresolved defect. Future source-specific producers should opt into v2 only when they have evidence for the chosen clock; no availability time may be imputed from event/action time or retrieval time.

### 6.3 Verified dashboard freshness race

The dashboard was deployed successfully from master 59f231db…, after which the status synchronizer published 62759435…. The live dashboard snapshot consequently lagged the then-current master. This PR adds a workflow_run completed trigger for the **Current Operational Status Synchronizer**, restricted to its master run, plus a regression test so the dashboard refresh follows the generated status snapshot rather than racing it.

The unusual-source ideas in [PR #1257](https://github.com/DWR-debug/trading-agent-public/pull/1257) (port satellite/AIS, exact-version CISA KEV × NVD CPE, official FDA state transitions), as well as Q202/Q203, already exist in the project and are not new candidates or a reason to widen automatic dispatch.

### 6.4 New 2026 PIT literature: versioned values *and* versioned representations

Three recent papers sharpen the methodological basis for the existing source-clock work. They are preprints/working papers, not a substitute for independent evidence on any Trading Agent candidate:

- **Wang (2026), “Point-In-Time Data Integrity in Quantitative Equity Research”** ([SSRN 7183438](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7183438), posted August 6, 2026). The paper distinguishes period-end/latest-value, filing-date/latest-value, acceptance-time/original-value and tradable-time/original-value information sets; its bounded pilot reports that period-end activation with later-revised values inflated measured CAPM alpha relative to a strict tradable-time/original-value set in the studied large-cap sample. This supports keeping the original observation and its availability/version lineage together. It does not estimate a correction to Q104, Q220 or Q221.
- **Lyle, Siano and Yohn (2026 revision), “Re-Adjusted Financial Statement Data: Challenges and Implications for Empirical Research”** ([SSRN 5107985](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5107985), revised February 16, 2026). Using Compustat Snapshot, the authors report frequent retrospective value changes and materially different inferences for a substantial portion of 35 accounting anomalies across data vintages. The data vendor and anomaly universe differ from this project; transfer the *version-control requirement*, not the reported effect sizes.
- **Chen et al. (2026), “Does Training on Future Data Pay? Look-Ahead Bias in Forecasting with Pretrained Models”** ([arXiv:2609.20554](https://arxiv.org/abs/2609.20554), posted September 17, 2026). The authors compare annual model vintages with origin-aligned PIT forecasts and report that later model vintages often changed forecasts even when numerical input histories were held fixed. This is a preprint, not evidence for model alpha. It motivates an additional boundary if learned representations ever become strategy inputs: the **model/checkpoint and its training-corpus cutoff** must be versioned alongside the data.

**Incremental engineering implication:** PIT applies to the whole transformation chain, not just source rows. For each historical observation that enters a formal compiler, retain the source/accession or transaction identity, source-vintage/hash, parser or transformation version, admissible public-time basis, and revision/parent lineage. If a future candidate uses model-generated features, record the exact model/version and historical training cutoff or fail closed; keep today's AI-worker outputs as design/review input only. The Research OS Evidence Bus v2 now supplies optional fields for source availability basis, evidence URL, vintage and revision parent, but its reachability probe correctly does not claim those clocks.

**Bounded use in the current active three only:**
- **Q104:I19:** after run [38168441086](https://github.com/DWR-debug/trading-agent-public/actions/runs/38168441086) is terminal and the six receipts reconcile, compare a fixed, outcome-blind sample of selected bulk-extract rows with the exact accession-level information table and preserve both hashes. The SEC explicitly says its quarterly extracts are not substitutes for the underlying filings and notes that the March 2024 refresh included fixes for missing information-table records ([official SEC page](https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets)).
- **Q220:** preserve each as-filed document and the frozen XBRL/TextBlock/presentation mapping as distinct versioned inputs; later amended/restated values must not overwrite the earlier observable prefix.
- **Q221:** keep policy-document vintages distinct from transaction vintages. The existing positive five-window USAspending policy-PDF receipt is not award-level timestamp, transaction-presence or issuer-mapping proof; the next workpack still needs those exact transaction-level boundaries.

No candidate is added, no active-focus lock is widened, and no performance, holdout, ranking, tuning, promotion, paid-service or live-execution gate changes.

### Operational disposition

- Active focus remains **Q104:I19, Q220 and Q221**; Q218 stays excluded from automatic dispatch.
- Do not duplicate Q104. After it is terminal, reconcile the six receipts, apply the existing targeted .hdr.sgml recovery, then perform only the bounded source-consistency QA before the existing PIT compiler.
- Q220's frozen 55-record population, historical-prefix compiler and independent PIT reproduction are now positive and receipt-linked; the next gate is a bounded adversarial robustness review plus formal trial-governance reconciliation, with no performance authorization. Q221 remains source-blocked at the award-level public-observation boundary until a separate transaction-level workpack proves historical presence/absence and correction lineage.
- No candidate contract, performance gate, holdout rule, ranking, tuning, promotion, paid service or live-execution boundary is changed.


## 7. Unusual-source lead: Government Patent Register (reserve only)

The NBER working paper [*The Government Patent Register: A New Resource for Measuring U.S. Government-Funded Patenting*](https://www.nber.org/papers/w32136) by Daniel P. Gross and Bhaven N. Sampat describes a historical register of U.S. government rights in patents. The published version appeared in *Research Policy* in 2025 ([journal record](https://www.sciencedirect.com/science/article/abs/pii/S0048733324001914)). Its useful distinction is between government-title patents and government-funded inventions licensed to private organizations; some license relationships cannot reliably be recovered from patent-text acknowledgements alone.

**Potential connection to the existing Q221 mechanism:** as a later, independent entity/capability cross-check, patent-level government-rights evidence could help distinguish recipients that perform technical work from recipients that hold or license inventions, and might support post-award capability outcome audits. This is a lead to screen against Q221's already frozen mechanism—not a new candidate and not a replacement for the award-level public-clock gate.

**PIT restriction:** the consolidated register was compiled retrospectively. Its current appearance in a register cannot be treated as contemporaneous public information at a historical award cutoff. Any future use must locate the exact patent record and use its own original publication/grant/publication-vintage evidence, while separately verifying the availability of the government-rights/licensing field. Do not infer award causality or transaction timing from the current register alone.

**Disposition:** reserve for a later Q221 identity/capability workpack only after the award-level source clock, fixed transaction classes and recipient-to-issuer map have a defensible contract. Active focus stays Q104:I19, Q220 and Q221; no candidate expansion or dispatch is authorized by this source lead.


## 8. FDA recall lifecycle clocks: firm notice, FDA visibility, classification and revisions (reserve only) — 2026-10-12

**Classification:** source-clock / data-feasibility lead for the already documented official FDA state-transition frontier. This is not a new candidate, not scientific evidence, and does not change the active execution focus.

The official [FDA Enforcement Report API Definitions](https://www.fda.gov/safety/enforcement-reports/enforcement-report-api-definitions) expose several distinct dates with different semantics:

- `recallinitiationdt`: when the firm first began notifying the public or its consignees;
- `postedinternetdt`: when the recall was first posted to the FDA Enforcement Report (the FDA documents that this can be blank for older recalls before 2022-10-25);
- `pressreleaseissuedt`: a press-release publication date;
- `centerclassificationdt`: when FDA assigned the recall's Class I/II/III risk classification;
- `enforcementreportdt`: issuance date of the weekly report;
- `eventlmd`: when the recall event was last posted/modified; history endpoints use it for the date a new field value was posted.

FDA's [Enforcement Report History Feature](https://www.fda.gov/safety/enforcement-reports/enforcement-report-history-feature) states that field-change history for product description, recall reason, classification and code information is tracked for recalls posted or updated from 2018-07-24 onward. FDA's [general Enforcement Reports guidance](https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts/enforcement-reports) also warns that firms often make voluntary public statements before FDA completes hazard assessment and classifies the recall. Thus FDA classification time is not a proxy for the earliest public warning, and a latest-state API row is not by itself a historical first-public observation.

**Why this may matter:** this provides a clean *state-transition decomposition* for a future reserve source-feasibility audit: (1) firm/public initiation, (2) first observed FDA report posting, (3) FDA classification, and (4) later corrections. Those clocks might support research into regulatory information processing only if each field can be pinned to a contemporaneously available source vintage. They must not be substituted for one another or used to infer an equity-return effect from recall severity alone.

**Bounded reserve-only checks, if the existing FDA frontier is later selected:** use a fixed outcome-blind sample stratified by pre/post-2022-10-25 and pre/post-2018-07-24 coverage; verify missingness and semantics of `postedinternetdt`, link field history through event/recall identifiers, compare API values with archived weekly report or dated press release where available, and preserve raw response, retrieval timestamp, response hash and parser version. Treat `eventlmd` as a revision clock, not necessarily the first public clock. The historical field-history cutoff is a documented coverage bound, not proof that every earlier public statement can be reconstructed. A latest/current record without dated public evidence must remain UNKNOWN for PIT purposes.

**Disposition:** reserve only. Active focus stays **Q104:I19, Q220, Q221**. Do not enqueue FDA work, create an additional candidate, or assign a runner from this source lead. No change to PAPER_ONLY, performance, holdout, ranking, tuning, promotion or live-execution gates.
