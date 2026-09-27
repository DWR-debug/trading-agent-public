# Q030 — T052 Mechanism Design Round

## Purpose

Q030 converts the Q029 diagnostic into a set of **unranked** and mechanistically distinct research families. It does not test any family and does not choose one.

Q029 found a common T052 failure pattern across the four fixed cells: research drawdown, rolling average drawdown, Research-to-Holdout return ratio, holdout profit factor and holdout drawdown all failed in every cell.

## Candidate mechanism families

### RISK-A — Volatility-targeted exposure overlay

The underlying signal remains unchanged. Aggregate exposure is scaled using trailing realized volatility.

The causal question for a later study is whether reducing exposure during high realized-volatility states changes the stability profile without changing the signal itself.

A future preregistration must freeze: realized-volatility lookback, annualization convention, target, exposure floor/cap and rebalance timing.

### RISK-B — Portfolio drawdown-state throttle

The underlying signal remains unchanged. A fixed state machine reduces gross exposure once the portfolio enters specified drawdown states, with a fixed recovery rule.

The causal question for a later study is whether an explicit state-dependent loss-control mechanism addresses the common drawdown failure.

A future preregistration must freeze all state thresholds, exposure multipliers, recovery conditions and evaluation timing.

### RISK-C — Common-mode correlation cap

The underlying individual security signals remain unchanged. Aggregate exposure is reduced when cross-sectional dependence rises enough that nominal diversification is impaired.

The causal question for a later study is whether common-mode risk, rather than individual signal quality alone, explains part of the shared drawdown pattern.

A future preregistration must freeze the dependence estimator, lookback, trigger, cap and any benchmark treatment.

### RISK-D — Position-lifecycle tail control

The underlying entry rule remains unchanged. A fixed lifecycle layer limits stale or adverse persistence through a pre-specified holding-period and/or adverse-move exit.

The causal question for a later study is whether tail losses are concentrated in prolonged position lifecycles.

A future preregistration must freeze maximum holding period, adverse-move rule, measurement convention and execution assumption.

## Non-ranking rule

Q030 does not establish a preferred family. No performance result, score, tier, ranking or promotion decision is produced.

## Required next step

Each family must become its own fixed-rule preregistration or a clearly pre-specified multi-arm study on a fresh validation universe. Coverage and point-in-time provenance must be passed before performance is evaluated. Existing T052 holdouts remain blind and cannot be used for family or parameter selection.

## Safety

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`  
`automatic_promotion=False`
