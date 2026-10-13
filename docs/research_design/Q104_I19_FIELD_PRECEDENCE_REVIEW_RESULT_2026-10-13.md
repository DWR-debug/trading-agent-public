# Q104:I19 — Filing-date precedence review result

**Observed:** 2026-10-13  
**Review run:** [GitHub Actions #38436121787](https://github.com/DWR-debug/trading-agent-public/actions/runs/38436121787)  
**Immutable artifact:** [q104-i19-filing-date-precedence-review-38436121787-1](https://github.com/DWR-debug/trading-agent-public/actions/runs/38436121787/artifacts/11833545960)  
**Receipt fingerprint:** `2347965c6e1501510c63dd74b24f72976d09dec00dde57acddb490123a2df043`  
**Status:** `FIELD_PRECEDENCE_REVIEW_PROPOSAL_READY_NOT_APPLIED`

## Frozen evidence chain

The review consumes the immutable header probe from run #38304249742 and retains the frozen R1 and R2 receipt fingerprints:
- R1: `c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7`
- R2: `d85ad092296b38f29fa25147537f52804f9a32d9969051c7f9e9cadff283fe04`
- Header probe: `17fa46e3f49b4bb296122a1f6e80b7fbe7e3c134868803b2ddb910f898521412`

## Observed result

Across all eight preselected rows:
- Bulk Form 13F filing date differs from EDGAR header filed date: **8/8**.
- Accession/CIK identity routes agree: **8/8**.
- Filed-date routes agree across index header, raw SGML header, and complete submission header prefix: **8/8**.
- Acceptance-time routes agree: **8/8**.
- `DATE-OF-FILING-DATE-CHANGE` differs from the header filed date in **6/8** and equals it in **2/8**.

## Review proposal — not applied

The receipt proposes that an accepted policy keep the EDGAR `ACCEPTANCE-DATETIME` as a separate event clock after exact accession/CIK/form validation, retain the bulk field unchanged for provenance, and represent any EDGAR header/index filing-date disagreement with an explicit discrepancy flag. `DATE-OF-FILING-DATE-CHANGE` remains separate metadata. No date shifting, imputation, or blanket correction is proposed.

**No operational rule or receipt was changed by this run.** `source_precedence_applied=false`, `acceptance_time_gate_cleared=false`, `historical_archive_gate_cleared=false`; performance, holdout selection, ranking, tuning, promotion, and live execution remain false. Eight observations do not establish prevalence across the 53 residual accessions; any production use requires separate review and validation against the exact residual population.
