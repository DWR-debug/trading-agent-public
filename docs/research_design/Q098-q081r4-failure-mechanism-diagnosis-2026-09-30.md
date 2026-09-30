# Q098 — Q081-R4 Failure-Mechanism Diagnosis

**Stand:** 2026-09-30
**Status:** DIAGNOSTIC_ONLY — no new performance evaluation, no selection, no authorization

## Purpose

Q098 describes the failure signature of the completed Q081-R4 fixed-rule performance experiment without modifying, rerunning or selecting any arm.

Source:
- Trial: T-2026-09-30-081R4-PERFORMANCE
- Workflow: 36704648242
- Result fingerprint: b57f93d2ebd1076f191076ea77ad37ca5dfd7cf4f8da5fdb0f4047b4217ea30a
- Research periods: 2798
- Holdout periods: 700
- Fixed universe: HAL, LRCX, OXY, COF, FIS, FISV, GM, LHX
- Arms: CONTROL_6SLEEVE_ENSEMBLE, E1_ALPHA_COMMON_MODE_THROTTLE, E2_TURNOVER_HYSTERESIS

No holdout observation is used to choose an arm. No parameter, threshold, asset, horizon, variant or family search is performed.

## Fixed gate failure signature

All three arms pass exactly 9 of the 13 preregistered gates.

The same four gates fail for all three arms:
1. research_drawdown_lte_10pct
2. rolling_average_drawdown_lte_10pct
3. oos_to_is_return_ratio_gte_0_25
4. holdout_drawdown_lte_10pct

The following nine gates pass for all three arms:
1. research_return_positive
2. research_profit_factor_gte_1_10
3. rolling_profit_factor_gte_1_10
4. rolling_profitable_window_ratio_gte_0_50
5. holdout_return_positive
6. holdout_profit_factor_gte_1_10
7. stress_1_5x_holdout_nonnegative
8. stress_2x_holdout_nonnegative
9. total_return_sensitivity_holdout_nonnegative

Thus the observed failure pattern is common across the control and both fixed follow-up mechanisms. The failures are concentrated in drawdown/risk limits and in the research-to-holdout transfer-ratio gate; the predefined cost-stress and non-negative-return gates are not the blocking dimensions in this trial.

## Arm-level descriptive measurements

These values are reported without ranking or selection:

| Arm | Research max DD | Holdout return | Holdout max DD | Holdout PF | OOS/IS return ratio |
|---|---:|---:|---:|---:|---:|
| CONTROL_6SLEEVE_ENSEMBLE | 45.0779% | 34.3006% | 24.1285% | 1.11727 | 0.16846 |
| E1_ALPHA_COMMON_MODE_THROTTLE | 25.3203% | 25.3878% | 17.4904% | 1.12967 | 0.24689 |
| E2_TURNOVER_HYSTERESIS | 44.9560% | 34.0086% | 24.1285% | 1.11654 | 0.16873 |

The table is descriptive only. The study does not authorize choosing an arm because of any observed metric.

## Diagnostic interpretation

### 1. Risk remains the dominant common failure dimension

Every arm exceeds the fixed 10% research drawdown limit, the fixed 10% rolling average drawdown limit, and the fixed 10% holdout drawdown limit.

Positive period return and profit-factor evidence is therefore not sufficient to satisfy the project's complete validation contract.

### 2. The common-mode throttle changes the observed risk profile but does not satisfy the fixed validation contract

E1 produces a distinct lower observed drawdown profile than the control in this fixed run, while still failing all four common failure gates. The diagnostic therefore does not treat E1 as a validated successor.

### 3. Cost stress is not the sole explanation of failure

Both predefined cost-stress gates pass for every arm, as does total-return sensitivity. The failure cannot therefore be reduced to a single cost-stress breakpoint in this experiment.

These are descriptive consequences of the completed result, not causal claims.

## Research consequence

Q098 does not justify a parameter retune or another performance run of Q081-R4.

Any later hypothesis must be defined before looking at new outcomes and must address the unresolved mechanism in a genuinely new way. A valid next step is a mechanism-level risk/dependence diagnosis on the frozen Q081-R4 evidence, or an independent design-only frontier family with its own provenance and PIT contract.

No successor may inherit performance authorization from Q081-R4.

## Governance

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- ORDERS_ENABLED=False
- AUTOMATIC_PROMOTION=False
- performance_authorized=false
- holdout_selection=false

Q098 creates no promotion evidence and no live-trading permission.
