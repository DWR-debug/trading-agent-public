# Trading Agent OS — Current Working-Session Recovery Checkpoint

**State verified through:** 2026-10-14T05:12:19Z
**Canonical repository:** DWR-debug/trading-agent-public
**Last master snapshot inspected:** `af993717710aaf566151f82a511231c76282acb3`
**North Star:** `research/governance/project_north_star.json`
**Safety:** PAPER_ONLY=true; live orders, live execution, automatic promotion and all performance/holdout/ranking/tuning gates remain disabled.

## Save and merge status

- PR [#1417 — bounded Q120 CFTC exceptions and Q127 Common Crawl metadata](https://github.com/DWR-debug/trading-agent-public/pull/1417) is **merged** at 2026-10-13T22:33:02Z (`3165bb2ae4f1ab3c114288892bc5b2c71075a708`).
- Duplicate PR [#1416](https://github.com/DWR-debug/trading-agent-public/pull/1416) remains closed without merge. Do not revive it; its useful changes were independently reapplied in #1417 and subsequent master commits.
- This checkpoint supersedes the older snapshot in this file. Its source of truth is current `master`, not the historical branch `research/q120-exceptions-q127-commoncrawl-20261013`.

## Q120 — CFTC release-date exception inventory

- Upstream R1: [run #38456880720](https://github.com/DWR-debug/trading-agent-public/actions/runs/38456880720), fingerprint `9e79abc9fac1b9d1599b35e111e82e19f8b365d99e06a447638d0c0135321445`; 822 weekly report rows from 2011-01-04 to 2026-09-29.
- Initial R2 run [#38478541967](https://github.com/DWR-debug/trading-agent-public/actions/runs/38478541967) failed due to a missing `timezone` import; it wrote no receipt.
- Corrected run [#38479045457](https://github.com/DWR-debug/trading-agent-public/actions/runs/38479045457) revealed the source page repeats report date 2025-11-10 under separate dated schedule versions. Fix commit `a47375ab742863d57664ec40a940180f4e8294be` preserves those versions instead of collapsing rows.
- Latest verified run [#38479765335](https://github.com/DWR-debug/trading-agent-public/actions/runs/38479765335) completed successfully with 13 offline tests passed. Receipt fingerprint: `b92f42f2c3f8dbf8f7cfd8499be44b4130c154c415e14e97f831da9230b846dc`. Two official-page requests; 174,434 bytes; 30 explicit exception rows; 28 changed intended publish dates and 2 unchanged.
- Interpretation limit: useful official exception inventory, not a complete release calendar. Intended publish dates do not prove exact first-publication time. Unlisted dates remain unknown; same-day PIT remains closed.

## Q127 — FINRA historical short-sale-volume PIT

- Frozen R1 sample: [run #38455702686](https://github.com/DWR-debug/trading-agent-public/actions/runs/38455702686), fingerprint `2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c`; 4 dates and 8 fixed symbols.
- R2 Internet Archive metadata: [run #38461580319](https://github.com/DWR-debug/trading-agent-public/actions/runs/38461580319), `Q127R2_WAYBACK_METADATA_INCOMPLETE`, 7 bounded metadata requests, 3,848 bytes and no target-file captures.
- R3 Common Crawl metadata: [run #38478542257](https://github.com/DWR-debug/trading-agent-public/actions/runs/38478542257), 28 offline tests passed, 5 requests / 35,686 bytes, receipt fingerprint `9b9159581e7770078325923e7d41df6e8fbc27986ffb329ec08d69f7bfe8bb4d`, status `Q127R3_COMMONCRAWL_METADATA_INCOMPLETE`.
- Common Crawl collection listing succeeded (128 collection rows), but all four selected index queries failed at the endpoint layer: 1 HTTP 502 and 3 HTTP 404. Zero usable captures means queries did not complete, not that files were absent. No FINRA data files or WARC payloads were downloaded.
- Next Q127 step must verify a different documented endpoint/index route or use a genuinely independent source. Do not repeat the same failed URLs as a negative result. A capture time remains an archive observation, not FINRA's exact first-publication time.

## Q220 — frozen SEC/XBRL hashes

Q220 remains blocked. Two bounded original-submission checks matched accession/CIK/form/filing-date identity but did not reproduce the frozen source hashes; the third daily-feed download was incomplete. The 55-entry population retained hashes and byte counts but not immutable raw bytes from original ingestion. This is a provenance gap, not proof which representation changed. Do not rewrite hashes or retry broad multi-GB downloads. Continue by reconstructing byte-boundary/extraction provenance from existing code, commit history and receipts.

## Q221 — transaction public-observation boundary

The official monthly archive catalogue exposed no multi-date archive series for the seven target fiscal years; no ZIP payload was downloaded. The transaction-parent UEI probe and its one registered retry both returned HTTP 503 before count preflight/download. Do not retry the same endpoint without a new route or documented service recovery. The 348 frozen keys and recipient-to-issuer mapping remain unchanged.

## Exclusive Windows runner capacity

The permanent operator contract in `ops/trading_agent_os_state.json` says all three Windows slots are always routable except when a job is actually running on that exact slot:
- A: `LHT-N133732` — formal readiness/local reproduction.
- B: `LHT-N133732-2` — frontier discovery/data QA.
- C: `LHT-N133732-3` — long deterministic research/independent reproduction.

At the last live snapshot, the only in-progress workflow reported was the hosted [Evidence Graph Stage 4–5 wave](https://github.com/DWR-debug/trading-agent-public/actions/runs/38512814652). Old queued Monitor/Router entries date to 2026-10-07 and do not reserve a Windows runner. Runner-C long workpack [#38487402103](https://github.com/DWR-debug/trading-agent-public/actions/runs/38487402103) previously completed successfully.

The paired window update in this checkpoint proposes the existing deterministic readiness/guard workpack for **2026-10-14 05:20Z–07:20Z**. It does not initiate Q220/Q221/Q127 external-source retries. It becomes active on `master` only after this checkpoint PR is merged.

## Resume checklist

1. Validate this checkpoint/window PR; merge only after all required checks pass.
2. Verify the Runner-C long deterministic workpack actually starts in the proposed window. Only an in-progress job on the exact runner reserves a slot; a queued job does not.
3. Keep Q120's complete-calendar/exact-publication-time gates closed.
4. For Q127, verify a different documented index route before further requests.
5. For Q220, resume byte-provenance analysis, not hash rewriting or broad downloads.
6. Preserve PAPER_ONLY=true; performance, holdout, ranking, tuning, promotion, orders and live execution remain disabled.
