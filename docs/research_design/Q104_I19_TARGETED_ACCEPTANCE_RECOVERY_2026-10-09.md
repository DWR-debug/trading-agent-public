# Q104:I19 — Targeted Acceptance-Time Recovery

**Status:** implementation contract / recovery-only  
**Date:** 2026-10-09  
**Candidate lock:** Q104:I19 remains the highest-priority formal-readiness candidate; Q218 remains the parallel source/PIT candidate.

## Recovery sequence

1. Wait until the selected census workflow run is terminal. Do not attempt to rerun a shard while its parent workflow run remains active.
2. Ensure all six shard receipts exist for the same run and share the same frozen `source_page_sha256`. A Windows runner shutdown can leave a shard without a receipt. Re-run only the missing/failed shard jobs after the parent run is terminal; do not re-run the full workflow.
3. Download the six receipts and the frozen source-page artifact for that exact run.
4. The targeted recovery script checks every input shard fingerprint, exact shard universe, source-page bytes/hash, top-level-vs-per-archive failure-set equality, and each affected quarterly archive SHA-256. It recovers CIK, form, filing date and period only from the byte-identical source archive used by the original shard.
5. It retries only accession headers whose frozen failure reason is transient (HTTP 408/425/429/500/502/503/504, timeout or network transport failure), with a fixed maximum of three header attempts per accession and the existing SEC request limiter. Identity/form/date/acceptance validation errors are not retried.
6. It emits patched shard receipts and a separate immutable recovery receipt with original and repaired fingerprints, exact failed/repaired/unresolved accession sets and attempt counts.
7. The existing strict six-shard merge remains authoritative. If any accession remains unresolved, a shard receipt is missing, the source archive hash differs, or timestamps/identities do not validate, no latest census receipt is published.

## Why this is not a full Census retry

Acceptance failures occur after the quarterly archives were scanned. Reprocessing all six shards repeats successful archive scans and burns several hours of Windows and hosted capacity. The recovery lane revisits only source archives containing a frozen unresolved accession, verifies those archive bytes against their original SHA-256, and performs bounded header-only retries. If a source archive is no longer byte-identical, the task stops instead of mixing versions.

## Restart/interruption policy

A Windows restart can interrupt all Windows matrix jobs even when hosted shards continue. The job artifacts are authoritative: a missing shard receipt is missing evidence, not an empty failure set. Wait for the run to end, then retry only the affected Windows jobs for that run. Do not merge receipts across different census runs unless their frozen source-page hash, archive inventory and every relevant archive fingerprint are shown to be identical. The current recovery workflow enforces one-run lineage and refuses mixed source snapshots.

## Automatic dispatch protection

The generic capacity dispatcher may make one technical retry after a failed workpack. That rule is not appropriate for the multi-resource I19 Census because its known failure mode can be a set of transient acceptance-header failures. Once an I19 census run fails or is cancelled, automatic capacity replenishment must select targeted recovery rather than dispatch another six-shard Census. A deliberately initiated new full Census remains a separate manual engineering decision.

## Scientific boundary

This work is source/identity/PIT preparation only. It creates no performance evidence and authorizes no performance run, holdout selection, ranking, tuning, promotion or live execution.

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`ORDERS_ENABLED=False`  
`AUTOMATIC_PROMOTION=False`
