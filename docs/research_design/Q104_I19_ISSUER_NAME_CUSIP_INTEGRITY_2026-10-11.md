# Q104:I19 — Historical issuer-name/CUSIP integrity diagnostic

**Audit date:** 2026-10-11 UTC  
**Code baseline when the diagnostic branch was created:** `194850147f047fb087f40589b4c7f2b9a6b8c8e3`  
**Classification:** Source/data integrity only. Not scientific performance evidence or authorization.

## Observed lead

The log for the completed 2023 shard of [Q104 historical 13F census run 38145062319](https://github.com/DWR-debug/trading-agent-public/actions/runs/38145062319) reports a complete acceptance-time join for its 14,502 target accession keys (14,502 records, zero join failures) and all four 2023 quarter archives. Its symbol-level AMP coverage summary includes several issuer-name labels, among them `AMERIPRISE FINANCIAL INC`, `AMERICAN EXPRESS CO`, and `AMERICAN TOWER CORP`.

The frozen Q113 coverage receipt (`research/evidence/q113_13f_q107_coverage_result.json`, receipt fingerprint `29da4de843641e4ac5760fdaaeb4833776ca7220842274234bf64236d2ecb19e`) reports AMP coverage through `CUSIP:03076C106`. The old Q104 shard receipt and its symbol-level log summary keep CUSIPs and issuer names as separate sets; they do not provide a row-level mapping from each issuer label to its CUSIP and accession. Therefore the log is a **diagnostic lead**, not enough by itself to conclude which name is associated with which frozen CUSIP or that any particular filing row is invalid.

## Falsifiable question

For each row in the frozen Q104 CUSIP universe, are the normalized `NAMEOFISSUER` observations stable under that CUSIP, or do multiple materially different issuer labels appear in different accessions/filing dates? Distinguish punctuation/case variants from different normalized names; retain all source rows and the frozen CUSIP list while the discrepancy is unresolved.

## Engineering change

- The historical census scanner groups observed issuer names by exact frozen CUSIP, recording normalized name, row count, accession count, filing-date bounds, bounded raw examples, and row-level accession/date/name samples.
- The per-archive and per-shard receipts carry an `issuer_name_cusip_audit`, `unresolved_issuer_name_cusips`, and an explicit `identity_resolution_proven=false` marker.
- The merger recomputes the audit and rejects a shard when its audit does not reconcile with the observed target CUSIPs/names/row counts. It aggregates variants across archives without resolving or dropping any observations.
- The historical PIT compiler fails closed when audit data is missing, inconsistent, or contains unresolved variants.
- The dashboard shows a blocked identity-review gate when archive/acceptance-clock closure is complete but the required audit is missing or unresolved. It will not advance that state to the PIT compiler.
- Regression tests exercise within-CUSIP variants, future filing exclusion, cross-shard variant propagation, and the blocked dashboard/compilation path.

## What this does not establish

- A name variant is not automatically an identity error. Issuer labels can be descriptive/historical, and resolution requires checking the corresponding SEC archive rows and frozen security identity basis.
- The diagnostic does not change the frozen CUSIP universe, alter filing cutoffs, infer acceptance timestamps, or remove rows.
- The current long-running Q104 job was started on an earlier commit without this diagnostic. Its output must not be described as containing the new row-level audit.
- No Q104 full-census duplicate, Q220 run, or other research workflow is started by this change.

## Next gate

After this PR passes CI and full-suite validation, reconcile the new audit against source rows in the existing SEC 13F archive set or run a bounded, receipt-backed audit-only pass against the frozen accession/CUSIP keys when a safe execution path and genuine capacity are available. Until then, any issuer-name/CUSIP variant remains unresolved and the PIT compiler remains blocked.

All safety flags remain `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False`, and `AUTOMATIC_PROMOTION=False`.
