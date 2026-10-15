# Q221 DoD 097 — CDX MIME-type diagnostic R4

**Attempt state:** separately preregistered, one-shot metadata diagnostic. No request is made from this PR branch.

## Triggering evidence

R3 run https://github.com/DWR-debug/trading-agent-public/actions/runs/38798769065 returned HTTP 200 for the pinned CDX record, verified the timestamp, URL, digest and advertised length, then received HTTP 200 with an application/zip replay body of 13,697,800 bytes, while the CDX row advertises 13,605,284 bytes. SHA-256 of the replay body is e9e952812886ffddd5d50ef6b712e58c804d5e01034a491f1f43432ef565c1bc. The probe rejected the body before ZIP or CSV inspection. There is no transaction-row-presence result.

## Research question and sole diagnostic

R4 makes one GET request to the same Wayback CDX prefix query, with the same status/original filters and the same date/row limit, adding only the mimetype field to the output fields. It records the exact target capture timestamp, original URL, mimetype, status code, digest and length, plus bounded HTTP response headers. The one-request response cap is 5,000,000 bytes and timeout is 60 seconds. Redirects fail closed.

There is no archive-replay request in R4; no ZIP payload is downloaded, stored, or uploaded. The exact 28-key target set and pinned 348-record manifest are verified offline from the existing R3 manifest/marker but are not queried as award rows by this diagnostic.

## Why MIME type matters — hypothesis, not conclusion

The Library of Congress CDX description discusses digest and file-size metadata for captured payloads (https://www.loc.gov/preservation/digital/formats/fdd/fdd000590.shtml). A Wayback raw id_ replay is intended to return the original captured content, for which the CDX digest can be compared (https://skeptric.com/notebooks/restoring_wayback_html.html). Some CDX-client documentation warns that lengths on warc/revisit records can have special or inaccurate semantics (https://wayback.readthedocs.io/en/v0.3.3/usage.html). R3's query omitted the MIME field, so R4 tests this metadata explanation explicitly. The response does not by itself prove the cause of R3's mismatch, and a matching MIME row would not repair it.

## Frozen scope and hard gates

- Manifest Git blob SHA-1 b78cf6f7b48af3f914ee7c6d06a38f6485b0438f; receipt fingerprint 9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4.
- Exact archive FY2025_097_Contracts_Full_20250106.zip; capture 20250128184322; expected CDX digest IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB; length 13,605,284 bytes.
- One CDX GET at most; no redirects, no automatic retries, no alternate source, maximum 5 MB response. No ZIP replay and no transaction-row/schema check.
- All first-public-time, event-level PIT/public-boundary, recipient-to-issuer mapping, scientific evidence, performance, holdout, ranking, tuning, promotion, order and live-execution gates remain false. Paper-Only remains mandatory.

R4 is one-shot. A metadata response can classify the indexed MIME value only; any attempt to change the replay method, retrieve another payload, or inspect transaction rows requires a separate reviewed preregistration.