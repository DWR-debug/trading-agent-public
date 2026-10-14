# Q220 — Complete-submission representation lineage audit

**Registered:** 2026-10-14 18:43:09 UTC (preregistration commit)  
**Status:** preregistered, bounded source/PIT diagnostic only  
**Request sequence:** `2026-10-14T18:43:14Z` (trigger freeze commit)

## Question

The Q220 source population froze 55 primary-document SHA-256 values and byte counts from the direct EDGAR primary-document URL route, but it did not retain the raw response bytes from that capture. Subsequent current primary-HTML responses, the primary `<TEXT>` bodies extracted from the exact original daily Feed submission wrappers, and the frozen source hashes disagree. The three original daily Feed submissions were already retrieved and fully scanned under an earlier frozen forensic request; they must not be downloaded again.

This request tests one distinct, official representation route: the SEC Complete submission text file (`.txt`) for the same three already-frozen accessions. The exact URL shape is documented by SEC's Accessing EDGAR Data guidance and illustrated in official filing-detail pages:
- https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data
- https://www.sec.gov/about/developer-resources

The selected input rows, expected hashes, prior-feed hashes, accession, CIK, form, filing date, and acceptance clock are frozen in the preregistration JSON and the run trigger. The route is not expanded if a sample fails.

## Bounded method

The capture job sends exactly one GET to each of these URL patterns, in fixed sample order:

`https://www.sec.gov/Archives/edgar/data/{CIK}/{accession_without_dashes}/{accession}.txt`

Each response has a hard cap of 45,000,000 bytes; the aggregate network-read cap is 120,000,000 bytes; timeout is 180 seconds; the requests are at least one second apart. There are no retries, alternate routes, user-agent contrasts, cache-busting query parameters, direct primary HTML requests, daily Feed requests, or extra accession samples. The `.txt` response bodies are inspected in memory and are never written to disk.

For each successful response, the parser requires agreement on the exact accession, filer CIK, form, filing date, and known acceptance timestamp. It locates exactly one primary filename and selects only a unique `</TEXT>` closer whose remaining content before `</DOCUMENT>` is whitespace. Ambiguous or over-limit content fails closed.

Only two source-derived byte ranges are retained for independent offline replay: the prefix before the first `<DOCUMENT>` (capped at 2 MB) and the exact matching primary `<DOCUMENT>` block (capped at 16 MB). The complete submission text file itself is not persisted. The ARM64 verifier does no network access; it reparses those preserved ranges, repeats all identity and hash calculations, and must reproduce the capture analysis fingerprint.

## Interpretation

For each accession, compare:
1. the exact extracted `<TEXT>` body SHA-256 and length against the frozen expected primary hash and length;
2. the same body against the previously recorded, exact original-feed `<TEXT>` body SHA-256 and length;
3. the complete-submission response metadata and hash/length against the already retained lineage evidence.

A match to any previously observed body can establish reproducibility of that representation for that accession only. It does not establish which historical representation generated the original frozen expectation, prove a first-public time, or authorize replacement of a frozen hash. The diagnostic remains non-authorizing even if a hash unexpectedly matches.

Any incomplete response, identity mismatch, missing/duplicate primary filename, ambiguous text boundary, or exhausted byte budget produces an incomplete result. No source hash, source-population membership, source code pin, expected hash, or research gate may be altered to force a pass.

## Stop and safety rules

- Do not repeat the original daily Feed downloads or fetch a direct primary `.htm` route.
- Do not make any request outside the three frozen Complete submission `.txt` URLs.
- Do not rewrite or silently refresh the 55 frozen expected hashes.
- Preserve Q220 blocked unless a separately reviewed source-contract correction is supported by immutable source evidence, independent reproduction, and explicit gate review.
- No scientific/performance evidence, holdout selection, ranking, tuning, promotion, orders, or live execution is authorized.
- Paper-only remains mandatory; live trading, orders and automatic promotion remain disabled.


## Result — complete-submission audit, 2026-10-14

