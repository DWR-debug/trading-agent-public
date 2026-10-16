# Q221 DoD 097 — CDX MIME-type diagnostic R5

**Attempt state:** separately preregistered, one-shot metadata-only request. R4 failed its offline preflight before any source request because its workflow referenced a Python module name that did not exist. R4 source request count was zero; the CDX request step was skipped in run [#38854562926](https://github.com/DWR-debug/trading-agent-public/actions/runs/38854562926). R5 does not retry a source request from R4; it is a new attempt with a new preregistration, request marker, workflow and receipt namespace.

## Sole diagnostic

R5 asks the same frozen question as R4: retrieve only the MIME type plus the frozen CDX fields for the exact Wayback capture. It allows at most one GET to the fixed CDX endpoint, caps the response at 5,000,000 bytes, and uses a 60-second timeout. Redirects fail closed. It does not request the archived ZIP, download ZIP payload, or inspect award/contract rows.

## Frozen source and target pins

- Manifest Git blob SHA-1: `b78cf6f7b48af3f914ee7c6d06a38f6485b0438f`; manifest fingerprint: `9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4`; 348 expected transactions and a frozen 28-key diagnostic subset.
- Target archive: `FY2025_097_Contracts_Full_20250106.zip`; Wayback capture `20250128184322`; expected CDX SHA-1 `IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB`; expected length `13,605,284` bytes.
- CDX fields: timestamp, original, mimetype, statuscode, digest, length. Exactly one request, max 5 MB, no redirects, no retries and no alternate source.

## Interpretation boundary

CDX MIME metadata is diagnostic only. A successful result cannot repair R3's replay-length mismatch, prove row presence, establish any award's first public-observation time, freeze recipient-to-issuer mapping, or change a PIT gate. A failed/timeout/capped response is recorded with a fingerprinted receipt. R1–R4 artifacts are not rewritten. 

Safety: `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False`, `AUTOMATIC_PROMOTION=False`. Performance, holdout selection, ranking, tuning, promotion, and live execution remain false.
