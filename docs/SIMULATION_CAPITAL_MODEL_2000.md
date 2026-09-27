# Simulation Capital Model — EUR 2,000

**Effective date:** 2026-09-27

## Canonical simulation reference

The project's current hypothetical starting/reference capital for new capital-dependent simulations is **EUR 2,000**.

This is strictly fictional: actual available capital remains **EUR 0**. No real account, broker or order path is enabled.

Safety remains:
- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `ORDERS_ENABLED=False`
- `AUTOMATIC_PROMOTION=False`

## Backward compatibility

The existing **EUR 500** BTCUSDT operational paper-forward canary remains a separate historical time series and is not silently rebased to EUR 2,000.

The existing `INITIAL_CAPITAL_EUR = 500` engine baseline also remains available for backward-compatible or explicitly historical replays. New capital-dependent simulations use the explicit EUR 2,000 project reference.

## New EUR 2,000 simulation lanes

The project now has a dedicated 2,000-EUR operational shadow lane and a dedicated formal 2,000-EUR candidate lane.

The operational shadow is engineering/monitoring only. It creates no Research Evidence and cannot trigger promotion.

The formal candidate lane remains fail-closed and idles until exactly one frozen candidate satisfies the unchanged `VALIDATED_PASS` evidence contract.

## Scaling rule

Changing the simulation capital changes accounting scale; it does not create an alpha signal. The capital change therefore does not justify changing signals, costs, leverage, risk gates, or selecting strategies from absolute EUR outcomes.

All scientific and safety boundaries remain unchanged.
