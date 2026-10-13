# Q220 — Original SEC daily Feed hash forensics

**Registered:** 2026-10-12 07:50 UTC  
**Stage:** three-accession source-provenance diagnosis. Not a population repair, positive source/PIT result, or performance experiment.

## Why this probe exists

The latest Q220 compiler receipt is still blocked with 55/55 primary-document SHA-256 mismatches. The observed current HTTP responses have plausible text/html type and byte-count agreement with the frozen population receipt, but different hashes. This excludes a simple length/truncation explanation; it does not identify the cause.

The SEC's official [EDGAR README](https://www.sec.gov/Archives/edgar/README.txt) describes the daily Feed directory as `YYYY/QTRn/YYYYMMDD.nc.tar.gz` archives holding individual submission payloads and separately named correction records (for example .corr01). The SEC's [Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) document also explains that current indexes may reflect post-acceptance corrections that are not retroactively reflected in older daily indexes. This makes a small original-submission comparison appropriate before any code or hash change.

## Frozen inputs and three samples

The run is bound to compiler receipt blob 2a3abbff6c6950e4f11d85bda92cb9c57a5c7ee0, fingerprint c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075, and source-population fingerprint 158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543. It tests one older direct-CIK filing, one older filing whose accession prefix represents a filing agent, and one recent direct-CIK filing. Exact keys, filenames, and expected hashes are pinned by the preregistration and request trigger.

## Bounded method

For each of the three fixed keys, fetch only (1) the current public primary-document URL, capped at 15 MB, and (2) the original filing-day SEC Feed archive using the official year/quarter directory (`Feed/YYYY/QTRn/YYYYMMDD.nc.tar.gz`), capped at 1.5 GB compressed per Feed. The code verifies SEC submission header accession, CIK, form, filing date, and acceptance-header presence; extracts only the exact primary filename; records raw and narrowly defined outer-linebreak hash variants; and lists correction members present in that one daily Feed. The maximum total download is 4.6 GB; cumulative uncompressed tar member bytes scanned per Feed are capped at 12 GB. Each request has a 600-second timeout. These ceilings were fixed before the first run after official SEC listings showed the 2019-02-13 and 2019-02-20 Feed archives at 845,477 KB and 814,528 KB, and the 2025-02-11 archive at 1,084,431 KB. The request remains limited to these same three dates and accessions. No annual or quarterly archives are downloaded.

The run does not prove that no later-day correction exists; it is an initial source-vintage diagnostic. A match between a frozen expected hash and an original Feed body is evidence for that one specific accession only.

## Decision rules

- If a frozen expected hash matches an original Feed body variant and today's public primary bytes differ, record potential source-vintage drift and write a follow-up proposal. Do not automatically replace any expected hash or unblock Q220.
- If no frozen expected hash matches the original Feed body variants, keep Q220 blocked and investigate frozen extraction provenance or document parsing.
- If any source is missing, oversized, identity-inconsistent, or incomplete under the bounds, preserve an incomplete receipt and make no source-vintage claim.

All scientific, performance, holdout, ranking, tuning, promotion, orders, and live-execution gates remain closed.


The compiler input is copied to an immutable fixture rather than reading `latest`, which automated status/evidence refreshes may overwrite. Its embedded receipt fingerprint and the three exact expected-hash pins remain unchanged.

## Post-run diagnosis — 2026-10-12

Two bounded runs completed their tar scans but did not locate the original submission member; both produced **incomplete** forensic receipts (0/3 completed comparisons), not evidence that the SEC Feed lacks those filings. The first correction incorrectly treated the PDS subscriber filename convention `[ACCESSION-NUMBER].dissem` as the member name inside the daily non-cooked Feed TAR. Those are different layers.

A focused implementation review of an independent SEC Feed parser shows the daily `.nc.tar.gz` archive members use `./{accession}.nc`, while correction members use `{accession}.corr01` and similar suffixes. See the parser's explicit layout and implementation: [milliondreams/bwm `feed_bulk.py`](https://github.com/milliondreams/bwm/blob/main/src/data/sources/edgar/feed_bulk.py). The SEC [EDGAR README](https://www.sec.gov/Archives/edgar/README.txt) independently confirms that each filing is a separate submission inside the daily Feed TAR and correction submissions are separately labelled. The local fixture is therefore changed to `.nc`, and the resolver recognizes the exact `.nc` member as well as its existing bare/`.txt` compatibility names; identity and byte limits stay unchanged.

Run `38233685159` remained `FORENSIC_COMPARISON_INCOMPLETE`: 2,829,769,099 bytes downloaded, 0/3 comparisons completed, and source hashes unchanged. The immutable receipt is its workflow artifact; it does not replace the current compiler/PIT receipt.

This is an extraction-path correction only. It does not change the pinned accession sample, accepted-submission identity checks, maximum feed/member/scan/download limits, frozen expected hashes, or any Q220 gate. The next expensive run must wait for the new parser and fixture CI to pass and must be triggered by a deliberate new request sequence. The workflow is restricted to explicit request-file changes, so parser/test edits alone do not re-download multi-gigabyte SEC Feed archives.


## Post-run byte-boundary diagnosis — 2026-10-13

