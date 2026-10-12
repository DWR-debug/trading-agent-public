# Q104:I19 date-change header probe — preregistration

Registered 2026-10-12 20:10 UTC. This is a small, header-only follow-up to the completed R1 and R2 cross-vintage source-lineage diagnostics. It is specifically intended to capture DATE-OF-FILING-DATE-CHANGE where present before any field-precedence proposal.

## Immutable inputs

- R1 run #38255701998, receipt fingerprint c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7.
- R2 run #38301876992, receipt fingerprint d85ad092296b38f29fa25147537f52804f9a32d9969051c7f9e9cadff283fe04.
- The exact eight accession keys, filer CIKs, forms, and frozen bulk FILING_DATE values are embedded in automation/q104_i19_filing_date_change_header_probe.py and checked against both immutable source receipts before any new SEC request.

## Method and bounds

- Reuse only the R1/R2 artifact receipts; do not re-download either SEC bulk archive.
- Query three SEC header routes for each of the eight frozen accessions: index headers, raw .hdr.sgml, and the bounded complete-submission header prefix.
- Capture accession, filer CIK, form, FILING-DATE / FILED AS OF DATE, ACCEPTANCE-DATETIME, and DATE-OF-FILING-DATE-CHANGE where present.
- Exactly 24 requests; 262,144 bytes maximum per response; 8,000,000 bytes aggregate response-body budget; 30-second timeout and one-second request spacing.
- Absence of DATE-OF-FILING-DATE-CHANGE in captured headers is reported as not observed, not proof that no post-acceptance change ever occurred.
- No date arithmetic, field precedence, receipt repair, census restart, performance, holdout selection, ranking, tuning, promotion, orders, or live execution.

## Decision boundary

The probe can inform a separate field-precedence review. It cannot by itself clear the acceptance-time gate or establish historical public-observation time.
