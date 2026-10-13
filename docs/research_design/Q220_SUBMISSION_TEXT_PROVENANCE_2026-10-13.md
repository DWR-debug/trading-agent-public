# Q220 — Complete SEC submission text provenance probe

**Registered:** 2026-10-13  
**Purpose:** distinguish the frozen primary-document byte representation from the complete SEC submission-text file for exactly one pre-registered SPGI filing. This is one-accession source provenance, not a source-population repair or PIT/performance gate.

## Frozen target and prior evidence

- CIK/accession/form/filed: 0000064040 / 0000064040-19-000059 / 10-K / 2019-02-13
- Primary filename: spgi-20181231x10k.htm
- Frozen primary SHA-256: 27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83
- Frozen primary length: 4,774,458 bytes
- Previous captured SHA-256: 08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb
- Previous single-feed extracted body SHA-256: aa1f89efdf13029de9dd8f7eb020502dd518d4350513d4ef041ba67d902ef368 (4,774,237 bytes)
- Frozen fixture blob/fingerprint: 2a3abbff6c6950e4f11d85dba92cb9c57a5c7ee0 / c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075
- Frozen 55-row population fingerprint: 158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543
- Prior single-feed summary blob SHA: 807f6796a0f84b27ab04160e944bdfdaec85525b; upstream receipt fingerprint fe98cecb579d15ecf6e48c3b84a3a699345bf840745e9be0c7cfcd972aebf03a

## Distinct source path and strict byte ceilings

The diagnostic reads only the SEC filing-index HTML, the exact complete-submission text URL, and the current primary HTML. The official filing index reports the following size metadata:
- Primary HTML: 4,774,347 bytes
- Complete submission text file: 26,429,931 bytes

Source links: [official SEC filing index](https://www.sec.gov/Archives/edgar/data/64040/000006404019000059/0000064040-19-000059-index.html), [complete submission text](https://www.sec.gov/Archives/edgar/data/64040/000006404019000059/0000064040-19-000059.txt), [current primary HTML](https://www.sec.gov/Archives/edgar/data/64040/000006404019000059/spgi-20181231x10k.htm).

Hard response limits:
- Filing index: 250,000 bytes
- Complete submission text: 30,000,000 bytes
- Current primary HTML: 8,000,000 bytes
- Aggregate transferred bytes, including failed retry attempts: 80,000,000 bytes
- Existing bounded SEC retry helper only; no loop until success.
- No daily Feed, annual/quarterly bulk archive, additional accession, or broad census.

## Interpretation and stop rule

The probe validates both pinned upstream receipts before networking; then it records response hashes/lengths/Last-Modified, index row uniqueness and stated sizes, exact accession/CIK/form/filed-date header values, extracted primary-body variants, and matches against the frozen hashes. It never persists or commits downloaded bodies.

A completed comparison is not a positive Q220 result. No source hash is updated automatically. If none of the variants matches, do not repeat the already scanned 865.8 MB daily Feed; the next engineering task must explain the historical hash-capture provenance from a distinct pinned artifact or extraction path. Q220 remains blocked until all 55 source hashes and strict PIT lineage are independently reconciled.

The population fingerprint, source sample, acceptance-time ordering, historical public-observation gate, issuer mappings, and all scientific/performance/holdout/ranking/tuning/promotion/live-execution gates remain unchanged. Paper-only remains mandatory.
