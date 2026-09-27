# Q029 — T052 Risk/Stability Diagnostic

## Objective

Q029 is a diagnostic-only decomposition of the immutable T052 fixed-core evidence. It does not rerun performance, alter gates, select a sleeve/universe, or use the holdout for selection.

The source population is exactly the four pre-specified cells from T049 and T050:
- SMA 50/200 inverse-volatility trend
- 12-1 top-2 cross-sectional momentum

## Fixed source

- T052 workflow: `36338219883`
- T052 artifact: `10938097809`
- T052 result fingerprint: `a0a1dc33ce281e7addcf9cf924881b6a30797c1a744d4160fbff91d3384b1b09`

The diagnostic reads the canonical T052 ledger record and validates that it still carries the frozen safety and no-selection contract.

## Diagnostic outputs

The runner reports, without ranking:
1. gate-failure counts across all four cells;
2. gates failed by all four cells;
3. gates shared by both sleeves within each universe;
4. grouped failure counts for risk/stability, generalization, cost-stress and research/rolling quality;
5. stored Research-to-Holdout shifts in return, maximum drawdown and profit factor;
6. stored rolling stability summaries.

No new P&L calculation is performed. Differences are arithmetic transformations of stored T052 metrics only.

## Interpretation rule

`COMMON_RISK_STABILITY_FAILURE` is emitted only when all three fixed risk/stability gates fail in all four cells:
- research drawdown <= 10%;
- rolling average drawdown <= 10%;
- holdout drawdown <= 10%.

This is a descriptive diagnostic label, not a strategy ranking or promotion decision.

## Safety and governance

`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`, `automatic_promotion=False`.

Q029 cannot modify T052, reopen Q020, select a candidate, change evidence gates, or trigger live execution.
