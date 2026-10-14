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


### Historical same-code hash drift found in Git history

The saved population-receipt diffs establish a broader time-varying representation change before the currently frozen hash set was created. The strict same-code comparison is **2026-10-10 17:19 UTC** versus **2026-10-11 08:24 UTC** (with an unchanged metadata re-publish at 2026-10-10 21:54 UTC), not the earlier 10:42 receipt by itself. The 10:42 receipt records the same SPGI 2019 values as the 17:19 receipt but predates the explicit code-fingerprint field, so it is excluded from the same-code proof.

Both strict-comparison endpoints carry gate-code SHA-256 `62ef075c9fe5ccc2527e5a918f9653a5a6d1602359d4bb795a0e97a5370ddcc1` and the exact same code Git-blob SHA-1 `17d3464605138e5035718664fb02ff1a56dcf5cc`. The diff between their immutable receipts changes all **55/55** primary-document SHA-256 values. All **55/55** primary-document byte counts decrease by exactly five bytes. The currently frozen 55-hash/length set exactly matches the 2026-10-11 08:24 side of that comparison.

Three row-level examples:

| Accession | 2026-10-10 17:19 UTC | 2026-10-11 08:24 UTC | Difference |
|---|---|---|---:|
| SPGI 2019 | 4,774,463 bytes; `f9b44be839a2775217b7e0fa15b3d91f8cae6b95dc0723dec54bf03e87aa3e0c` | 4,774,458 bytes; `27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83` | −5 bytes |
| DVN 2019 | 10,558,511 bytes; `77b8333af3c42f4a020ed2667c8911c415d11083ba5456dc06f32c32decd51ce` | 10,558,506 bytes; `b024964aa602547d102af1f9cd51c61a3d723ab25b21ef5686b02ac8d4f40dd1` | −5 bytes |
| SPGI 2025 | 4,133,821 bytes; `33732dc05d44f8e3fa83a82e73f34040a201097456e58ab74fe0d77868724d0a` | 4,133,816 bytes; `afe05282d5d5af7f3068287cceaa679db962264d5d704d2d32ac19e2c4d3531d` | −5 bytes |

A separate comparison against the current blocked compiler receipt finds another common shift on 2026-10-14: all 55 current direct-primary hashes differ from the frozen set, and all 55 current HTTP body lengths are one byte below their frozen lengths. The five-request HTTP-profile test also returned one identical current SPGI 2019 hash and length across all five profiles. Thus, User-Agent/Accept profile variation is still not supported as the cause; rather, the persisted metadata shows at least two systematic between-capture shifts under a fixed population request implementation.

This does **not** prove which five bytes were removed on the first transition or which byte differed in the current capture. No raw original response bodies were persisted, so a byte-level diff cannot be reconstructed. We also do not infer that the difference was an SEC correction, a server-layer rewrite, line-ending normalization, or any other specific cause. The observed evidence is: same-code direct-primary captures; different hashes in all 55 rows; exactly −5 bytes in all rows in the earlier transition; then exactly −1 byte versus the frozen set in all rows in the current compiler view.

The new structured timeline and exact checks are in [`q220_complete_submission_representation_audit_38619590525.json`](../../research/evidence/q220_complete_submission_representation_audit_38619590525.json). No frozen hash has been changed; the PIT/source gate stays blocked.


### Which receipt fields changed in the five-byte same-code transition?

The immutable Git diff was also classified by JSON field name. Across the 55-row receipt, the only per-row fields that changed were:
- `header_sha256`: 55 old and 55 new values;
- `primary_document_bytes`: 55 old and 55 new values;
- `primary_document_sha256`: 55 old and 55 new values.

The receipt-level `generated_at_utc` and derived `receipt_fingerprint` also changed, as expected. The recorded `directory_index_sha256`, selected primary filename and source label, acceptance datetime, and the other persisted XBRL mapping/source-structure fields did not change in the diff. Thus, the five-byte/primary-hash transition coincided with a changed filing-header response hash for every accession, while the directory-index hash stayed constant in the stored receipt.

This narrows where the metadata change is observed: the filing-header route and direct-primary body representation both changed, while the stored directory index did not. It does **not** tell us which bytes changed, or prove whether the source of the change was the SEC origin, a transfer/caching layer, or another response-representation detail. The old response bytes are absent, so the precise cause remains unidentifiable from the repository's retained evidence. The structured field-by-field count is saved alongside the population timeline in the immutable result JSON.


### Collector-code boundary: historical and current routes are not identical

A final offline code check compares the exact `def fetch(...)` source text from the older population gate code blob `17d3464605138e5035718664fb02ff1a56dcf5cc` and current population gate blob `16d37c9b346c1542348d26212c50c257d558c05e`. The function is byte-for-byte identical in both. It uses the same population User-Agent, the same `Accept` value (`text/html,text/plain,application/json,application/xml,*/*`), `Accept-Encoding: identity`, a 60-second timeout, three attempts, and an unbounded `response.read()`. Therefore, the all-55 hash/length change between 2026-10-10 17:19Z and 2026-10-11 08:24Z cannot be explained by a change to that function in source control.

