# Q104:I19 — R7 applicability review for the frozen 53 residuals

**Preregistered request:** research/run_requests/q104_i19_residual_policy_applicability_r7.trigger  
**Source of truth:** DWR-debug/trading-agent-public  
**Scope:** review-only coverage of the exact 19 previously unobserved filing-date mismatches, not source repair or a production rule change.

## Frozen evidence and target set

The request consumes the immutable recovery result [#38250105408](https://github.com/DWR-debug/trading-agent-public/actions/runs/38250105408), the two architecture receipts from [#38557631541](https://github.com/DWR-debug/trading-agent-public/actions/runs/38557631541), and the separately pinned R4/R5/R6 diagnostics [#38574180245](https://github.com/DWR-debug/trading-agent-public/actions/runs/38574180245), [#38582684174](https://github.com/DWR-debug/trading-agent-public/actions/runs/38582684174), and [#38588100012](https://github.com/DWR-debug/trading-agent-public/actions/runs/38588100012).

The frozen 53-case recovery receipt contains 36 filing-date mismatches, 7 identity conflicts (6 CIK + 1 Form), and 10 complete-submission-header 404s. Previous pinned evidence covers 17 of the 36 date-mismatch rows. R7 targets the remaining 19 exact accession keys, fixed in the request and compiler constants:

| Frozen quarterly dataset | Target rows | Pinned bytes | SHA-256 |
|---|---:|---:|---|
| 2020 Q3 Form 13F | 8 | 49,051,852 | 2bcc0bebb7f9eb66b757e44583c0b51069941b9f87a3b4b107a24abe2b7cd7f3 |
| 2015 Q1 Form 13F | 7 | 42,434,965 | 96ab4cb60063beb98317ce3e2558b3539546e54485fdb1c68adcd33b5634a6ee |
| 2013 Q3 Form 13F | 4 | 36,457,022 | aa20c79d552722cb7bae8cefe3e63cd61a0929a4d5234c0b5d9ce1c75309a616 |

Total archive bytes are 127,943,839, below the fixed 150,000,000-byte combined budget. The job validates each archive against its hash/length pins from both original and repaired source-shard receipts before parsing its 13F submission rows. It then queries only three EDGAR header routes for each frozen accession: the filing index header, raw SGML header and complete-submission header prefix (57 route requests total). It downloads no daily Feed archives and no primary filing HTML. Response bodies are parsed in memory and never written to the artifact.

## Analysis contract

Each of the 19 R7 observations must independently establish accession, CIK and Form agreement with the exact pinned 13F row; all three EDGAR header dates must agree and differ from the bulk Form 13F filing date; all three acceptance timestamps must agree. An unusable route, source-byte mismatch, changed helper hash, changed upstream receipt, failed source identity or budget overflow fails closed. The ARM64 lane makes no network requests and must independently reproduce the same deterministic analysis fingerprint from the stored capture and exact receipt bytes.

A complete review combines the 14 previously cross-vintage observations, R4/R5/R6, and the 19 R7 rows into a unique 36-row set. It remains a field-precedence review proposal not applied. It does not apply a precedence rule, mutate historical receipts, change the production join, restart the census, or clear historical PIT/public-observation gates.

## Decision boundary

The possible review output remains diagnostic/source-lineage evidence only:
- preserve bulk Form 13F filing date unchanged;
- preserve consistent EDGAR header/index filed date separately with a discrepancy flag;
- retain acceptance time and DATE-OF-FILING-DATE-CHANGE as distinct metadata;
- apply no date arithmetic, imputation or blanket correction.

The seven CIK/Form conflicts and ten HTTP 404 records remain separate unresolved work. No performance, holdout selection, ranking, tuning, promotion, order, or live-execution authority is created.

Safety: PAPER_ONLY=true; LIVE_TRADING_ENABLED=false; ORDERS_ENABLED=false; AUTOMATIC_PROMOTION=false; paid API budget remains 0 USD.
