# Trading Agent OS — Working Session Recovery Checkpoint

**Checkpoint time:** 2026-10-13T22:35:08Z (UTC; local date in Europe/Berlin is 2026-10-14)
**Canonical repository:** [DWR-debug/trading-agent-public](https://github.com/DWR-debug/trading-agent-public)  
**Primary active research PR:** [#1417 — bounded Q120 CFTC exceptions and Q127 Common Crawl metadata](https://github.com/DWR-debug/trading-agent-public/pull/1417)  
**Previous duplicate PR:** [#1416](https://github.com/DWR-debug/trading-agent-public/pull/1416) was closed without merge; do not revive it.

## Resume point and validation

The default branch was verified at `6fe23d483f4a535f590854ddcae27cf6342f69c8` before this checkpoint refresh. PR #1417's prior head was `95d9cc08c085965d032b060b94841260d875a3c8`, whose checks had completed successfully on Ubuntu x64, Ubuntu ARM64, and the full suite:
- [Ubuntu / ARM64 and x64 checks](https://github.com/DWR-debug/trading-agent-public/actions/runs/38469075033)
- [Full Suite Verification](https://github.com/DWR-debug/trading-agent-public/actions/runs/38469075235)

The self-hosted worker check was **skipped** and is not counted as a Windows runner test. The PR branch had diverged from the advancing default branch; the refresh merges the verified master snapshot into the PR history and reapplies only the bounded research changes, preserving unrelated newer master state. Re-run CI on the refreshed head before merging.

## Research state

### Q120 — CFTC report-date versus publication-date feasibility

- Upstream feasibility run: [#38456880720](https://github.com/DWR-debug/trading-agent-public/actions/runs/38456880720)
- Receipt fingerprint: `9e79abc9fac1b9d1599b35e111e82e19f8b365d99e06a447638d0c0135321445`
- Official special-announcement pages document specific delays, including the ION incident in 2023 and the 2025 funding lapse/shutdown. Q120-R1 did not recover a complete historical release calendar.
- The first Q120-R2 attempt after merge, [Run #38478541967](https://github.com/DWR-debug/trading-agent-public/actions/runs/38478541967), passed 11 offline tests and validated the pinned upstream receipt, but crashed while finalizing the receipt with `NameError: name 'timezone' is not defined`. This is an implementation bug, **not** a research outcome; no valid receipt/artifact was written.
- The corrective fix imports `timezone`, adds an end-to-end mocked run test that validates the complete receipt path, refreshes only the request sequence, and lets the workflow trigger on code/test changes as well as request changes. Do not treat the failed run as source evidence; inspect the corrected retry's own receipt.
- Q120-R2 still reads only two official CFTC pages, with 350 KB per response / 700 KB total. It records explicitly listed report-date, original publication-date and new publication-date rows. Unlisted dates must not be assigned an assumed Friday release date. Exact first-public time and a complete historical calendar remain unproven.

### Q127 — FINRA daily short-sale volume PIT feasibility

- Upstream fixed-sample run: [#38455702686](https://github.com/DWR-debug/trading-agent-public/actions/runs/38455702686)
- Receipt fingerprint: `2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c`
- Q127-R2 (Internet Archive metadata) completed as `Q127R2_WAYBACK_METADATA_INCOMPLETE`: zero captured API response payloads; eight bounded metadata requests; reported body bytes were 18. It did not download target files.
- Q127-R3 run [#38478542257](https://github.com/DWR-debug/trading-agent-public/actions/runs/38478542257) wrote fingerprint `9b9159581e7770078325923e7d41df6e8fbc27986ffb329ec08d69f7bfe8bb4d`, status `Q127R3_COMMONCRAWL_METADATA_INCOMPLETE`. Common Crawl's collection list succeeded (HTTP 200, 35,226 bytes, 128 collection rows); all four selected collection-index queries failed instead: one HTTP 502 (`CC-MAIN-2024-10`) and three HTTP 404 (`CC-MAIN-2024-30`, `CC-MAIN-2025-05`, `CC-MAIN-2025-43`). The receipt has zero usable captures because the queries did not complete, not because the files were absent. No FINRA file or WARC payload was downloaded.
- Do not rerun the same four failed URLs as if they were negative results. A next attempt must use an independently verified archival-index endpoint/path or a genuinely different source; a Common Crawl capture, if found, remains observation time rather than FINRA's exact first-publication time.

## Windows runner capacity and dispatch

The permanent operator policy is committed in `ops/trading_agent_os_state.json` as `ASSUMED_ALWAYS_AVAILABLE_BY_OPERATOR`:
- A: `LHT-N133732`, formal readiness / local reproduction.
- B: `LHT-N133732-2`, frontier discovery / data QA.
- C: `LHT-N133732-3`, long deterministic research / independent reproduction.

All three are exclusive and routable. Only a job that is actually `in_progress` on a specific runner, or a verified `busy=true` observation, occupies that slot. Queued/waiting jobs do not reserve the physical runner. Availability never creates scientific evidence or authorization.

The bounded Runner-C window is renewed in this checkpoint to **2026-10-13 22:25Z–2026-10-14 00:25Z**. The capacity scheduler may dispatch the existing long deterministic readiness/guard workpack during the active interval. It must not duplicate an active job or preempt useful work actually running on that slot.

## Next actions after this checkpoint

1. Wait for refreshed PR #1417 CI and inspect any failures on the current merged tree; only merge a clean revision.
2. After merge, verify that Q120-R2, Q127-R3 and the six-pack Windows regression **actually started**. A green workflow check is not itself a scientific gate.
3. Inspect each receipt and artifact for exact status, request count/bytes, frozen upstream fingerprints and gate fields. Keep Q120 PIT and Q127 same-day/revision-lineage gates closed unless the receipts independently prove otherwise.
4. Confirm that all three Windows runners are productively used while jobs exist, and that an idle runner is refilled only with an independent, bounded, non-duplicate task.
5. Preserve the invariant: `PAPER_ONLY=true`; performance, holdout selection, ranking, tuning, promotion, orders and live execution remain disabled.

**No Q220 expected hash, Q221 identity mapping, frozen sample, or scientific/performance gate is modified by this checkpoint.**
