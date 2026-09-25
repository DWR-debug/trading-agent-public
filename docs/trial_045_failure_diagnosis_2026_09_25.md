# T045 Failure Diagnosis — 2026-09-25

## Status

- Trial: T-2026-09-25-045
- Formal workflow: 36117548408
- Artifact: 10854674939
- Artifact SHA256: sha256:6981fd12a8f8b1e6b4b28a4eef885af963e1de5922edf9fbe182047872dd0adb
- Formal report fingerprint: 90bb1b7f84b19a8675bab6ed6505931544e2d320c0cdaf199db4c8666a94595a
- Candidate status: **BLOCKED**
- Diagnosis status: **DIAGNOSTIC_ONLY**

Coverage passed before formal performance execution: 3,519 common timestamps against a 3,500 target; coverage fingerprint 4c82327c957331851b1184a2a947f77f38e0b73d8e6b54a3fafda424d86296dc. The formal run completed with 743 tests passed and Paper-Only safety verified.

## Absolute gate result

| Gate | Challenger | Threshold | Result |
| --- | ---: | ---: | --- |
| Research return | +41.228% | > 0% | PASS |
| Research max drawdown | 20.066% | ≤ 10% | FAIL |
| Research profit factor | 1.068 | ≥ 1.10 | FAIL |
| Rolling PF | 1.068 | ≥ 1.10 | FAIL |
| Profitable rolling windows | 60% (3/5) | ≥ 50% | PASS |
| Average rolling DD | 13.075% | ≤ 10% | FAIL |
| OOS / IS | 0.202 | ≥ 0.25 | FAIL |
| Holdout return | +8.340% | > 0% | PASS |
| Holdout PF | 1.059 | ≥ 1.10 | FAIL |
| Holdout max DD | 15.984% | ≤ 10% | FAIL |
| 1.5x-cost holdout return | +6.520% | ≥ 0% | PASS |
| 2x-cost holdout return | +4.730% | ≥ 0% | PASS |
| Total-return sensitivity | +12.570% | ≥ 0% | PASS |

## Change versus fixed control

| Metric | Fixed | T045 challenger | Delta challenger - fixed |
| --- | ---: | ---: | ---: |
| Research return | +60.616% | +41.228% | -19.388 pp |
| Research max DD | 19.733% | 20.066% | +0.333 pp |
| Research PF | 1.090 | 1.068 | -0.021 |
| Rolling PF | 1.090 | 1.068 | -0.021 |
| Profitable rolling windows | 80% (4/5) | 60% (3/5) | -20 pp |
| Average rolling DD | 14.024% | 13.075% | -0.949 pp |
| OOS / IS | 0.349 | 0.202 | -0.146 |
| Holdout return | +21.130% | +8.340% | -12.791 pp |
| Holdout max DD | 9.792% | 15.984% | +6.192 pp |
| Holdout PF | 1.127 | 1.059 | -0.068 |

The only control-relative metric that improved in the prescribed base comparison was average rolling drawdown. The primary research max-DD and holdout DD gates both remained above 10%.

## Rolling-window structure

| Window | Challenger return | Challenger DD | Challenger PF | Fixed return | Fixed DD | Fixed PF |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | +8.402% | 8.119% | 1.117 | +14.431% | 10.051% | 1.186 |
| 2 | -0.669% | 14.262% | 1.004 | +2.685% | 13.217% | 1.030 |
| 3 | +31.061% | 8.260% | 1.255 | +31.709% | 9.529% | 1.252 |
| 4 | +17.877% | 15.102% | 1.142 | +19.280% | 19.733% | 1.149 |
| 5 | -15.102% | 19.631% | 0.897 | -12.994% | 17.592% | 0.914 |

Window 5 remains the clearest common weak tail in this decomposition; the challenger has the more negative return and lower PF in that window. This is descriptive only.

## Lifecycle diagnostics

391 stop events occurred across the eight trend assets: AXP 55, BLK 53, COP 37, DHR 49, DUK 46, INTU 50, MAR 53, WFC 48.

The run records 14,524 stopped asset-days and 13,476 position asset-days. These counts confirm substantial lifecycle intervention, but they do not by themselves establish causality.

## Methodological conclusion

T045 does not satisfy the preregistered evidence contract. It is archived as **BLOCKED / NO_SUPPORT** and does not modify the fixed candidate, its parameters, or the project gates.

The next work item is a **descriptive, immutable-artifact diagnosis** of stop timing, post-stop path behaviour, and asset/time concentration. It will not tune the ATR multiple or select assets from the T045 outcome. Any new performance intervention must be independently preregistered and evaluated on a fresh symbol-disjoint universe.


**Safety:** PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False; automatic_promotion=False.
