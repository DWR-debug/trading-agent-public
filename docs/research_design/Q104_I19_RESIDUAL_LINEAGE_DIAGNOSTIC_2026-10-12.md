# Q104:I19 — Residual Source-Lineage Diagnostic

**Date:** 2026-10-12  
**Purpose:** read-only investigation of four residual filing-date mismatches.  
**State boundary:** this diagnostic is not a repair, census, acceptance-time proof, or candidate promotion gate.

## Frozen inputs

The diagnostic reuses completed Q104:I19 source census run 38168441086, source-page SHA-256 b2c4083c3615ce6646764d8e80dc18c2f5484a25c417281be580bdc650817b46, and only two archive byte identities already recorded in the original shard receipts:

| Archive | Shard | Frozen archive SHA-256 | Bytes |
|---|---|---|---:|
| 2015q1_form13f.zip | 2013-2016 | 96ab4cb60063beb98317ce3e2558b3539546e54485fdb1c68adcd33b5634a6ee | 42,434,965 |
| 2020q3_form13f.zip | 2019-2020 | 2bcc0bebb7f9eb66b757e44583c0b51069941b9f87a3b4b107a24abe2b7cd7f3 | 49,051,852 |

The script validates the canonical fingerprints of both original shard receipts, the source-page bytes, these exact archive hashes/lengths, and the original failure labels before it reads the archive rows.

## Frozen sample keys

The four samples are two filing-date mismatches from each high-count archive: 0000950123-15-003104, 0000950123-15-003463, 0001800724-20-000002, and 0001800724-20-000003. Together, the source receipt reports 21 of the 53 unique unresolved accessions across the two selected archives. This is a diagnostic sample, not a prevalence estimate.

For each sample, the workflow records the submission.tsv row from the verified archive, then probes three official SEC routes derived from that row's filer CIK: index headers, raw .hdr.sgml, and a bounded complete-submission header prefix. Each body is size-limited and hashed. Extracted accession, filer CIK, form, filing date, and acceptance timestamp are observations only; the script never treats a mismatch as valid and never substitutes one source's identity for another.

## Limits and decision boundary

- At most two source archive downloads, each capped at 60,000,000 bytes; aggregate download ceiling 150,000,000 bytes.
- At most four accession keys and three bounded SEC header probes per key; request spacing is at least one second.
- No source archive is examined further unless its downloaded bytes match the exact frozen archive SHA-256 and byte count.
- No census restart, repair receipts, acceptance-time merge, model performance run, holdout selection, ranking, tuning, promotion, order placement, or live execution.
- Even a complete diagnostic does not resolve the 53 residuals. The acceptance-time gate and historical archive gate remain closed until independent source evidence and strict identity validation support a separate, reviewed decision.
