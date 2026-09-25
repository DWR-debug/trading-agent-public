# Q010 Cross-Trial Failure Diagnosis — 2026-09-25

## Formal status

Q010 was executed exactly once under the explicit authorization commit `7000b6c47c488c28aa5f1700aceac7fc4b64675b`.

- Workflow run: 36119705793
- Artifact ID: 10856102739
- Artifact ZIP SHA256: sha256:9f10a27ed267870981c8f480e868967e22c4d19a8c3562c37c9690d19dcf01c2
- Diagnosis fingerprint: c11a4a2340bf4f7a9f132f53835465d57d0b12ab97770a24f3fd98492e7f9549
- Tests: 744 passed
- Paper-only Safety: passed
- Result status: **DIAGNOSTIC_ONLY**

## Evidence scope

The diagnosis uses immutable archived evidence for T041, T042, T044 and T045 plus the data-invalid record T043. No new performance backtest was executed. T045's duplicate formal reproduction remains a duplicate and is not counted as an independent trial.

T043 is **DATA_INVALID** and therefore carries no performance claim.

## Recurring failure signature

Across the four performance-valid trials:

| Pattern | Recurrence |
| --- | ---: |
| Research drawdown gate > 10% | 4 / 4 |
| Control-relative non-deterioration failure | 4 / 4 |
| OOS/IS stability failure | 3 / 4 |
| Holdout drawdown > 10% | 3 / 4 |
| Positive holdout return | 4 / 4 |

The important distinction is that positive holdout returns occurred in all four performance-valid trials, but none satisfied the complete evidence contract. The recurring constraint is therefore not simply sign of return; it is robust risk quality together with preservation relative to the fixed control.

## Methodological interpretation

The four performance trials represent materially different intervention families:

- T041: portfolio-risk control
- T042: volatility-managed TSM
- T044: trend-signal consistency
- T045: position-lifecycle exit control

Despite those differences, the same research-risk and control-relative failures recur. This is evidence for a research-direction constraint, not proof of a single causal mechanism.

Accordingly, the next research step is not another adjustment to the failed controls. The next mechanism should be orthogonal and information/alpha-oriented, with a fixed rule and the existing evidence contract unchanged.

## Explicit non-actions

No parameter reselection, asset reselection, holdout selection, gate relaxation, same-trial backtest rerun, production promotion, or live execution was performed.

## Safety

`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`, `automatic_promotion=False`.
