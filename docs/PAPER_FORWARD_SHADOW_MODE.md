# Paper-only shadow/forward simulation

`automation/paper_forward_shadow.py` replays one explicitly frozen candidate on
successive candle inputs using the existing `StrategyEngine` and
`BacktestEngine`. It does not select candidates, fetch market data, call a
broker, submit orders, evaluate research gates, or promote anything.

## Candidate and data contract

Start with a JSON candidate containing exactly the following fields:

```json
{
  "schema_version": 1,
  "frozen": true,
  "candidate_id": "candidate-001",
  "freeze_ref": "immutable-preregistration-or-commit-reference",
  "symbol": "TEST",
  "interval": "1h",
  "initial_capital_eur": 1000.0,
  "risk_per_trade": 0.01,
  "leverage": 1.0,
  "fee_rate": 0.001,
  "slippage_rate": 0.0005,
  "parameters": {
    "momentum": {"lookback": 5},
    "mean_reversion": {"window": 5, "threshold": 0.02}
  }
}
```

`frozen` and a non-empty `freeze_ref` are mandatory declarations by the caller;
the harness does not decide whether the candidate is scientifically authorized.
The supplied parameters and costs are fixed for the life of a run. The supported
intervals are `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, and `1d`. Candle input is a
non-empty JSON array of `{timestamp, open, high, low, close, volume}` objects
with timezone-aware ISO timestamps.

Candles must be ordered, unique, finite, and exactly contiguous at the declared
interval. A missing interval, modified previously observed candle, unsupported
interval, or invalid OHLCV value fails closed; the runner neither fills nor
silently skips gaps. An update can contain only new candles, an unchanged
overlap plus new candles, or an unchanged historical window. Replaying
unchanged inputs leaves the portfolio fingerprint and output unchanged.

## Start, update, and stop

State is kept in a caller-selected JSON file and atomically replaced at each
successful update. The state contains the frozen candidate, the complete
canonical candle history, portfolio summary, and trade record, so every update
replays from the same initial simulated capital and candidate rather than
depending on hidden process memory.

```sh
python -m automation.paper_forward_shadow start \
  --candidate frozen_candidate.json --candles initial_candles.json --state shadow.json
python -m automation.paper_forward_shadow update \
  --candles next_candles.json --state shadow.json
python -m automation.paper_forward_shadow stop --state shadow.json
```

The run ID is stable for the frozen candidate and first market timestamp.
Candidate, cumulative input, and signal fingerprints are SHA-256 over canonical
JSON. `started_at_utc` and `updated_at_utc` are market-data timestamps (first
and latest candle), not wall-clock execution times. Stop time is the last
processed candle timestamp, making a replay reproducible. A stopped session
cannot be resumed or updated; start a separate state file for a new run.

Each snapshot records net simulated P&L, trade count, gross traded notional,
maximum single-trade notional, and maximum drawdown on the realized trade-equity
curve. The existing backtest engine marks any still-open simulated position to
the latest close when producing a snapshot, so `current_position_exposure_eur`
is zero at that boundary. Drawdown is trade-close based and does not claim
intrabar mark-to-market risk. No metric is interpreted as evidence or used for
candidate selection or promotion.

## Safety

Every start/update/stop checks the central configuration and fails unless
`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False`, and
`AUTOMATIC_PROMOTION=False`. The runner only consumes local JSON/candle objects
and the offline signal/backtest components; it contains no broker or order API.
Historical evidence, authorizations, research gates, and holdout logic are not
inputs or outputs of this mode.
