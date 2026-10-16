# Q221 — Arquivo.pt Memento TimeMap metadata probe

**Registered:** 2026-10-16  
**Stage:** bounded archive metadata feasibility only; not transaction-row evidence, historical PIT clearance, or performance authorization.

## Why this route is distinct

The four fixed Q221 source-feasibility records were already queried once against the legacy FPDS Public Atom route. All four calls returned HTTP 302 and the no-redirect policy blocked them. The same records are reused here; the sample is not expanded.

The SAM.gov Contract Awards API remains a conditional lead because current documentation requires an API key and does not establish retrievable prior public versions or a record-level first-public timestamp. The official USAspending monthly archive inventory found no multi-date archive series for the seven frozen target fiscal years. A separate Common Crawl exact-URL metadata route used for another candidate returned HTTP 504 for all four lookups; its run record says not to blindly retry the same route.

Arquivo.pt documents a Memento TimeMap endpoint that returns archived URL versions and provides newline-delimited JSON metadata:
https://dados.gov.pt/en/datasets/memento-api-url-search

This makes it an independent bounded archive-index feasibility lead, not a known working source for these FPDS records.

## Frozen query contract

The one-shot workflow is bound to the immutable Q221 public-boundary manifest, pre-event identity-feasibility receipt, and prior four-record FPDS probe. It queries the exact four FPDS Atom URLs already registered in that probe, once each, in sequence. It does not issue requests to FPDS, SAM.gov, USAspending, SEC, Common Crawl, or the previously used Wayback service.

The procedure is metadata-only:
- HTTPS GET requests to the Arquivo.pt TimeMap endpoint using each fully percent-encoded exact original URL.
- Four archive-index requests at most; no retries; no redirects; 35-second timeout; at least one second between request starts.
- Maximum 500,000 response bytes per query and 2,000,000 aggregate response bytes.
- TimeMap JSON lines are parsed in memory. Only timestamp, indexed original URL, source HTTP status, MIME/digest/length metadata, and presence of archive byte-range coordinates are retained.
- No archived replay URL is opened, no original source content is downloaded, and no raw TimeMap response body is persisted. Response byte count and SHA-256 are retained for provenance.
- Any immutable-input mismatch blocks before the first source request. Transport, HTTP, schema, and response-limit errors produce a fail-closed receipt.

## Interpretation rules

A successful response means only that the archive metadata query completed under the fixed schema. An exact-original-URL capture is a candidate for a possible second, separately preregistered replay inspection. It does not establish that the archived feed contains an exact transaction tuple until that tuple is inspected.

A capture timestamp is when Arquivo.pt observed the URL, not the transaction’s true first-public timestamp. No returned captures do not prove the transaction was absent from the archive at every time, nor do they prove that it was historically unavailable on other public channels. Redirects, 404s, 5xx responses, timeouts, and malformed metadata are incomplete outcomes, not no-hit outcomes. This route is one-shot and must not be retried without a new, separately reviewed contract.

The 348-row Q221 sample, all transaction keys, the 247 unmapped recipient candidates, transaction-class applicability rules, agency exceptions, source receipts, and expected hashes are unchanged. Historical first-public observation, event-level public boundary, recipient-to-issuer mapping, scientific evidence, performance authorization, holdout selection, ranking, tuning, promotion, and live execution remain false.

## Sources and prior evidence

- Arquivo.pt Memento TimeMap endpoint documentation: https://dados.gov.pt/en/datasets/memento-api-url-search
- Prior four-record FPDS Atom receipt: https://github.com/DWR-debug/trading-agent-public/blob/master/research/evidence/q221_fpds_public_atom_identity_bridge_latest.json
- SAM.gov source-feasibility adjudication: https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q221_SAM_PUBLIC_DELTA_SOURCE_FEASIBILITY_ADJUDICATION_R1_2026-10-16.md
- USAspending monthly archive inventory result: https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q221_MONTHLY_ARCHIVE_INVENTORY_RESULT_2026-10-13.md
- Common Crawl exact-index route failure: https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q127R3_COMMONCRAWL_INDEX_FAILURE_2026-10-14.md
