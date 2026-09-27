# Q031 - Q030 Risk/Stability Coverage Preflight

## Purpose
Q031 checks only the data prerequisites for the four Q030 mechanism families on a new fixed, symbol-disjoint ETF universe.
No strategy performance, return, drawdown, holdout or candidate-selection result is produced.

## Fixed universe
BSV, FAN, JNK, UDN, VCLT, VGIT, SCHR
Study window: 2011-01-01 through 2025-09-24.
Acquisition request: 4,000 daily candles per symbol.
Common-calendar target: 3,500 sessions.

These symbols were previously observed in a coverage-only candidate search, but are not present in the formal asset-universe registry before this preregistration. No performance criterion is involved.

## Mechanism families
- RISK-A: volatility-targeted exposure overlay
- RISK-B: portfolio drawdown-state throttle
- RISK-C: common-mode correlation cap
- RISK-D: position-lifecycle tail control

Q031 does not select between them.

## Pass/block rule
A future performance study is blocked unless the fixed universe meets the 3,500 common-session coverage contract and applicable point-in-time requirements.
A Q031 coverage failure is a data-contract failure, not trading performance evidence.

## Governance and safety
No holdout is used. No parameters, assets, thresholds, horizons or variants are searched. No gate is changed and no promotion is possible.
PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False; automatic_promotion=False
