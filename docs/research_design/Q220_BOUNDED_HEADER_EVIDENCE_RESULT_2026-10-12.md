# Q220 — Completed bounded header-only timestamp evidence

**Run:** [GitHub Actions #38258251764](https://github.com/DWR-debug/trading-agent-public/actions/runs/38258251764)  
**Immutable receipt fingerprint:** \`39bf95fa15bf149094d5b56c90e58622c2339d452fd138c6deb0a463668f85b4\`  
**Diagnostic state:** \`HEADER_EVIDENCE_COMPLETE\` — this is supplemental timestamp evidence, not source-vintage proof.

## Frozen input and bounds

The run validated and read the exact Q220 post-fix forensic receipt from #38254139755 (source receipt fingerprint \`840f280cbcb1fdbe4b2fbaa88f8d7f02edf447799e13fe0171d37fcd57f3221b\`; source population fingerprint \`158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543\); 55 expected-versus-observed primary-document hash disagreements). It then fetched only nine official EDGAR header routes for the three already-frozen accessions. Total transferred bytes were 101,547 against a 3,000,000-byte cap. No daily Feed archive or primary filing document was downloaded.

All 9/9 header routes returned usable observations. For each fixed sample, accession, CIK, form and EDGAR filing date agreed across the index-header page, raw \`.hdr.sgml\` and the complete-submission header prefix. All three routes reported the same \`ACCEPTANCE-DATETIME\` per accession. The parser also captured \`DATE-OF-FILING-DATE-CHANGE\`.

| Accession | EDGAR filing date | Acceptance datetime | Date of filing-date change |
|---|---|---|---|
| \`0000064040-19-000059\` | 2019-02-13 | 2019-02-12 18:15:22 | 2019-02-12 |
| \`0001564590-19-003382\` | 2019-02-20 | 2019-02-20 12:18:53 | 2019-02-20 |
| \`0000064040-25-000052\` | 2025-02-11 | 2025-02-11 17:29:21 | 2025-02-11 |

The first sample demonstrates a filing accepted on the prior evening with a next-calendar-day official filing date, while the other two were accepted and filed on the same calendar date. This is useful metadata context for reviewing historical filing-date discrepancies, but these three filings are not the same population as the 53 Q104 residuals and do not establish a Q104-wide rule.

## Decision boundary

The result clears neither Q220 gate: the acceptance-time/source-vintage gate remains closed, and the 55 frozen primary-document hash mismatches remain unresolved. A matching EDGAR acceptance timestamp does not reconcile a primary-document byte hash or establish that a hash pin points to the right source vintage.

Next, compare the frozen expected and observed primary-document hash lineage and identify the originating source artifact/version before any source-vintage policy proposal. Do not redownload the three multi-GB Feed archives, fetch primary documents for this timestamp question, rewrite any expected hash, or change the frozen sample keys, population fingerprint, or gate criteria. Paper-only execution remains mandatory.
