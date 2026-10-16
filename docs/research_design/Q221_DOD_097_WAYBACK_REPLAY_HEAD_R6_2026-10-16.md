# Q221 DoD 097 — replay HEAD metadata diagnostic R6

**State:** separately preregistered, one-shot metadata request. No source request is made from this PR branch.

## Why this is the next narrow diagnostic

The pinned R3 receipt recorded two HTTP 200 responses: the CDX JSON row (3,330 bytes) and the raw Wayback replay body (13,697,800 bytes). The CDX row advertises 13,605,284 bytes, a 92,516-byte difference. R3's receipt stores the replay status and Content-Type application/zip, but not its Content-Length, Content-Encoding, or Transfer-Encoding headers. R5 separately verified the exact CDX row MIME type is application/zip, not warc/revisit.

R6 asks one limited question: which HTTP headers does the exact pinned raw-replay URL advertise for a HEAD request? It does not repeat R3's GET request.

## Frozen contract

- Exact URL: https://web.archive.org/web/20250128184322id_/https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip
- Method: one HEAD; 60-second timeout; no redirects, retries, alternate sources, request body, response-body reads, or payload persistence.
- Whitelisted response metadata only: content-length, content-type, content-encoding, transfer-encoding, last-modified, date, server, accept-ranges, content-range, etag.
- R3 receipt blob SHA-1 91e45f71a2b31721375f8fa0812ebac038fc8d1f and fingerprint 895a6d4e343cb535866df81ce06d6d824e1d05b1c7af114aa3befeb5c5473a5b; R5 receipt blob SHA-1 9f2eb4d0e1efb419e39cb2cb8909842fd93f8164 and fingerprint a29529db8730d85c3c72a2b773033faa39653ef62a9d69703ce5a60433a9fc9d. The frozen 348-record manifest and 28-target diagnostic subset remain unchanged.

## Interpretation boundary

HEAD headers describe the current server's response metadata. Even a successful Content-Length observation does not verify archived body bytes, reconcile the original R3 body/CDX mismatch, establish transaction-row presence, prove first-public-observation time, freeze recipient-to-issuer mapping, or change a research gate. Redirects, 405 responses, timeout, and transport failures are recorded fail-closed as diagnostic outcomes.

PAPER_ONLY=True; live trading, orders, scientific evidence, performance authorization, holdout selection, ranking, tuning, promotion, and live execution remain disabled.
