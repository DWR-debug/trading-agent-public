# Q104:I19 — Four-key residual filing-date lineage result

**Observation run:** [GitHub Actions #38255701998](https://github.com/DWR-debug/trading-agent-public/actions/runs/38255701998)  
**Immutable receipt fingerprint:** \`c0881b295d37fa34925103b30acbb893a78bbbe230af6e637576dfda4fac86f7\`  
**Status:** \`LINEAGE_DIAGNOSTIC_COMPLETE\`; diagnostic completeness is not acceptance-time-gate clearance.

## What was validated

The probe reused source census run #38168441086 and validated both archived shard receipt canonical fingerprints and the frozen SEC source-page SHA-256. The two quarterly 13F ZIPs were downloaded within the 150 MB aggregate ceiling and matched the exact byte lengths and SHA-256 pins stored in the immutable census receipts:

| SEC archive | Bytes | SHA-256 matched |
|---|---:|---|
| \`2015q1_form13f.zip\` | 42,434,965 | Yes |
| \`2020q3_form13f.zip\` | 49,051,852 | Yes |

Four pre-registered accession rows were read from the verified \`submission.tsv\`; three independent SEC header routes were captured for each. All 12/12 probes returned usable observations. Each sample's accession, filer CIK, and form agreed across the source row and all three EDGAR routes. Each route yielded an \`ACCEPTANCE-DATETIME\`.

| Accession | Frozen bulk \`FILING_DATE\` | EDGAR header date | EDGAR acceptance datetime |
|---|---|---|---|
| \`0000950123-15-003104\` | 2015-02-18 | 2015-02-17 | 2015-02-17 17:55:54 |
| \`0000950123-15-003463\` | 2015-02-18 | 2015-02-17 | 2015-02-17 21:39:45 |
| \`0001800724-20-000002\` | 2020-08-10 | 2020-08-07 | 2020-08-07 17:59:18 |
| \`0001800724-20-000003\` | 2020-08-10 | 2020-08-07 | 2020-08-07 18:17:45 |

The discrepancy is therefore specifically a cross-publication disagreement over filing-date metadata in these four verified rows, not a disagreement over accession, filer CIK, form, or the observed acceptance timestamp. This four-key sample does not establish a rate for the remaining 49 accessions.

## Interpretation boundary

The SEC's [Form 13F Data Sets readme](https://www.sec.gov/files/form_13f_readme.pdf) describes \`SUBMISSION.FILING_DATE\` as the filing date with the Commission sourced from EDGAR, but also warns that the quarterly data may contain inaccuracies or compilation errors and may disagree with other publication formats; it says the dataset is not a substitute for the underlying filing (sections 1 and 5.1).

The SEC's [EDGAR Public Dissemination Subsystem specification](https://www.sec.gov/files/info/edgar/specifications/pds_dissemination_spec.pdf) describes \`<FILING-DATE>\` as the EDGAR-assigned official filing date (including a post-acceptance new filing date). The official SEC filing detail page for another residual accession in the 2015 Q1 cluster, [0000950123-15-003279](https://www.sec.gov/Archives/edgar/data/923093/000095012315003279/0000950123-15-003279-index.htm), displays Filing Date 2015-02-17 and Accepted 2015-02-17 19:43:40. These sources demonstrate why the discrepancy deserves field-level analysis; they do not justify silently rewriting the frozen receipts or assuming a blanket date-conversion rule.

## Required next step and gates

Perform one more bounded diagnostic on a pre-registered sample from another archive vintage and capture any available \`DATE-OF-FILING-DATE-CHANGE\` field plus the filing-detail page values. Only after that evidence is independently checked should a separate reviewed proposal define field precedence or a revised discrepancy classification.

Until then, preserve every immutable receipt, all 53 residual accession outcomes, and the acceptance-time and historical-archive gates. Do not repair or retry those rows from this diagnostic alone; do not restart the full census; do not begin the PIT compiler or independent reproduction. Performance authorization, holdout selection, ranking, tuning, promotion, orders, and live execution remain disabled.
