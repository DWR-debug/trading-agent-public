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

The first run completed its archive scans but did not locate any original submission member in the three Feed TARs. Its status is therefore **incomplete**, not evidence that the daily Feed lacks those filings. The parser searched only for the bare accession and `.txt`; the SEC's [EDGAR Public Dissemination Service specification](https://www.sec.gov/files/edgar/pds_dissemination_spec.pdf) describes electronically accepted submissions as `[ACCESSION-NUMBER].dissem`. The corresponding local test now uses that documented member suffix.

This is an extraction-path correction only. It does not change the pinned accession sample, accepted-submission identity checks, maximum feed/member/scan/download limits, frozen expected hashes, or any Q220 gate. The Q220 feed comparison must remain incomplete until a new, explicitly triggered run proves the exact member and header identities. The workflow's push trigger is consequently narrowed to the explicit request file; edits to the parser, tests or workflow do not automatically re-download multi-gigabyte SEC Feed archives.
