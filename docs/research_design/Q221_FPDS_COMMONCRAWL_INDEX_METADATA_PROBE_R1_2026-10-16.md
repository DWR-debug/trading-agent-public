# Q221 — Common Crawl pre-event URL-index metadata probe R1

**Study mode:** one-shot, pre-event archive index metadata only  
**Sequence:** Q221-CC-INDEX-R1-20261016-A  
**Request budget:** exactly four requests at most; one per frozen transaction key  
**State:** preregistered; not yet executed

## Rationale

The recent Wayback CDX lookup returned empty result arrays for four exact FPDS Atom feed-query URLs, and the Arquivo.pt TimeMap probe failed with HTTP 404. These are route-specific negative findings, not evidence that the transaction history never appeared elsewhere. The SAM.gov API-key preflight found no configured key, so this probe uses another independent public archive index rather than assuming credentials.

Each URL is queried only in a named Common Crawl collection whose official crawl window falls before the frozen transaction action date:
- CACI / action date 2019-01-03: `CC-MAIN-2018-51`, crawl window 2018-12-09 to 2018-12-19.
- Booz Allen / action date 2020-01-02: `CC-MAIN-2019-51`, crawl window 2019-12-05 to 2019-12-16.
- OSI / ASE / action date 2023-01-03: `CC-MAIN-2022-49`, crawl window 2022-11-26 to 2022-12-10.
- Northrop / action date 2024-01-02: `CC-MAIN-2023-50`, crawl window 2023-11-28 to 2023-12-12. The Common Crawl release post explicitly gives that final window.

The published collection IDs are listed by Common Crawl's Get Started page; the CDXJ Index page describes the capture-index record fields and the separately required WARC range operation. This workflow stops at index metadata.

## Frozen bounded method

Exactly one HTTPS GET is planned for each exact frozen original URL against its pre-selected collection index. Each query requests the Common Crawl CDXJ JSON-line metadata format and explicitly asks for exact URL matching. There is no prefix/host/domain expansion and no additional record IDs.

- Four requests maximum; no retries and no redirects.
- Maximum 512 KiB per response and 2 MiB total; 45-second timeout and at least one second between request starts.
- Only bounded metadata fields (URL, crawl timestamp, HTTP status, MIME, digest, WARC record length/offset and filename) plus response length/hash are retained. Raw response bodies are not persisted.
- No FPDS origin requests, Wayback/Arquivo.pt/SAM.gov/SEC/USAspending requests, WARC range requests or payload downloads.

## Interpretation limits

A Common Crawl timestamp is when the URL was crawled by Common Crawl, not necessarily the first time the transaction became public. A valid empty response is no row returned for that exact URL in that collection only; it is not proof of historical absence elsewhere. HTTP errors, malformed JSONL, oversized responses, non-exact original URLs, and records belonging to any other collection are incomplete results, not no-hit.

Index metadata alone does not prove that the archived FPDS response contained the frozen transaction tuple. If any capture is found, inspecting a WARC record must be separately preregistered and reviewed. This R1 has no permission to retrieve WARC bytes. The frozen 348-row population, all transaction keys and all recipient identity fields remain unchanged. Historical first-public time remains unproven for 348/348 rows; 247 recipient-to-issuer mappings remain unfrozen. Paper-Only remains enforced, and no performance, holdout, ranking, tuning, promotion or live execution is authorized.

## References

- Common Crawl, [CDXJ Index](https://commoncrawl.org/cdxj-index).
- Common Crawl, [Get Started / available crawl collections](https://commoncrawl.org/get-started).
- Common Crawl, [November/December 2023 Crawl Archive Now Available](https://commoncrawl.org/blog/november-december-2023-crawl-archive-now-available).
