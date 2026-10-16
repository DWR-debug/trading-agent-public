# Q221 — Common Crawl index metadata result R1

**Source run:** [#38902507051](https://github.com/DWR-debug/trading-agent-public/actions/runs/38902507051)  
**Observation date:** 2026-10-16  
**Preregistration:** `research/preregistrations/q221_fpds_commoncrawl_index_metadata_probe_r1_2026_10_16.json`  
**Immutable receipt:** `research/evidence/q221_fpds_commoncrawl_index_metadata_attempt_38902507051.json`  
**Receipt Git blob SHA-1:** `a1a06fcc646c26babf75cb982d276e4cb5165fe2`  
**Receipt fingerprint:** `f5e147f3d1be28424f3236fb85fe89f77720f357e1b1c50edef2abb55776e1d0`  
**Analysis fingerprint:** `6fb6a46ed003c24a02b9623d03a50d98f4a0e9609215ecf9b5e25b8fbb14a98e`  
**Disposition:** `INDEX_METADATA_ROUTE_INCOMPLETE; NO_ARCHIVE_ABSENCE_INFERENCE`

## 1. Execution integrity

The one-shot probe validated all frozen inputs and passed its mandatory offline tests before source access. It then attempted exactly four metadata-only HTTPS requests, one for each frozen FPDS Atom URL in a pre-selected Common Crawl collection that predates the matching transaction action date. The receipt and independent offline receipt validation were persisted successfully.

The overall GitHub Actions run is marked failed because the preregistered source outcome was incomplete. It was not a preflight failure: the capture step ran after preflight succeeded and recorded the four attempts.

## 2. Per-query observations

| Frozen record | Crawl collection | HTTP status | Query completed | Capture metadata rows |
|---|---|---:|---|---:|
| CACI 2019 | `CC-MAIN-2018-51` | 504 | No | 0 |
| Booz Allen 2020 | `CC-MAIN-2019-51` | 504 | No | 0 |
| OSI / American Science & Engineering 2023 | `CC-MAIN-2022-49` | 504 | No | 0 |
| Northrop Grumman 2024 | `CC-MAIN-2023-50` | 503 | No | 0 |

All four responses contributed zero counted body bytes. No response bodies were persisted. The run issued no FPDS origin requests, Wayback requests, Arquivo.pt requests, SAM.gov API requests, USAspending requests, SEC requests, Common Crawl WARC range requests, or WARC payload downloads. No retries or redirects were used.

## 3. Interpretation and route disposition

This is an **index service availability failure**, not a completed lookup with an empty result. The queries completed 0/4 times, so the receipt provides no exact-URL capture/no-capture conclusion for any of the four collections.

Do not retry this frozen R1 request contract or fetch WARC bytes on its basis. Any genuinely different source/query contract would require a new, independently reviewed preregistration and a concrete reason why it is materially different; it must not be created merely to repeat a failed route or keep runners busy.

Even a future successful index match would establish only that Common Crawl indexed a URL during a crawl window. It would not establish that the captured response contained the frozen PIID/modification/action-date/recipient tuple, nor that the crawl timestamp was the transaction's true first-public time. Payload inspection would require separate preregistration.

## 4. Q221 gates and safety remain unchanged

- The frozen population remains 348 transaction rows; no transaction keys or source hashes were modified.
- Historical first-public-observation time remains unproven for 348/348 rows.
- Recipient-to-issuer mapping remains unfrozen for 247 distinct recipient candidates.
- Transaction-class applicability, correction lineage and agency-specific publication-delay checks remain open.
- No source rows or historical receipts were rewritten.
- `paper_only=true`; live trading and orders remain disabled.
- Performance authorization, holdout selection, ranking, tuning, promotion and live execution remain false.

## References

- Common Crawl, [CDXJ Index documentation](https://commoncrawl.org/cdxj-index).
- Common Crawl, [Get Started / crawl collections](https://commoncrawl.org/get-started).
- Immutable source run [#38902507051](https://github.com/DWR-debug/trading-agent-public/actions/runs/38902507051).
- [SAM.gov public-delta source feasibility adjudication](https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q221_SAM_PUBLIC_DELTA_SOURCE_FEASIBILITY_ADJUDICATION_R1_2026-10-16.md).
- [Arquivo.pt TimeMap R2 result adjudication](https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q221_ARQUIVO_PT_FPDS_TIMEMAP_R2_RESULT_2026-10-16.md).
- [Wayback CDX empty-result adjudication](https://github.com/DWR-debug/trading-agent-public/blob/master/docs/research_design/Q221_FPDS_WAYBACK_CDX_EMPTY_RESULT_ADJUDICATION_R1_2026-10-16.md).
