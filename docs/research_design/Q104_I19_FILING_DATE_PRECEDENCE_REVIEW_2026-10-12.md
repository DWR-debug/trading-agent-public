# Q104:I19 filing-date precedence review — preregistration

Registered 2026-10-12 20:40 UTC. Review-only analysis of header probe run #38304249742 (receipt fingerprint 17fa46e3f49b4bb296122a1f6e80b7fbe7e3c134868803b2ddb910f898521412), linked to R1 fingerprint c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7 and R2 fingerprint d85ad092296b38f29fa25147537f52804f9a32d9969051c7f9e9cadff283fe04.

## Official source semantics

The SEC EDGAR PDS Technical Specification (https://www.sec.gov/info/edgar/pdsdissemspec051310.pdf) defines FILED AS OF DATE as the EDGAR-assigned official filing date, or a post-acceptance new filing date in a post-acceptance correction. DATE AS OF CHANGE / DATE-OF-FILING-DATE-CHANGE is the date when the last post-acceptance event occurred; the field is optional. They are distinct fields.

## Frozen observations

Eight preselected accessions from 2015, 2017, 2020, and 2025 were checked through three SEC header routes each:
- bulk Form 13F FILING_DATE differs from EDGAR header filing date in 8/8;
- accession, filer CIK and form agree across routes in 8/8;
- EDGAR header filing date and ACCEPTANCE-DATETIME agree across routes in 8/8;
- DATE-OF-FILING-DATE-CHANGE agrees between index headers and raw SGML header in 8/8;
- the change date equals header filing date in 2/8 and differs in 6/8.

## Review proposal — not applied

1. Use EDGAR ACCEPTANCE-DATETIME as the acceptance-event clock after exact accession/CIK/form validation and cross-route agreement.
2. Where bulk Form 13F FILING_DATE conflicts, retain the bulk value unchanged and use the EDGAR header/index filed date as the filed-date field, with an explicit discrepancy flag.
3. Preserve DATE-OF-FILING-DATE-CHANGE as separate post-acceptance metadata; never substitute it for filing date or acceptance timestamp.
4. Do not use date arithmetic, infer a fixed offset, or silently rewrite historical source fields.

The eight-row pattern does not establish prevalence across every unresolved accession. This review does not change the production join, clear the acceptance-time or historical archive gate, or authorize performance, tuning, promotion, orders, or live execution. A separately reviewed implementation must be tested on the exact residual population before any gate can be reconsidered.
