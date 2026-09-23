# Task: UTC Timestamp Consistency

Goal:
Make all historical market-data ingestion paths consistently use UTC-aware timestamps.

Scope:
- data/csv_loader.py
- data/market_store.py
- affected tests
- regression tests where useful

Requirements:
1. Keep data/quality.py strict: Candle timestamps must remain timezone-aware and UTC.
2. Do not weaken or remove existing quality checks.
3. Binance loader behavior must remain unchanged.
4. CSV timestamps without an explicit timezone must be interpreted consistently as UTC.
5. CSV timestamps containing an offset must be normalized to UTC.
6. MarketDataStore.load() must produce UTC-aware UTC timestamps.
7. Update tests that currently construct valid naive timestamps.
8. Preserve tests that specifically verify naive timestamps are rejected by validate_candles().
9. Do not modify trading execution, paper-trading safety, or live-trading guards.
10. Run the complete pytest suite.
11. Only commit if all tests pass.
12. Commit message:
   "UTC-Zeitstempel im Marktdatenpfad vereinheitlichen"

Before editing:
- inspect the relevant files and existing tests
- do not guess about APIs, paths, or field names

After editing:
- run python -m pytest -q
- report the exact test count
- verify:
  PAPER_ONLY is True
  LIVE_TRADING_ENABLED is False
