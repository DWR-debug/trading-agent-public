# Q221 — Arquivo.pt TimeMap R2 result adjudication

**Source run:** [#38869362949](https://github.com/DWR-debug/trading-agent-public/actions/runs/38869362949)  
**Observation date:** 2026-10-16  
**R2 preregistration:** `research/preregistrations/q221_arquivo_pt_fpds_timemap_probe_r2_2026_10_16.json`  
**Receipt:** `research/evidence/q221_arquivo_pt_fpds_timemap_r2_attempt_38869362949.json`  
**Receipt Git blob SHA-1:** `d0d56836c4356977dfa37e515ffe2516b1e7c6d9`  
**Receipt fingerprint:** `a5bb1aee620768f71bad7f05fd8af5ac123b6fe87230bd9df538999640438403`  
**Analysis fingerprint:** `9894fdd5c28aa69c1b58164b9b45eb758bfd73cb5772c7a71b2426cd6f6d2eb1`  
**Disposition:** `METADATA_ROUTE_UNAVAILABLE_FOR_FROZEN_URLS; NO_ARCHIVE_ABSENCE_INFERENCE`

## 1. Execution integrity

R1 (#38863558147) failed before source access because the runner had no `pytest` module. Its immutable receipt records zero TimeMap requests, zero observations, and `PREFLIGHT_FAILED_NO_SOURCE_REQUESTS`. R2 was separately preregistered and pinned that exact R1 receipt before dispatch.

R2's one-shot guard, offline tests (12 passed), and immutable-input preflight succeeded. All four source-query attempts then ran once. The receipt and independent offline verification were persisted successfully; offline validation is `VALIDATED` with fingerprint `b908889d9483eed5b7ba1b2b91390aa3b46f4788e4878bf8800cdd91e639b880`. The workflow's overall run is marked failed because the preregistered outcome was metadata-incomplete, not because the receipt failed validation.

## 2. Frozen per-query observations

All four exact Arquivo.pt TimeMap metadata requests returned HTTP 404 with response content type `text/x-ndjson`:

| Frozen record | TimeMap HTTP status | Receipt status |
|---|---:|---|
| CACI 2019 | 404 | `HTTP_404` |
| Booz Allen 2020 | 404 | `HTTP_404` |
| OSI / American Science & Engineering 2023 | 404 | `HTTP_404` |
| Northrop Grumman 2024 | 404 | `HTTP_404` |

No successful response body was read or persisted. The client does not read HTTP error bodies, so the receipt has zero counted response-body bytes and no response-body SHA-256 for these errors. This is **not** a successful TimeMap response with zero rows. The metadata lookup did not complete: 0/4 queries completed, 0 capture metadata rows, 0 exact-URL capture rows.

## 3. Interpretation and decision

The result establishes that this exact Arquivo.pt endpoint-template/query contract did not produce valid TimeMap metadata for these four frozen URLs during this run. A 404 from the archive endpoint is a transport/route failure in this contract; it is not evidence that the archive never captured the URLs, nor that the transactions were historically absent from FPDS, SAM.gov, USAspending, or every public channel.

The R2 preregistration authorized no retries. Do not repeat these four TimeMap calls, switch endpoints ad hoc, open replay URLs, or expand to more transaction keys. Any different Arquivo.pt endpoint/query scheme would require a new source contract and separate review.

## 4. Scope and gates unchanged

- The frozen Q221 public-boundary population remains 348 transaction keys.
- The four purposively selected probe records and their transaction keys remain unchanged.
- Historical first-public-observation time is unproven for 348/348 rows.
- Recipient-to-issuer mapping remains unfrozen for 247 distinct recipient candidates.
- No archive payload or FPDS origin endpoint was accessed in R2; no SAM.gov, USAspending, SEC, Common Crawl or Wayback requests were made by this workflow.
- `PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`.
- Performance, holdout selection, ranking, tuning, promotion, and live execution remain unauthorized.

**Conclusion:** close this exact TimeMap URL-template route for the current preregistered workpack. Preserve the negative transport evidence, but classify it correctly as an incomplete metadata lookup—not as a historical no-hit and not as positive or negative scientific evidence.
