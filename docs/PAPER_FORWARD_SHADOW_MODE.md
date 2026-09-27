# Paper-only shadow/forward simulation

The paper-forward harness now forms a complete technical simulation chain:

Frozen Candidate -> paper capital -> closed market candles -> simulated positions ->
fees/slippage -> realized and unrealized P&L -> per-candle MTM ledger ->
reproducible persistent state.

The system remains strictly paper-only. It does not call a broker, submit orders,
select candidates, evaluate research gates, or promote anything.

## Frozen candidate

The candidate contract remains version 1. The supplied parameters and costs are
fixed for the lifetime of a shadow run. A simulated initial capital of 500.00 EUR
is supported and is not evidence of available real capital.

## Automatic market data

automation/paper_forward_market_feed.py uses the existing public Binance market
data endpoint without API keys. Only completed candles are accepted. The feed
never overwrites an already observed candle; a vendor revision is rejected
fail-closed by the shadow state.

The existing historical Binance loader is reused for the initial warm-up. The
incremental path fetches a recent window, filters the still-open candle, and
passes the closed overlap/new candles through the same immutable-input validator.

Each successful feed update can write a separate JSON receipt containing deterministic
`candle_fingerprint`, `fetch_fingerprint`, and `receipt_fingerprint` values.
The persisted Shadow-State stores the same receipt, candle, and fetch fingerprints,
and the receipt records the resulting state `input_fingerprint`, making the feed
receipt and state provenance explicit. `fetched_at_utc` is volatile retrieval
metadata and is deliberately excluded from all deterministic hashes.

## Persistent MTM portfolio ledger

Shadow state schema_version=2 contains a complete ledger row for every accepted
market candle. Each row records market time, close, signal, cash, realized P&L,
unrealized P&L, MTM equity, position state, gross exposure, cumulative fees,
cumulative traded notional, and realized/MTM drawdown.

Open positions remain open at an update boundary. The snapshot does not force an
artificial closing trade merely to obtain a final equity number. final_equity_eur
is therefore MTM equity, while realized_pnl_eur excludes unrealized gains/losses.

Entry fees reduce cash when a position opens; exit fees and slippage are charged
when it closes. The simulator uses candle OHLC for the same stop-loss semantics
as the existing offline backtest model. The MTM mark is the latest completed
close and does not claim tick-level liquidation or intrabar mark accuracy.
Forward candidates must use the authorized execution-cost contract: 10 bps fee
and 5 bps slippage per one-way execution. A mismatch fails closed before a
session starts; no alternate technical cost simulation is silently accepted.

The full candle history, ledger, trades and fingerprints are atomically replaced
as one state file. Replaying unchanged candles must reproduce the same portfolio
and fingerprint.

## Autonomous running loop

automation/paper_forward_loop.py connects the feed and the state machine.

One-shot initialization:

python -m automation.paper_forward_loop ^
  --candidate frozen_candidate.json ^
  --state shadow.json ^
  --receipt shadow-feed-receipt.json ^
  --max-iterations 1

Continuous paper-forward mode:

python -m automation.paper_forward_loop ^
  --candidate frozen_candidate.json ^
  --state shadow.json ^
  --receipt shadow-feed-receipt.json

The default polling interval is derived from the candidate candle interval and
capped at 15 minutes. The process can be stopped with Ctrl+C; the last successful
state remains intact. A later process restart validates the saved state and
resumes using the candidate interval stored there; the original candidate file
is not required for resume. If the state is missing after initialization, the
loop fails closed rather than silently starting another session. Restore the
matching state or select a new state path for an intentional independent run.

The loop holds exclusive locks for its state and optional receipt paths for
its entire lifetime, including polling waits. A conflicting process exits
without modifying either file. The adjacent `.lock` targets must not be
deleted while a process may be running, and the `.initialized.json` marker
must be preserved to detect accidental state loss.

This loop is an operational shadow simulator, not a research-evidence producer.
Its output must remain outside research/evidence and cannot alter gates or
promotion state.

## Safety

Every start/update/loop path requires:

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

There is no broker client, order API, exchange account credential, or automatic
promotion path in the paper-forward implementation.