The current PIT compiler is a different route: `automation/q220_historical_representation_pit.py::fetch_primary` uses a different `Accept` value (`text/html,application/xhtml+xml,*/*`), four attempts, and `response.read(MAX_PRIMARY_BYTES + 1)`. Its fetch helper returns `requested_url`, `final_url`, `content_type`, `content_length_header`, `content_encoding`, `last_modified` and `etag`; when a primary hash fails, the persisted error string includes the non-empty `content_type`, `content_length_header`, `content_encoding`, `last_modified`, `etag` and `final_url` values. The requested URL is deterministically derived from the pinned CIK/accession/filename but is not copied into that error string. The one-byte-short current receipt therefore must not be misdescribed as a same-code/same-request-profile comparison with the old population runner.

The evidence now supports three appropriately separated statements:
1. **Historical shift, same population code and request profile:** all 55 direct-primary hashes changed and all lengths fell by five bytes.
2. **Current PIT compiler view:** all 55 current hashes differ and all bodies are one byte shorter than the frozen lengths, but its fetch function/profile differs from the population fetch function.
3. **Bounded repeatability probes:** repeated/profile-varied direct-primary requests were invariant within the fixed SPGI 2019 probe at that time; this does not reconstruct either historical byte set.

No retained raw bodies allow a byte-level diff. This distinction is frozen in the result JSON; it must constrain any future source-contract proposal.


### Historical independent reproduction — exact run, source code and time boundary

