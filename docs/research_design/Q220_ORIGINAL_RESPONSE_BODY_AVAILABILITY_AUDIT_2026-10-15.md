# Q220 — retained original-response body availability audit

**Audit receipt:** `research/evidence/q220_original_response_body_availability_audit_2026_10_15.json`  
**Receipt fingerprint:** `9d3bab479450124d07d8f19640aa82fc899c5087b7a630f9c9afea02c56d586c`  
**Repository snapshot inspected:** `dbe45ea03456e4533f7651a40f3f58e8747d810b` on public `master`

## Result

The targeted inventory did not find the original direct-primary HTTP response bodies from the frozen 55-row Q220 capture in the current Git tree or in the reviewed retained Actions artifacts. The current Git tree has 3,053 entries, is not truncated, and contains no Q220-named raw-body file with any of the searched raw-document/archive extensions. The frozen fixture is JSON receipt metadata, not a body archive.

This is a **bounded artifact inventory**, not a claim that every Actions artifact across the full repository history was downloaded and exhaustively searched.

## What is preserved

The frozen population artifact (#11710195878) and the same-run route artifact (#11712140975) hold row-level SHA-256/byte-count/source metadata, not the body bytes. The historical positive independent-reproduction receipt (#11717643698), the first blocked compiler (#11729007177), original Feed forensics (#11749259509), header-only evidence (#11751436149), the single-feed boundary receipt (#11838034399), the five-profile HTTP sensitivity probe (#11907246485), and the x64/ARM64 offline lineage artifacts (#11955293266, #11955288234, #11954749019) similarly retain receipts and fingerprints rather than the original direct-primary body bytes.

There is one relevant distinction: complete-submission audit artifact #11921560717 preserves three selected `<DOCUMENT>` blocks extracted from the official `.txt` route plus bounded headers. It does **not** preserve the full `.txt` response, and these blocks are not the original direct-primary HTTP response bodies. None of the three block hashes equals its frozen direct-primary expected SHA-256:

| Accession | Retained complete-submission block | Frozen direct-primary expected hash reproduced? |
|---|---|---|
| `0000064040-19-000059` | 4,774,346 bytes; `cd5f2a074e7e1858bf45a5225944f5eec0d7352fdbf61c0789404645d4b2c512` | No |
| `0001564590-19-003382` | 10,558,528 bytes; `6369f2207e113e72a6529cc1a66d2c1f54eef77bd82b10bc7132ca15e629c768` | No |
| `0000064040-25-000052` | 4,133,826 bytes; `f4eecb1a270e56f2c74607a8ffccf3de512cc8134f2b5ac8d1cfd2478e7ea45b` | No |

Hashes and lengths cannot be reversed into the bytes that produced them. The missing original bodies prevent an exact byte-level diff and prevent identifying the particular source-side or delivery-layer change responsible for the shared drift.

## Disposition

The audit made zero SEC requests and downloaded no new source content. Keep the 55 frozen hashes and source population unchanged. Keep Q220’s historical PIT and current independent-reproduction gates closed. Do not repeat the multi-gigabyte Feed downloads or the already-run direct-primary/HTTP-profile probes.

Only reopen this source-vintage line if a **distinct immutable artifact containing the original direct-primary bytes** or an authoritative contemporaneous source-version record is discovered. Otherwise, preserve the provenance gap as unresolved and move resources to an independent, admissible task under the existing Q104:I19/Q220/Q221 focus lock.

All authority flags remain closed: `PAPER_ONLY=true`; live trading, orders, automatic promotion, performance, holdout selection, ranking, tuning, promotion, and live execution remain false; paid API budget remains USD 0.