The frozen run was executed after PR [#1464](https://github.com/DWR-debug/trading-agent-public/pull/1464) merged. Capture run [#38619590525](https://github.com/DWR-debug/trading-agent-public/actions/runs/38619590525) completed successfully; immutable capture metadata is in [artifact #11921560717](https://github.com/DWR-debug/trading-agent-public/actions/runs/38619590525/artifacts/11921560717). It made three HTTP-200 requests, read 86,836,164 aggregate bytes (below the 120,000,000-byte cap), and used zero retries. The complete `.txt` response bodies were not persisted.

The ARM64 [independent offline-reproduction job](https://github.com/DWR-debug/trading-agent-public/actions/runs/38619590525) completed successfully for all three samples and made zero network requests. Its immutable verification artifact is [#11922195517](https://github.com/DWR-debug/trading-agent-public/actions/runs/38619590525/artifacts/11922195517). Capture analysis fingerprint: `867ad0b84913619a2b505e82e8c0903dea7b0e44dd4b77d31ccc05d51e5b8ca5`; verification fingerprint: `cd5467600478db509a9bc3903c43a08498b077365b9156ec92bb096e86503685`.

### Exact comparison

| Frozen accession | Frozen expected primary | Current Complete `.txt` extracted raw `TEXT` | Earlier original-Feed `TEXT` reproduced? | Expected hash reproduced? |
|---|---|---|---|---|
| SPGI 2019 — `0000064040-19-000059` | 4,774,458 bytes; `27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83` | 4,774,237 bytes; `aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368` | Yes; exact SHA and length | No |
| DVN 2019 — `0001564590-19-003382` | 10,558,506 bytes; `b024964aa602547d102af1f9cd51c61a3d723ab25b21ef5686b02ac8d4f40dd1` | 10,558,411 bytes; `e72d769d3ebcd9fddee3732785dd94d530f6d81a03c94c7f9343fb5bda25e2cc` | Yes; exact SHA and length | No |
| SPGI 2025 — `0000064040-25-000052` | 4,133,816 bytes; `afe05282d5d5af7f3068287cceaa679db962264d5d704d2d32ac19e2c4d3531d` | 4,133,721 bytes; `44040ca6cf934f7bd336063ba4b3da67a3c815678dda87474a11a1e6a2ec47ba` | No; same byte length as the prior Feed extraction but different SHA | No |

All three current submissions returned HTTP 200 and passed accession, filer CIK, form, filing-date and acceptance-datetime validation. None reproduced a frozen expected hash. For the 2019 samples, the Complete `.txt` raw `TEXT` exactly reproduces the previously extracted original-Feed `TEXT` body. For the 2025 sample, its text body has the same length as the prior Feed extraction but a different SHA-256. This narrows the observed representation lineage; it does not reveal which representation generated the original 2025 expected hash or the 2019 expected hashes.

### Original population-run review

The original population run [#38155914188](https://github.com/DWR-debug/trading-agent-public/actions/runs/38155914188) has a successful 55/55 population receipt with fingerprint `158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543`. Its retained runner stdout contains only the aggregate success summary; it does not retain per-accession HTTP headers or raw response bodies. The immutable population artifact preserves hash/length fields but not the original primary-document bytes.

The same run's independent route artifact [#11712140975](https://github.com/DWR-debug/trading-agent-public/actions/runs/38155914188/artifacts/11712140975) contains an additional cross-check for SPGI 2025: the direct primary-document route returned the frozen `afe052...` hash and 4,133,816-byte length at 2026-10-11 18:49:19 UTC, after the population receipt was created. The route artifact stores the hash and length, not the response body or per-row HTTP response metadata. Thus it corroborates that the frozen 2025 direct-route hash was reproducible at that time, but it does not preserve bytes for a later byte-for-byte diff.

The population code's `primary_document_source=company_submissions_recent` labels where the primary filename was selected; the selected document body was fetched separately from the direct EDGAR Archives accession URL. The later compiler receipt records a distinct present-time byte set for all 55 rows (including lengths one byte below the frozen expectation for these three samples). The five-request HTTP-profile sensitivity probe also returned the same current SPGI 2019 representation for every profile. The request-profile variation hypothesis therefore remains unsupported; the historical capture body is missing.

### Disposition

This is a reproducible **representation diagnostic**, not historical source-vintage proof. The original source hash/byte values remain untouched, the compiler still reports 55 hash failures and zero verified primary documents, and Q220 remains blocked. Neither current `Last-Modified` nor a matching daily-Feed/Complete-submission body is treated as proof of first public observation time.

The detailed metadata-only result is preserved in [`q220_complete_submission_representation_audit_38619590525.json`](../../research/evidence/q220_complete_submission_representation_audit_38619590525.json). It records the immutable workflow artifact IDs/digests, three sample comparisons, original runner-log limitations, and all safety/gate flags.

**Next step:** offline-only inspection of retained Git history and older immutable artifacts for a body-bearing original primary response or independently pinned historic representation. If none exists, keep the missing-byte provenance gap explicit. Do not redownload the three daily Feed archives or the direct primary documents, rewrite expected hashes, or alter Q220 gates.
