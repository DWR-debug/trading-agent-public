# Trading Agent — Current Operational Status

**Initial synchronized baseline:** a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba  
**Repository:** DWR-debug/trading-agent-public  
**Date:** 2026-09-27

This file is the canonical human-readable current operational status. It is intentionally separate from historical project archaeology and immutable research evidence.

## Current baseline

- master includes PR #352: autonomous paper-forward feed, persistent loop and schema-v2 MTM ledger.
- PR #355 (stale Q017-G3 execution branch) has been closed because it was 384 commits behind master; its recorded scientific state remains DATA_INSUFFICIENT and it is not a current execution base.
- Bounded agent routing uses two queue lanes with fail-closed task contracts.
- Self-hosted Continuous QA is scheduled every 15 minutes on trading-agent-research.
- Current architecture claims one self-hosted runner process; a second process is a prepared scale path, not an online capacity claim.
- Coverage-only fixed-study-window candidate discovery is implemented.
- Turnover-shock continuation is implemented as a fixed coverage/PIT-only candidate; Yahoo source-vintage provenance currently prevents a formal PIT validation result.
- No current candidate has promotion evidence.
- Last recorded deterministic self-hosted QA baseline: workflow 36259124979, 881 tests passed, 2 warnings, AST and safety checks successful. This baseline predates the current master and therefore must not be presented as current verification.

## Scientific checkpoint

- Latest formal outcome recorded: NO_PROMOTION_EVIDENCE.
- Q026: DATA_INVALID / NO_SCIENTIFIC_OUTCOME; 3,704 common sessions versus 4,000 requested.
- Q023: COVERAGE_VALIDATED.
- Q025: DATE_PIT_VALIDATED.
- No holdout-based selection, promotion or live execution is authorized.
- Next scientific path: fresh fixed-rule candidate discovery, then coverage/PIT, then narrow formal validation only after a clean frozen input.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False

## Resource policy

Paid agent/API budget is 0 USD. Actual available capital is 0 EUR. The 500 EUR value is a hypothetical simulation/reference capital only.

## Canonical source order

Current operational status:
- docs/CURRENT_STATUS.md
- research/evidence/current_operational_state.json

Technical truth:
- current master

Scientific evidence:
- research/evidence/trial_ledger.json
- immutable evidence/checkpoints
- workflow artifacts

Project intent:
- docs/PROJECT_CONTEXT.md

Historical reconstruction:
- PROJECT_STATUS.md

## Synchronization rule

A dedicated GitHub Actions synchronizer updates the two current-status files after every relevant master push. It records the exact source commit that it summarizes and uses a path-exclusion rule so the documentation-only sync commit does not recursively retrigger itself.

A future trading agent chat must read this file first, then independently verify live GitHub state before changing anything.
