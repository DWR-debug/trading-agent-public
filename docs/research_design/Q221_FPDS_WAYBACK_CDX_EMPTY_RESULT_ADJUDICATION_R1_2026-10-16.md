# Q221 — adjudication of the R1 Wayback CDX empty-array responses

**Adjudication date:** 2026-10-16  
**Source run:** https://github.com/DWR-debug/trading-agent-public/actions/runs/38900486932  
**Immutable source receipt:** research/evidence/q221_fpds_wayback_cdx_metadata_attempt_38900486932.json  
**Receipt SHA-256 fingerprint:** 84dc038f080aafbbedb5338fa66a77781fe10619fbb1aad6e750345e6d4ca39b  
**Receipt Git blob SHA-1:** 844dd2da40c9ca32adfccb1c2a4d2bcea590af86

## Observed result

The one-shot metadata probe made exactly four requests to https://web.archive.org/cdx/search/cdx, one for each frozen exact FPDS Public Atom URL. Each response was HTTP 200 with Content-Type application/json, a consumed response length of 3 bytes, and SHA-256 37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570. An offline hash comparison confirms that fingerprint matches the three-byte candidate byte sequence [] followed by a newline. Raw response bodies were not persisted, so this adjudication is based on the recorded byte counts/digests and the pinned upstream writer behavior—not on newly downloaded content.

The original parser expected a field-name header row even when no rows were returned. It consequently wrote the immutable source receipt as Q221_WAYBACK_CDX_METADATA_INCOMPLETE / Q221_WAYBACK_CDX_SCHEMA_INCOMPLETE. That status remains in the original receipt and is not rewritten.

## Upstream format adjudication

The official Wayback CDX README explains that output=json returns a JSON array with a leading CDX field header when result rows are present and that url must be URL-encoded when the original URL contains a query string. The upstream implementation is more specific for the zero-row case: in wayback-cdx-server/src/main/java/org/archive/cdxserver/writer/JsonWriter.java, Git blob 07de0ce22232e9af9802086d25a253fddf088b11, begin() emits [, the header is emitted from writeLine() only when a result row arrives, and end() emits ] plus a newline. Zero result rows therefore serialize as [] followed by a newline without the field header.

That implementation, together with the matching response-body hash for all four requests, supports interpreting the four responses as valid empty CDX result arrays, not transport errors and not malformed JSON. The corrected parser and regression test now recognize that output shape. This code correction is offline-only; it does not rerun or repeat the consumed R1 requests.

## Narrow interpretation

The defensible finding is: at the time of R1, the CDX index returned no captures for these four exact encoded original URLs. It does not establish that the transaction data were historically absent, that alternate query spellings or record-detail URLs were never archived, or that no other source/publication route existed. No capture timestamp or archived transaction payload was available to inspect.

No Wayback replay, FPDS origin, Arquivo.pt, SAM.gov, USAspending, SEC, or Common Crawl request was made in this adjudication. The 348-row population and every frozen transaction key are unchanged. Historical first-public time remains unproven for 348/348 rows, and 247 recipient-to-issuer mappings remain unfrozen. Paper-Only remains enforced; performance, holdout, ranking, tuning, promotion and live-execution gates remain closed.

## References

- Internet Archive, Wayback CDX Server API documentation: https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md
- Internet Archive, upstream JSON writer implementation: https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/src/main/java/org/archive/cdxserver/writer/JsonWriter.java
- R1 source run #38900486932: https://github.com/DWR-debug/trading-agent-public/actions/runs/38900486932
- R1 persisted receipt: https://github.com/DWR-debug/trading-agent-public/blob/master/research/evidence/q221_fpds_wayback_cdx_metadata_attempt_38900486932.json

