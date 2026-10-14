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
