# Trading Agent — Current Operational Status

**Current operational snapshot:** `5b91675d78a24d709aeb5337848ca9f6876f026d`

**Generated (UTC):** `2026-09-28T05:04:14.909943+00:00`

**Repository:** `DWR-debug/trading-agent-public`

> This file is the canonical current operational status. `PROJECT_STATUS.md` is historical reconstruction and must not override it for current operational facts. Scientific evidence remains governed by the trial ledger, immutable evidence/checkpoints and workflow artifacts.

## Current state

### Engineering

- Paper/Shadow/Forward infrastructure: **MERGED** via PR #352, merge commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`.
- The Forward path contains closed-candle market-data ingestion, a persistent update loop and a schema-v2 per-candle MTM ledger.
- Canonical data-layer infrastructure is merged.
- Bounded agent routing uses two queue lanes with fail-closed task contracts.
- Self-hosted Continuous QA is scheduled every 15 minutes under label `trading-agent-research`.
- The current architecture claims one runner process; a second process is only a prepared scale path, not an online capacity claim.

### Scientific status

- Latest formal performance trial: **T-2026-09-27-065 / NO_ARM_PASSED_ALL_13_GATES**.
- **Q066/T-2026-09-28-066** is completed as **DIAGNOSTIC_ONLY**; it reconstructed Q041/T060 and Q045/T065 exactly from immutable Actions evidence.
- Q066 identifies persistent multi-regime drawdowns and high adverse-period return co-movement as the shared risk patterns; concentration amplifies some arms, while turnover/cost is a separate failure mode for high-churn arms.
- Q041/T060 is now canonically present in the trial ledger; Q066 is also canonically recorded.
- **Q067 is DESIGN_ONLY_UNRANKED** with two follow-up mechanisms: alpha-level common-mode exposure control and turnover hysteresis.
- No current candidate is authorized for promotion or live execution. Any Q067 performance study remains blocked until ex-ante parameter freeze, fresh symbol-disjoint coverage and PIT validation.
- Current generic master Actions lanes are showing immediate failures with no job records; this is treated as infrastructure evidence, not scientific evidence. Q066's dedicated workflow itself completed successfully.

### Resource policy

- Paid agent/API budget: **0 USD**.
- Actual available capital: **0 EUR**.
- Hypothetical reference capital: **2000 EUR**, simulation/planning only.
- Legacy 500-EUR operational canary remains separate.
- Deterministic research stays on reproducible runner paths.
- Agent output is never scientific evidence by itself.

## Q067 — next research design

Two unranked mechanisms are frozen at the design level only:

- **E1 Alpha Common-Mode Throttle:** tests whether dependence among alpha-sleeve return streams can be controlled without collapsing exposure.
- **E2 Turnover Hysteresis:** tests whether deterministic rebalance deadbands can reduce cost drag in high-churn mechanisms without redefining the signal.

Neither mechanism has performance evidence yet. The existing 13-gate contract remains unchanged.

## Safety

`PAPER_ONLY=True`

`LIVE_TRADING_ENABLED=False`

`ORDERS_ENABLED=False`

`AUTOMATIC_PROMOTION=False`

## Canonical source order

1. Current operational facts: `docs/CURRENT_STATUS.md` and `research/evidence/current_operational_state.json`
2. Technical truth: current `master`
3. Scientific evidence: trial ledger, immutable evidence/checkpoints and workflow artifacts
4. Project intent: `docs/PROJECT_CONTEXT.md`
5. Historical reconstruction: `PROJECT_STATUS.md`

## Continuity protocol

Every relevant `master` push triggers the status synchronizer. It records the exact source commit being synchronized and updates these two operational-status files in a documentation-only commit. Those files are excluded from the synchronizer trigger, preventing recursive commits.

A future `trading agent` chat must read this file first, then verify live GitHub state before acting.