The historical positive reproduction is **GitHub Actions run [#38183038217](https://github.com/DWR-debug/trading-agent-public/actions/runs/38183038217)**, workflow `Q220 Independent Historical PIT Reproduction`. The recorded run interval is 2026-10-11 23:06:46 UTC to terminal update 23:08:40 UTC; its `reproduce` job (ID `114599454543`) and all enforcement steps concluded successfully. The receipt was generated at **2026-10-11 23:08:31.626126 UTC** and published at commit [`c3c01e66dba382e062d84614d179ae1c0b97614f`](https://github.com/DWR-debug/trading-agent-public/commit/c3c01e66dba382e062d84614d179ae1c0b97614f).

That exact independent receipt records:
- `status=Q220_INDEPENDENT_PIT_REPRODUCED`, `gate_positive=true`;
- 55/55 primary documents independently retrieved and hash-verified; zero source-hash failures and zero errors;
- all primary-source, identity, strict acceptance-time prefix, TextBlock, structured-fact and mutation-invariant checks passed;
- upstream frozen population receipt `158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543`;
- upstream compiler receipt fingerprint **`1b34b3ac2f3a6fc3ff90fa42cd8ea1c7b73297b5cbd71414a0877bb25d9b203c`**, generated at **2026-10-11 23:06:37.379425 UTC**, with `gate_positive=true`.

The immutable job artifact is [#11717643698](https://github.com/DWR-debug/trading-agent-public/actions/runs/38183038217/artifacts/11717643698), `q220-independent-pit-reproduction-38183038217-1`, SHA-256 `1147d01f71d11c5436b85791bbd4157c8db8fe8d6d11791461627325b6d4477b`. It contains the small reproduction receipt, not the raw 55 primary-document bodies.

**Independent reproducer path (unchanged between the historic run and current master):** `automation/q220_independent_pit_reproduction.py` has the same exact Git blob SHA-1 `3a424e17e2ca35b531e48c011480b1b9fab186db` at the historical run's commit and current master. Its request used its own User-Agent `DWR-debug/trading-agent-public Q220 independent PIT reproduction/1.0 research@example.invalid`, `Accept: text/html,application/xhtml+xml,*/*`, `Accept-Encoding: identity`, a 60-second timeout, 0.25-second request spacing, and at most three attempts. This is the independent retrieval/parser route; it is not the same source file as the primary compiler.

**The compiler was not the same current version.** The historical compiler source file at the run commit has Git blob SHA-1 `c4587f75551297c1ceae9ed151196681eddfbdb8`. The current compiler source file has Git blob SHA-1 `5092a459ce8a976af2a07af926653885a7c86281`. The current canonical compiler receipt was generated at **2026-10-14 17:12:46.964937 UTC** with fingerprint **`b394356b05c0c3e512f750174ffd501aafd9de8809da2266115b57c21d5bb93e`**; it is `Q220_HISTORICAL_REPRESENTATION_PIT_BLOCKED`, reports 55 source-hash failures, zero verified primary documents, and `gate_positive=false`.

This establishes a precise temporal boundary: a positive 55-document independent reproduction existed on 2026-10-11 against compiler fingerprint `1b34b3ac…`; by 2026-10-14 17:12:46 UTC the canonical compiler was blocked against fingerprint `b394356b…`. The unchanged independent-reproducer blob shows that its implementation source did not drift between these two repository states, but it does not make the old upstream compiler receipt current. Nor does it reconstruct the original document bodies. **The historical pass is valid evidence for that specific time-bound chain only; it must not be used to clear the current Q220 gate.**

The exact fields, run/artifact IDs, blob IDs, upstream fingerprints and current comparison are pinned in [`q220_complete_submission_representation_audit_38619590525.json`](../../research/evidence/q220_complete_submission_representation_audit_38619590525.json). The source/PIT gate remains blocked until a new review proves the current representation and exact historical source/availability contract; no expected hash, population membership or gate has been changed.


### First negative compiler receipt and subsequent representation states — offline timeline

A review of the immutable Q220 compiler receipt history narrows the first known hash-provenance failure to a specific receipt interval, then shows two further common-mode representation changes. This analysis reads only saved Git receipts and existing Actions artifacts; it made no SEC requests.

| UTC observation time | Saved status / fingerprint | Primary representation observation |
|---|---|---|
| 2026-10-11 23:06:37.379425 | Positive compiler run [#38182963418](https://github.com/DWR-debug/trading-agent-public/actions/runs/38182963418), fingerprint `1b34b3ac2f3a6fc3ff90fa42cd8ea1c7b73297b5cbd71414a0877bb25d9b203c`, code SHA-256 `6a8fb949…` | 55 verified, zero hash failures; compiler source Git blob `c4587f75551297c1ceae9ed151196681eddfbdb8` |
| 2026-10-11 23:08:31.626126 | Independent receipt [#38183038217](https://github.com/DWR-debug/trading-agent-public/actions/runs/38183038217), fingerprint `64198d5df1451c1a1aab7b9a57e8604dc3fc13fbfb25f2244b8782928d3274c7` | 55/55 independent documents hash-verified against the exact upstream compiler receipt above |
| **2026-10-12 06:00:28.208402** | First retained blocked compiler receipt, run [#38210402239](https://github.com/DWR-debug/trading-agent-public/actions/runs/38210402239), fingerprint `c9cc85da4e632a801a2cf451ecaf83ae8a375688ea33aad42eaba7eee50e3e5d`, same code SHA-256 `6a8fb949…` and same source Git blob | 55 failures, zero verified documents. The SPGI 2019 hash changed from frozen `27177e35…` to observed `08039132…`. Immutable artifact [#11729007177](https://github.com/DWR-debug/trading-agent-public/actions/runs/38210402239/artifacts/11729007177), SHA-256 `1780ac90f403b977d0f80235964c0d828f89534c701d92ffecf36c564120b778` |
| 2026-10-12 07:15:14.773357 | Fingerprint `c7fc53c9…`, compiler code SHA-256 `08f904ef…` | 55 failures; observed SPGI 2019 hash `08039132…` and expected byte lengths for all 55 rows |
| 2026-10-13 00:41:46.756632 | Fingerprint `1960eb6d…`, same compiler code SHA-256 `08f904ef…` | All 55 hashes changed again; all 55 bodies were **7 bytes longer** than their frozen lengths; SPGI 2019 hash `26938196…` |
| 2026-10-14 04:55:53.484073 | Fingerprint `6ca92546…`, same compiler code SHA-256 `08f904ef…` | All 55 hashes changed again; all 55 bodies were **1 byte shorter** than their frozen lengths; SPGI 2019 hash `fc7dfedd…` |
| 2026-10-14 17:12:46.964937 | Current canonical receipt, fingerprint `b394356b05c0c3e512f750174ffd501aafd9de8809da2266115b57c21d5bb93e` | Still blocked, 55 hash failures and zero verified primary documents |

The last positive compiler receipt and first blocked compiler receipt are **6 hours, 53 minutes, 50.829 seconds apart**. The first negative receipt uses the same compiler source Git blob and compiler-code SHA as the positive compiler receipt, so the first observed shift cannot be explained by a source-code change between those two runs. This interval is an observation bound only: it does not identify the exact moment of change on the server or intermediary path.

The saved receipts also show the returned representation was not one single stable “current” variant: the SPGI 2019 primary hash was `08039132…` on 12 October, `26938196…` on 13 October with +7 bytes across the 55 rows, and `fc7dfedd…` on 14 October with −1 byte across all 55 rows. Between repeated snapshots in each state, all 55 per-row failure records were identical. The logged SPGI 2019 `Last-Modified` remained `Wed, 13 Feb 2019 11:02:53 GMT` across the later states despite the changing body hash/length. That timestamp therefore does not identify the body version for this investigation.

This substantially strengthens the common-mode representation-drift explanation and time-bounds the first observed loss of the frozen hash match. It still does not prove which bytes changed, why the representation changed, or whether the cause was at the SEC origin, a caching/intermediary layer, or another delivery component. No raw historical primary bodies were retained, so a historical byte-level diff remains impossible.

All historical positives remain explicitly time-bound to their own compiler fingerprints. The current canonical compiler remains `b394356b…`, blocked with 55 failures. No source hashes, population membership, or research gates are changed.
