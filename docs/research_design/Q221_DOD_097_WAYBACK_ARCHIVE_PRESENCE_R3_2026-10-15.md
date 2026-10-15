# Q221 DoD 097 Wayback archive row-presence probe — recovery R3

**State:** separately preregistered proposal; no source request has run from this branch. This is not archive-row evidence or public-clock clearance.

## Evidence driving R3

R2 source run [#38797148893](https://github.com/DWR-debug/trading-agent-public/actions/runs/38797148893) successfully validated the pinned manifest and exact 28-target sample, then made one request to the fixed Wayback CDX endpoint. The persisted, fingerprint-validated receipt records `request_count=1`, `response_bytes=0`, `responses=[]`, and `TimeoutError`. No HTTP response or archive-row outcome was observed. The receipt is persisted at [attempt JSON](https://github.com/DWR-debug/trading-agent-public/blob/master/research/evidence/q221_dod_097_wayback_archive_presence_attempt_38797148893.json).

## Sole acquisition-method change

R3 freezes a per-request socket/open timeout of **60 seconds**, changed from 25 seconds in R2, as a direct response to that observed timeout. This changes no scientific gate and does not authorize retries within a request or a third request.

Unchanged: exact archive `FY2025_097_Contracts_Full_20250106.zip`; pinned Wayback capture `20250128184322`; CDX SHA-1/Base32 `IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB`; expected length 13,605,284 bytes; original manifest Git blob SHA-1 `b78cf6f7b48af3f914ee7c6d06a38f6485b0438f`; its fingerprint `9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4`; the same 28 keys derived at run time from the same 348-key manifest; at most two GET requests to `web.archive.org`; the same CDX/archive/total response and ZIP/CSV caps; no redirects; no archive bytes persisted or uploaded.

## Interpretation and hard gates

A timeout remains an unknown archive-row outcome. A successful R3 result could establish only schema/row presence in this exact historical snapshot, not first-public time. A no-match would apply only to this snapshot, not historical absence from every public channel. Historical first-public observation, event-level PIT, transaction-class applicability, pre-event recipient-to-issuer mapping, scientific evidence, performance authorization, holdout selection, ranking, tuning, promotion, orders and live execution remain false. The R2 marker and receipt are immutable. R3 is one-shot and will not auto-retry if the transport fails again.
