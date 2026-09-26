# Q019 — Treasury Auction Signal Contract — 2026-09-26

**Status: PREREGISTERED_COVERAGE_ONLY**

This gate follows the objective Q018 source-feasibility result. It does not evaluate performance.

## Fixed mechanism

For each U.S. Treasury 10-Year Note auction after the first, compare the bid-to-cover ratio with the immediately preceding 10-Year Note auction. Positive change is `+1`, negative change `-1`, unchanged `0`.

## Point-in-time rule

`record_date` is the information timestamp. The event becomes actionable only on the first eligible common trading date strictly after `record_date`. Events without an in-window next bar are recorded as terminal rather than silently removed.

## Data contract

Required fields: `record_date`, `auction_date`, `cusip`, `bid_to_cover_ratio`.

The preflight must verify deterministic ordering, duplicate handling, numeric bid-to-cover values, `record_date >= auction_date`, and mapping to the fixed common market calendar.

## Governance

No parameter, threshold, asset, feature, horizon, or variant search. No holdout use. No P&L or forward-return calculation. No performance authorization or automatic promotion.
