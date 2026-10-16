# Q221 DoD 097 — replay/CDX length discrepancy adjudication R1

**State:** evidence reconciliation only. No source request is authorized by this note. The R3 and R5 receipts and the R6 HEAD-only receipt remain immutable.

## Frozen observations

- R3 source receipt: [run #38798769065](https://github.com/DWR-debug/trading-agent-public/actions/runs/38798769065), Git blob SHA-1 `91e45f71a2b31721375f8fa0812ebac038fc8d1f`, receipt fingerprint `895a6d4e343cb535866df81ce06d6d824e1d05b1c7af114aa3befeb5c5473a5b`.
- R3 recorded a CDX row with HTTP status 200, digest `IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB`, and `length=13605284`; the subsequent raw replay GET returned HTTP 200 and 13,697,800 body bytes. The difference is 92,516 bytes. The GET body SHA-256 is `e9e952812886ffddd5d50ef6b712e58c804d5e01034a491f1f43432ef565c1bc`.
- R5 source receipt: [run #38855135000](https://github.com/DWR-debug/trading-agent-public/actions/runs/38855135000), fingerprint `a29529db8730d85c3c72a2b773033faa39653ef62a9d69703ce5a60433a9fc9d`. It confirmed the exact CDX capture has MIME type `application/zip`, status 200, and the same length `13605284`; R5 made no archive replay request and inspected no archive rows.
- R6 source receipt: [run #38857230362](https://github.com/DWR-debug/trading-agent-public/actions/runs/38857230362), fingerprint `7e9299b743381716251b87e976bf5c23e6511b4b2cc9457b0660bc7346a4b882`. A single HEAD request reported HTTP 200, `Content-Length: 13697800`, `Content-Type: application/zip`, `Accept-Ranges: bytes`, `Server: nginx`, and a response date of 2026-10-16. It read zero response-body bytes and issued no GET. The immutable R6 receipt is stored at [attempt #38857230362](https://github.com/DWR-debug/trading-agent-public/blob/master/research/evidence/q221_dod_097_wayback_replay_head_r6_attempt_38857230362.json).

## What authoritative documentation supports

The Library of Congress description of CDX says the 2015 format's `file_size (S)` is the size of the web object in bytes derived from the CDX index and notes that the offset points into the compressed WARC file: <https://www.loc.gov/preservation/digital/formats/fdd/fdd000590.shtml>. The Internet Archive CDX server documentation lists `length` as a public API field but does not define its exact production calculation in the field list: <https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md>.

The `wayback` client documentation describes the CDX `length` as size of captured content, while warning that this value may be inaccurate; it separately notes a special case for `warc/revisit` records: <https://wayback.readthedocs.io/en/v0.3.3/usage.html>. R5 reports `application/zip`, not `warc/revisit`, so that documented special case is not a demonstrated explanation for this record. It does not follow that the CDX value is guaranteed correct.

WARC itself has a separate record-block `Content-Length`, defined as the number of octets in the WARC block. A WARC response record may also contain the original HTTP response headers, including a different inner HTTP `Content-Length`; the WARC specification demonstrates this distinction: <https://iipc.github.io/warc-specifications/specifications/warc-format/warc-1.1-annotated/>. This is an important terminology distinction, not proof that the specific CDX `length` value here is a WARC block size.

## Adjudication

1. **Established:** the current raw-replay endpoint advertises a HEAD `Content-Length` equal to the body byte count observed during R3. The current HEAD MIME type also agrees with R3 and R5.
2. **Not established:** that current HEAD metadata proves the byte-for-byte identity of the historically stored payload; that it explains the CDX `length`; or that the captured archive bytes were corrupted, transformed, or truncated.
3. **No finding of historical transaction-row presence:** neither R5 nor R6 inspected ZIP/CSV content. No row, schema, public-boundary, first-public-observation, or recipient-to-issuer mapping gate is satisfied by these metadata results.
4. **No automatic next request:** the R3 GET is not repeated. Any future WARC/CDX-record-level investigation requires its own narrow preregistration and bounded request contract before external access. It must distinguish the CDX object's advertised size, the replay endpoint's HTTP `Content-Length`, WARC record-block length, and the actual uncompressed payload; these values must not be silently substituted for one another.
5. The 348-record source manifest, frozen 28-target diagnostic set, expected digest, population, all scientific gates, and Paper-Only controls are unchanged.

## Safety

`PAPER_ONLY=True`. Live trading, orders, scientific evidence, performance authorization, holdout selection, ranking, tuning, promotion, and live execution remain disabled. R6 read no response-body bytes and made no archive GET.
