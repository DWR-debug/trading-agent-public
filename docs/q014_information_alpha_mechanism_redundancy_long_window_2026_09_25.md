# Q014 Information-Alpha Mechanism Redundancy — Long Window — 2026-09-25

Q014 ist eine rein diagnostische Ein-Jahres-Erweiterung von Q013.

## Fixed window
- 2025-09-25 through 2026-09-24 (365 calendar days)
- Assets: SPY, TLT, GLD
- Event filter: international event with num_articles >= 3
- Features and mechanism groups unchanged from Q013

## Minimum data contract
- at least 80 common market-day observations
- at least 40 event windows
- otherwise: DATA_INSUFFICIENT

## Prohibitions
- no feature selection
- no asset selection
- no horizon selection
- no parameter/threshold search
- no holdout selection
- no performance trial
- no gate changes

## Point-in-time
The Q011/Q012 event-to-market-day contract remains unchanged. Same-day returns are not used.

## Safety
PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False; automatic_promotion=False.
