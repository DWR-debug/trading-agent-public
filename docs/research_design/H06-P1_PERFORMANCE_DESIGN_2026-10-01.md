# H06-P1 Sector-Neutral Residual Momentum — Performance Design

Stand: 2026-10-01

## Status

DESIGN-ONLY / NO PERFORMANCE AUTHORIZATION

This document defines a new, fixed-rule performance research object derived from the already coverage- and PIT-validated H06 repair. It does not authorize execution.

## Research object

Trial family: H06-P1
Parent: H06 sector-neutral residual momentum repair
Universe: `validation_2026_09_25_sector_neutral_residual_momentum_repair`

Fixed universe:
- Technology: TXN, ADI, AMAT
- Healthcare: MDT, SYK, BDX
- Industrials: ETN, ITW, GD
- Consumer Staples: CL, KMB, GIS
- Utilities: AEP, XEL, DTE

Data contract:
- Daily OHLCV
- 3,500-session common-calendar snapshot
- 2,798 research sessions
- 702 holdout sessions
- signal decision uses only information available on the decision bar
- execution is on the following actionable session

## Fixed signal

Raw momentum score:

`close[t-21] / close[t-252] - 1`

Treatment H06-P1:
- within each fixed sector, compute the equal-weight sector mean of the three raw scores;
- residual score = raw score minus that sector mean;
- within each sector, choose exactly one long: highest residual score;
- within each sector, choose exactly one short: lowest residual score.

Control H06-P1-C:
- same sector-by-sector construction;
- use the raw momentum score instead of the residual score.

Thus both arms contain exactly:
- 5 long positions, one per sector;
- 5 short positions, one per sector;
- equal absolute position weights;
- gross exposure = 1.0;
- net exposure = 0.0.

No leverage is used.

## Rebalance and execution

Signals are recomputed on each research decision bar.
The resulting target positions are applied on the immediately following actionable session.
No rebalance-frequency variant is permitted.

## Evaluation

The formal runner must evaluate both arms symmetrically under the existing unchanged 13-gate framework, including:
- research and holdout results;
- rolling windows;
- cost/slippage stress;
- control-relative non-deterioration checks where applicable.

No parameter, threshold, horizon, asset, sector-map or variant search is permitted.
The holdout is not available for selection.

## Provenance and fail-closed requirements

The formal path must require:
1. the immutable H06 coverage receipt;
2. the immutable H06 PIT receipt;
3. a frozen input bundle;
4. a fixed preregistration fingerprint;
5. an exact source-code fingerprint;
6. explicit performance authorization for this exact trial ID;
7. paper-only safety invariants.

Any identity mismatch is a hard failure with no scientific interpretation.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

No real orders, brokerage credentials, or live execution are part of this research object.

## Next gate

Implement deterministic runner + structural/mutation tests + readiness receipt.
Only after those pass should a separate authorization object be created.
