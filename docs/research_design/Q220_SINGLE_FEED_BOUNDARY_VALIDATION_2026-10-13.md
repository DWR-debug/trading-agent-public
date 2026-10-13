# Q220 — Single frozen SEC Feed boundary validation

**Registered:** 2026-10-13  
**Purpose:** verify the corrected EDGAR TEXT extraction boundary against one previously completed and identity-validated daily-feed sample. This is a source-parser diagnostic only, not a PIT or trading-evidence gate.

## Frozen sample

- CIK: 0000064040
- Accession: 0000064040-19-000059
- Form / filed date: 10-K / 2019-02-13
- Primary: spgi-20181231x10k.htm
- Original frozen SHA-256: 27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83
- Frozen document length: 4,774,458 bytes
- Frozen input receipt blob: 2a3abbff6c6950e4f11d85dba92cb9c57a5c7ee0
- Frozen source receipt fingerprint: c7fc53c9ef2daaef9caee29c0ba1084602c0bf4b24c6d2a13cb812b7b592c075
- Source population fingerprint: 158e84963e7fe4a8d32f91939011a6b23dfdbf7fcec0eeca2cb97be56634f543

## Hard source and compute limits

- Exactly one current primary-document request and one daily Feed archive URL.
- Feed archive maximum: 900,000,000 bytes.
- Aggregate HTTP download maximum, including any failed retry bytes: 950,000,000 bytes.
- Current primary maximum: 15,000,000 bytes.
- Extracted primary maximum: 30,000,000 bytes.
- Original submission wrapper maximum: 150,000,000 bytes.
- Total uncompressed tar member bytes scanned: 12,000,000,000 bytes.
- Existing SEC retry policy only; no annual/quarterly archive, no other accession, and no retry-until-success behavior.
- The feed's previously observed Content-Length was 865,768,653 bytes.

## Interpretation and stop rules

The receipt records the current direct document, one daily Feed tar, exact member identity, complete scan status, closing-tag count/offset, and exact SHA-256 match variants. It does not persist the downloaded archive or primary body. No match means stop and retain the blocked state; one match supports only this one accession's byte provenance and triggers separate review before any population-level action. A complete run is not a positive Q220 research result.

This single-sample diagnostic cannot change any of the 55 frozen primary hashes, population membership, expected bytes, filing identity rules, compiler state, historical acceptance-time logic, or research gates. The expected SHA-256 is never replaced automatically. No performance, holdout selection, ranking, tuning, promotion, order, or live execution is authorized. Paper-only remains mandatory.
