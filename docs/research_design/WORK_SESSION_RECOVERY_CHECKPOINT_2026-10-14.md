# Trading Agent OS — Working Session Recovery Checkpoint

**Checkpoint time:** 2026-10-13T22:31:02Z (UTC; local date in Europe/Berlin is 2026-10-14)  
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
- Official special-announcement pages document specific delays, including the ION incident in 2023 and the 2025 funding lapse/shutdown. The existing source-feasibility receipt recovered no complete historical release calendar.
- Q120-R2 is a new two-request, official-source-only inventory of rows explicitly stating COT report date, original publish date and new publish date. Its 350 KB per-response / 700 KB total caps and non-authorizing flags are frozen. Unlisted dates must not be assigned an assumed Friday release date. The exact first-public timestamp remains unproven.

### Q127 — FINRA daily short-sale volume PIT feasibility

- Upstream fixed-sample run: [#38455702686](https://github.com/DWR-debug/trading-agent-public/actions/runs/38455702686)
- Receipt fingerprint: `2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c`
- Q127-R2 (Internet Archive metadata) completed as `Q127R2_WAYBACK_METADATA_INCOMPLETE`: zero captured API response payloads; eight bounded metadata requests; reported body bytes were 18. It did not download target files.
- Q127-R3 uses the distinct Common Crawl index for the same four frozen FINRA file URLs, up to five requests and 1.2 MB total. No FINRA file or WARC payload may be downloaded. A crawl timestamp means Common Crawl observed a URL then; it is not FINRA's exact first-publication time. A no-hit is not proof of nonpublication.

### Q220 and Q221 — do not restart the same failed path

- Q220's 55 frozen population hashes remain unchanged. The bounded SEC Feed retry found correct accession/CIK/form/filing-date identity in two of three samples, but none of their tested content representations reproduced the frozen expected hash; the third large feed download was incomplete. Do not change expected hashes or initiate another multi-GB retry without a genuinely new, evidence-backed route.
- Q221's transaction-level parent-UEI route returned HTTP 503 on both the original attempt and the single permitted retry, before count preflight and with no archive download. Treat that route as exhausted; do not issue another identical retry or infer any identity mapping.

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
