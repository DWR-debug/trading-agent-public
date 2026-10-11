# Prioritized source-clock research wave: Q221 disposition, Q224 and Q228 preflight

**Date:** 2026-10-11 UTC  
**Repository basis:** master commit 22ab0e28913b717d638302837b2b912d1833225b  
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

## 2. Active lanes: operate the existing work, not duplicate it

| Lane | Latest verified state | Next action |
|---|---|---|
| Q104:I19 | Run 38145062319 is still in progress. Some historical census shards have failed at SEC acceptance-time joins; other shards were still running; source snapshot completed. | Let the existing census reach terminal state. Reconcile every shard receipt. Repair only the exact frozen accessions/joins shown to be missing; do not restart the entire census. |
| Q220 | Run 38155914188 is pending overall. Its population job succeeded: 55/55 records, zero record failures, eight-issuer frozen universe. Route probe remains pending. | Wait for route probe and reconcile population receipt provenance with gate-code/contract hashes. Do not start a duplicate run or declare the downstream PIT gate positive. |
| Q221 | Archive catalog stage completed, but historical multi-version series not found; fail-closed status is correct. | Bounded alternate-source research as described above. No event-level public boundary, frozen recipient/issuer map or scientific evidence is claimed. |

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

### Ordered gate sequence

**Q224-A — archive and schema census**
- Enumerate every expected file/vintage in the modern published range and record file name, period, byte size and SHA-256.
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
