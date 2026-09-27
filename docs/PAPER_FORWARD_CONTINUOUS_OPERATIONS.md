# Continuous paper-forward operation

The project now has a persistent operational paper portfolio that is separate
from research evidence.

The scheduled workflow executes one bounded paper-forward update every 15
minutes on the public repository. The durable state is committed under
ops/paper_forward/state/ so an ephemeral GitHub runner can resume from the last
accepted candle.

The simulation uses the frozen operational canary
paper-forward-operational-canary-btcusdt-1h-v1:
- BTCUSDT
- 1h closed candles
- EUR 500 hypothetical starting capital
- 1x leverage
- 10 bps fee
- 5 bps slippage
- existing strategy-engine parameters frozen in the candidate file

The workflow is not a broker connection. It never creates exchange orders and
does not write research/evidence or promotion state.

Each run:
1. checks all paper-only safety invariants;
2. restores the existing schema-v2 state if present, otherwise initializes it
   from a bounded historical Binance warm-up;
3. fetches only closed candles with a bounded fetch window;
4. applies the existing state/lock/fingerprint validation;
5. stores the updated state and feed receipt;
6. commits only the operational state/receipt when the state changed.

A missed schedule does not create synthetic candles. If the bounded feed window
cannot bridge a real data gap, the update fails closed and the previous state
remains untouched in Git history.

The repository state is operational telemetry, not scientific evidence.
Forward P&L is descriptive only and cannot promote a candidate.

Safety invariants:
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
