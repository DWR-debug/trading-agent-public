# Q220 — Bounded header-only acceptance evidence

**Frozen source run:** [#38254139755](https://github.com/DWR-debug/trading-agent-public/actions/runs/38254139755)  
**Frozen receipt fingerprint:** `840f280cbcb1fdbe4b2fbaa88f8d7f02edf447799e13fe0171d37fcd57f3221b`  
**Current state:** `FORENSIC_COMPARISON_INCOMPLETE`, 0/3 complete comparisons; the 55 frozen primary-document hash failures remain.

## Why this is separate from Feed forensics

The post-fix Feed probe downloaded the three exact daily Feed archives and their expected `.nc` members completely. For all three original submission wrappers, accession, filer CIK, form, and filing date parsed and matched the frozen sample keys, but `ACCEPTANCE-DATETIME` was absent. The receipt also confirms that the current SEC primary documents match the prior frozen actual hashes but not the prior frozen expected hashes. This header-only probe collects no Feed archives and no primary filing documents.

## Frozen sample keys and bounds

The three sample record keys, filer CIKs, accessions, forms, filing dates and source receipt fingerprints are hard-coded and must match the immutable artifact byte-for-byte before any HTTP request. Each sample is checked on the SEC index-header route, raw `.hdr.sgml` route, and only the prefix of the complete-submission `.txt` through `</SEC-HEADER>`.

- Maximum 262,144 bytes per route; at most nine requests and 3,000,000 total transferred bytes.
- At least one second between requests, 60-second HTTP timeout.
- Prefix-mode parse data is cut at `</SEC-HEADER>`; no primary document is saved, parsed or used.
- Every route response is hashed and records the returned HTTP metadata, observed identity and acceptance timestamp.
- Missing, inconsistent or identity-mismatched fields produce `HEADER_EVIDENCE_INCOMPLETE` and a fail-closed workflow result.

## Decision boundary

Even a complete acceptance-time header observation is only supplemental evidence. It cannot prove source vintage, reconcile any of the 55 frozen expected primary hashes, or reopen Q220's source-hash, historical PIT, performance, holdout, ranking, tuning or promotion gates. It does not authorize orders or live execution. Do not change any source receipt, expected hash, sample key, source population fingerprint, contract or byte limit to force a pass.
