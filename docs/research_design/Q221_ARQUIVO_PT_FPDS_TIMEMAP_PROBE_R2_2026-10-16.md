# Q221 — Arquivo.pt TimeMap R2 after a zero-request bootstrap failure

**Preregistered:** 2026-10-16T07:40:45Z  
**Status before execution:** pending; no R2 source requests have been made  
**Mode:** bounded archive-metadata feasibility only

## Why R2 exists

The R1 workflow [#38863558147](https://github.com/DWR-debug/trading-agent-public/actions/runs/38863558147) failed in its mandatory offline test step with `No module named pytest`. The persisted immutable R1 receipt states `PREFLIGHT_FAILED_NO_SOURCE_REQUESTS`, `archive_metadata_requests_attempted=0`, a known request count, and zero observations. The failure is infrastructure-only and is not a source outcome. Its receipt blob SHA-1 is `049c75c80b267434b62c654c4fa9a9d8bc3f4068`; receipt fingerprint `1b983784ea7b8d2d496021560b324195e9c219eafc9c538e7be32b232599aaae`.

R2 is a new, separately versioned preregistration. It pins that zero-request R1 receipt and refuses preflight if the prior artifact differs. The workflow installs the test dependency before running offline tests. R2 still requires every frozen input and budget to validate before any external request.

## Frozen scope

R2 reuses exactly the same four purposively selected FPDS Public Atom URLs and transaction keys from the previous preregistration. It does not add sampled rows, broaden any query, repeat the FPDS requests, call SAM.gov or USAspending, call SEC, query Common Crawl or Wayback, or fetch any archive replay payload.

The contract authorizes no more than four HTTPS GET requests to the Arquivo.pt Memento TimeMap metadata endpoint: one per exact encoded original FPDS URL. Each response is capped at 500,000 bytes; the total cap is 2,000,000 bytes; timeout is 35 seconds; requests are separated by at least one second. There are no automatic retries or redirects. Response bodies remain in memory and are not persisted; only bounded metadata, byte counts and SHA-256 digests enter the receipt.

## Interpretation boundary

A TimeMap capture timestamp is an archive observation, not proof of the transaction's true first-public timestamp. Even an exact-URL HTTP 200 capture is only eligible for a separately preregistered replay inspection; metadata alone does not establish that the archived payload contains the target modification tuple. Empty, unavailable, redirected, incomplete, or malformed results are not evidence that the transaction was historically absent from all public channels.

R2 cannot modify the 348-row sample, the four transaction keys, expected source hashes, recipient mappings, transaction-class applicability, agency exceptions, or earlier receipts. No result from this source-feasibility probe can clear Q221's event-level public-clock or pre-event issuer-mapping gate.

## Safety

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`. Performance authorization, holdout selection, ranking, tuning, promotion and live execution all remain false. The project stays at zero paid API budget. No credential is assumed.

**R2 decision rule:** if parser tests, immutable pin validation, or offline receipt verification fail, persist a fail-closed receipt and do not access Arquivo.pt.
