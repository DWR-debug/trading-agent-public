# Q104:I19 — Expanded cross-vintage filing-date precedence review

**Review run:** [GitHub Actions #38559709707](https://github.com/DWR-debug/trading-agent-public/actions/runs/38559709707)  
**Immutable review artifact:** [q104-i19-cross-vintage-precedence-review-38559709707-1](https://github.com/DWR-debug/trading-agent-public/actions/runs/38559709707/artifacts/11891802466)  
**Review receipt fingerprint:** `b0f14dc094bcc706d7bc19c64ae6f1fe5bf305bbeaaa655fc92f38c15a996531`  
**Source analysis fingerprint:** `9bff9c1b1b0da2f1415c7aabaa66a5ce97b14abd89015f9d47d61a287189e12b`  
**Status:** `FIELD_PRECEDENCE_REVIEW_PROPOSAL_READY_NOT_APPLIED`

## Frozen evidence chain

The review validates both immutable outputs of Candidate Next-Gate Wave [#38557631541](https://github.com/DWR-debug/trading-agent-public/actions/runs/38557631541):

- Ubuntu x64 aggregate receipt fingerprint: `95644cd88172dad43cb311ad5b217b4f082185fd3280f7cd5735089eb82ba8cd`.
- Ubuntu ARM64 independent reproduction receipt fingerprint: `1b9236ed4848b51016426e6a9ad6e1623ea318c9455f66f70736286e602cc8cf`.
- Both reproduced analysis fingerprint: `9bff9c1b1b0da2f1415c7aabaa66a5ce97b14abd89015f9d47d61a287189e12b`.
- The aggregate retains the prior R1/R2 date-change header probe and the pinned R3 lineage receipt. The review fetched no SEC data; it read only these two workflow artifacts.

## Observed result

Across the 14 preselected observations spanning five archive vintages:

| Check | Result |
|---|---:|
| Bulk Form 13F date differs from EDGAR header date | 14/14 |
| EDGAR header filed-date routes agree | 14/14 |
| Acceptance-time routes agree | 14/14 |
| `DATE-OF-FILING-DATE-CHANGE` observed | 14/14 |
| Date-change value differs from header filed date | 12/14 |
| Date-change value equals header filed date | 2/14 |

This is a consistent source-field discrepancy pattern in the selected sample, not an estimate of prevalence across the full unresolved population.

## Review proposal — not applied

1. Keep EDGAR `ACCEPTANCE-DATETIME` as a distinct event clock only after exact accession, CIK and form identity validation plus cross-route agreement.
2. Preserve the bulk Form 13F `FILING_DATE` unchanged as source provenance.
3. Preserve the consistent EDGAR header/index filed date as a separate field and attach an explicit discrepancy flag when it differs from the bulk value.
4. Retain `DATE-OF-FILING-DATE-CHANGE` as separate post-acceptance-change metadata. Do not substitute it for acceptance time or silently overwrite either filed-date source.
5. Apply no date shifting, timezone arithmetic, imputation, or blanket correction.

## Decision boundary and next gate

This is a proposal-only review. `source_precedence_applied=false`, `production_join_changed=false`, `source_receipts_modified=false`, `acceptance_time_gate_cleared=false`, and `historical_archive_gate_cleared=false`.

The 14 rows do not cover the exact 53 unresolved accessions and do not close the distinct CIK/form/date identity conflicts, missing historical source records, or first-public-observation requirements. Before any production join change, separately review and test the proposed policy against the exact residual population and its source-vintage conflicts. The historical archive/PIT, performance, holdout-selection, ranking, tuning, promotion and live-execution gates remain closed.

`PAPER_ONLY=true`; live trading, orders and automatic promotion remain disabled.
