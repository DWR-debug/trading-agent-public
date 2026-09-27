# Q033 — T052 Risk/Stability Mechanism Parameter Freeze — 2026-09-27

Q033 freezes four Q030 mechanism families before any performance evaluation. The design round itself produces no performance evidence, and no family is ranked or selected.

The fixed control remains the unchanged T052 SMA 50/200 and 12-1 Top-2 core, with unchanged T052 evidence gates.

Frozen parameters:
- RISK-A: 63-session sleeve-level realized volatility, 10% annualized target, exposure 0.25–1.00x, daily, one-session lag.
- RISK-B: drawdown states at 5% and 8%, scales 0.50x and 0.25x, recovery at <=3% drawdown for 5 consecutive completed sessions.
- RISK-C: 63-session Pearson mean pairwise correlation of active assets, trigger >=0.60, scale 0.50x, daily, one-session lag.
- RISK-D: ATR20 trailing exit at 3x ATR, monthly baseline entry/re-entry, no post-exit renormalization, effective from next session.

All overlay decisions for session t use information available no later than the close of session t-1. No leverage, asset search, threshold search, parameter search, horizon search or holdout selection is permitted.

RISK-D inherits the already documented fixed T045 lifecycle rule as a pre-existing parameter source; it is not re-fitted on Q031/Q032.

Prerequisites: Q031 coverage passed on workflow 36340958902 and Q032 PIT passed on workflow 36341117495. Before performance, the mechanism implementations themselves require separate PIT-only mutation validation (Q034).

Safety remains paper-only; live trading, orders, automatic promotion and performance evaluation are disabled.
