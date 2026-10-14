# Q104:I19 — descriptive comparison of frozen 14-row aggregate and R4–R6

**Prepared:** 2026-10-14  
**Type:** documentation-only descriptive synthesis; not a new evidence receipt  
**Status:** no precedence decision applied; all gates remain closed

## Frozen inputs

- Original cross-vintage aggregate: run [#38557631541](https://github.com/DWR-debug/trading-agent-public/actions/runs/38557631541), x64 receipt fingerprint `95644cd88172dad43cb311ad5b217b4f082185fd3280f7cd5735089eb82ba8cd`, analysis fingerprint `9bff9c1b1b0da2f1415c7aabaa66a5ce97b14abd89015f9d47d61a287189e12b`.
- Existing proposal-only review of that aggregate: [#38559709707](https://github.com/DWR-debug/trading-agent-public/actions/runs/38559709707), receipt fingerprint `b0f14dc094bcc706d7bc19c64ae6f1fe5bf305bbeaaa655fc92f38c15a996531`.
- Additional R4: run [#38574180245](https://github.com/DWR-debug/trading-agent-public/actions/runs/38574180245), receipt fingerprint `8be8fd68de0324a331d2b587a540b605ac5c6e9a71ec203fa9d2fc089450fb3c`.
- Additional R5: run [#38582684174](https://github.com/DWR-debug/trading-agent-public/actions/runs/38582684174), receipt fingerprint `3d9bc88c1f43e4efac88e4528d5ac2c4b6a017beccdbe2e0e821ff150b7cd8a5`.
- Additional R6: run [#38588100012](https://github.com/DWR-debug/trading-agent-public/actions/runs/38588100012), receipt fingerprint `5571f2a8c496d32583b4b7a6bd5d6fee71533e889a5e75b434d1d84031c59522`.

The original 14-row aggregate is immutable and unchanged. R4–R6 are three separately pinned observations; they are not appended to or represented as part of that aggregate receipt. This note merely compares reported results.

## Original aggregate: 14 preselected observations

The existing validated aggregate reports:

| Check | Result |
|---|---:|
| Bulk Form 13F `FILING_DATE` differs from EDGAR header filed date | 14/14 |
| EDGAR header filed-date routes agree | 14/14 |
| Acceptance-time routes agree | 14/14 |
| `DATE-OF-FILING-DATE-CHANGE` observed | 14/14 |
| Date-change value differs from header filed date | 12/14 |
| Date-change value equals header filed date | 2/14 |

These are sample-specific descriptive counts, not prevalence estimates for the 53 unresolved accessions.

## Separately pinned observations

| Diagnostic | Archive / accession | Bulk date | EDGAR header date | Acceptance-time evidence | Date-change field evidence | Route caveat |
|---|---|---|---|---|---|---|
| R4 | `2017q2_form13f.zip` / `0001008929-17-000008` | 2017-05-31 | 2017-04-21 | Reported as 2017-05-31T14:33:43 | 2017-06-01 on index and raw SGML; absent from bounded complete-submission header prefix | All three routes agreed on accession, CIK and form; archive matched frozen size/hash pins |
| R5 | `2015q1_form13f.zip` / `0000950123-15-003183` | 2015-02-18 | 2015-02-17 | 2015-02-17T18:51:10 agreed across three routes | 2015-02-20 on index and raw SGML; absent from bounded complete-submission header prefix | All three routes completed; archive matched frozen 42,434,965-byte/SHA-256 pin |
| R6 | `2013q3_form13f.zip` / `0000950123-13-006989` | 2013-08-15 | 2013-08-14 | 2013-08-14T21:51:40 agreed across two successful routes | 2013-08-26 on raw SGML; absent from bounded complete-submission header prefix | Index-header route returned HTTP 404; raw SGML and bounded complete-submission routes succeeded; archive matched frozen 36,457,022-byte/SHA-256 pin |

Each of R4–R6 independently reports a bulk/header filing-date discrepancy, adding three further selected examples to the 14-row observation set. Taken together, the documented examples comprise 17 selected observations across seven represented archive vintages (the original five plus the new R4 2017 Q2 and R6 2013 Q3 vintages; R5 is from the already represented 2015 Q1 vintage). This is a descriptive cross-document synthesis only: the observations were not recomputed as one aggregate, and the additional cases were selected diagnostics rather than a random or population-complete sample.

## Interpretation and decision boundary

1. Preserve the bulk Form 13F date, EDGAR header filed date, acceptance timestamp, and `DATE-OF-FILING-DATE-CHANGE` as distinct source fields.
2. Do not infer that any one field universally overrides another. The repeated discrepancy supports retaining explicit provenance and discrepancy flags, not silently rewriting dates.
3. Do not infer first-public-observation time from acceptance time or the date-change field. These observations do not establish the historical availability of a filing or the first time a downstream observer could have seen it.
4. R6's HTTP 404 is a route failure, not evidence that the filing or its header did not exist.
5. Do not modify the immutable 14-row aggregate, source receipts, production join, or the frozen census. Do not restart the census.

## Remaining blockers and safety

The 53 unresolved accession keys remain unresolved; identity/source-lineage discrepancies and the historical archive/acceptance-time gates remain closed. This note does not authorize the PIT compiler, independent reproduction, performance testing, holdout selection, ranking, tuning, candidate promotion, orders, or live execution.

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`.
