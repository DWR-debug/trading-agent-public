# Q104:I19 residual lineage diagnostic R2 — preregistration

**Registered:** 2026-10-12 19:50 UTC  
**Question:** Does the observed bulk FILING_DATE versus official EDGAR header-date disagreement recur in two additional, independently pinned SEC Form 13F archive vintages, including a recent 2025 vintage?

## Frozen source inputs

All pins below come from the immutable six-shard census run #38168441086 and its archived shard receipts. The source-page SHA-256 remains b2c4083c3615ce6646764d8e80dc18c2f5484a25c417281be580bdc650817b46.

| Shard | Archive | SHA-256 | Bytes | Frozen failure labels |
|---|---|---|---:|---|
| 2017–2018 | 2017q1_form13f.zip | edeb7e682ca82cf49a1cded13ae82177126f3284a0464d46d7b58849e652c587 | 43,724,820 | 2 FILING_DATE_MISMATCH |
| 2024–2025-09 | 01jun2025-31aug2025_form13f.zip | 9468ae5e90278e847d5035f5efe4294b104a2a25f35169f532b83cea6de19365 | 86,295,095 | 2 FILING_DATE_MISMATCH |

Shard receipt fingerprints: 8175c92b1a899a8993af069d68f9de1553364b84c8c7029c1a1933c61b0a8db8 and 2500f2ee3f07258a9525cd6e7018fd67f380cf0244028c5948866d55c835794e.

## Frozen sample keys

- 0000950123-17-002537
- 0000950123-17-002540
- 0000895421-25-000499
- 0001102578-25-000024

The four keys were selected only from the original frozen failure labels, before new downloads. No sample substitution is permitted.

## Method and bounds

- Re-download exactly the two pinned archives; require exact SHA-256 and byte-count equality to the immutable census receipts before parsing any row.
- Capture the same three official SEC header routes per accession: filing index headers, raw .hdr.sgml, and a bounded complete-submission header prefix.
- Maximum archive response size: 100,000,000 bytes each; aggregate download ceiling: 150,000,000 bytes; each header response: 262,144 bytes; minimum request spacing: 1 second.
- Validate accession, filer CIK, form, filing date, and acceptance timestamp across the frozen Form 13F data-set row and official EDGAR routes.
- No census restart, no receipt repair, no date arithmetic, no blanket field override, no performance/holdout/ranking/tuning/promotion, no orders or live execution.

## Decision rules

A complete result only establishes what these four preselected rows show. It does not estimate prevalence across the remaining 49 unresolved accessions and does not itself clear the acceptance-time or historical archive gate. If both new vintages reproduce the same field conflict, the next step is a separately reviewed field-precedence proposal grounded in SEC documentation; if they differ, preserve the stratification and diagnose the specific source route. Any missing or changed archive pin fails closed.