The bounded forensic run [#38439183202](https://github.com/DWR-debug/trading-agent-public/actions/runs/38439183202) completed two of three samples and failed closed on the third because the 2025-02-11 daily Feed download was truncated at 4 MiB after a prior incomplete attempt. Its immutable receipt is [artifact 11835800109](https://github.com/DWR-debug/trading-agent-public/actions/runs/38439183202/artifacts/11835800109), fingerprint 4accecf3dcb0708d4b61259d9f9234f0946a7d25150aa5864f42b948b272566f.

For the two fully scanned Feed submissions, identity checks passed (accession, filer CIK, form, filing date, exact primary filename, and full TAR scan). Yet no frozen hash matched the extracted body variants. The frozen primary byte lengths were 4,774,458 (SPGI 2019) and 10,558,506 (DVN 2019), while the extracted TEXT payloads were 4,774,237 and 10,558,411 bytes—short by exactly 221 and 95 bytes. The current direct SEC responses observed in the same run were each 7 bytes longer than the frozen lengths. These counts point to a likely extraction-boundary issue, but the hash-only artifact does not contain enough original payload bytes to claim the cause as proved.

The extractor previously used a non-greedy first-close regex for TEXT, which accepts the first literal closing token even if the same byte sequence occurs inside the embedded HTML. This change selects only a closer with whitespace-only trailing bytes before the surrounding DOCUMENT boundary, records the number and offset of closing-tag candidates, and fails closed if that boundary is ambiguous. A regression test embeds a literal closing token inside the HTML body and requires every subsequent body byte to be preserved.

**This is an extraction-integrity repair, not a source-hash repair.** The 55 expected hashes, 55-row population, frozen three-accession sample, archive identities, byte ceilings, and all scientific/PIT/performance gates remain unchanged. The incomplete 2025 sample is not inferred from the two older rows; no additional multi-GB source run is started by this PR. Any future live confirmation requires a separately reviewed request and successful exact byte/hash reconciliation.

## Single-feed validation result — 2026-10-13 (SPGI accession)

**Run:** [Q220 Single SEC Feed Boundary Validation #38446029194](https://github.com/DWR-debug/trading-agent-public/actions/runs/38446029194)  
**Immutable artifact:** [artifact 11838034399](https://github.com/DWR-debug/trading-agent-public/actions/runs/38446029194/artifacts/11838034399)  
**Upstream receipt fingerprint:** \`fe98cecb579d15ecf6e48c3b84a3a699345bf840745e9be0c7cfcd972aebf03a\`  
**Status:** \`SINGLE_FEED_BOUNDARY_COMPARISON_COMPLETE\` — the bounded identity/extraction comparison completed; this is not a positive Q220 source-hash or PIT result.

### Exact result

The run validated the exact source fixture Git blob SHA, frozen source-receipt fingerprint, 55-failure compiler receipt, fixed accession/date/form/primary filename and all original-submission identity checks before accepting the result. It downloaded **870,543,118 bytes total**, below the registered 950,000,000-byte ceiling; the single daily Feed archive was 865,768,653 bytes. The archive was completely scanned, examining 6,501,098,502 uncompressed member bytes under the 12 GB cap. The exact \`./0000064040-19-000059.nc\` member was 26,429,640 bytes, and accession, CIK, form and filing date matched.

The corrected extractor reported **one** \`</TEXT>\` closing-tag candidate in the exact primary \`spgi-20181231x10k.htm\` document block. Therefore, this actual sample gives no support to the hypothesis that an embedded \`</TEXT>\` token caused its earlier truncation: the corrected parser selected the only closer and still extracted 4,774,237 primary-text bytes, 221 fewer than the frozen 4,774,458-byte document.

No hash variant matched the frozen expected SHA-256 \`27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83\`:
- Raw extracted \`TEXT\`: 4,774,237 bytes; SHA-256 \`aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368\`.
- Drop one leading line break: 4,774,236 bytes; SHA-256 \`54d62d26b31bd4e8a94b1f49c1641f2fc69c79cd5b4290d11d9191a4e9db39d0\`.
- Drop outer line breaks: 4,774,235 bytes; SHA-256 \`bbaee52940cc5f2327445da95e98e46705d90b58a615edcd2d83df08da3a6fc1\`.

The current primary-document URL returned HTTP 200 and 4,774,465 bytes, SHA-256 \`2693819652172f0c218394ef036eb3f4af95c2a7077f624f6efcd990df370172\`, also matching neither the frozen expected hash nor the previously captured 4,774,458-byte body. Its HTTP \`Last-Modified\` header continued to report 13 February 2019. This is a real source-byte/provenance discrepancy, not a successful hash reconciliation.

### Interpretation and next gate

This probe closes the one-accession byte-boundary test, not Q220. It does **not** reproduce the frozen expected hash and does not demonstrate that the expected hash came from the original submission. The proposed inner-\`</TEXT>\` explanation is not supported for this SPGI sample; the root cause remains unresolved. Keep all 55 frozen hashes and the compiler receipt unchanged, leave Q220 blocked, and do not repeat this 866 MB archive or launch another multi-GB run without a distinct, preregistered hypothesis.

\`source_vintage_proven=false\`, \`historical_first_public_observation_proven=false\`, \`gate_positive=false\`, and performance, holdout selection, ranking, tuning, promotion and live execution remain false. Paper-only remains mandatory.
