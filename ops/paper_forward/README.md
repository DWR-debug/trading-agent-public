# Paper-forward operational state

This directory contains the operational, paper-only simulation state for the
live market-data shadow process.

The candidate is an operational canary only. It is not a research candidate and
cannot alter research evidence, gates or promotion.

Persistent state is written under ops/paper_forward/state/ by the scheduled
workflow. The state contains the schema-v2 MTM portfolio ledger and immutable
input fingerprints. It uses only public closed Binance candles.

Safety invariants:
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
