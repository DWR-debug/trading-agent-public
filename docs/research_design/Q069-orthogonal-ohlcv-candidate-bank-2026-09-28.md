# Q069 — Orthogonal OHLCV Candidate Bank

**Date:** 2026-09-28  
**Status:** PREREGISTERED / DESIGN-ONLY  
**Issue:** #536

## Purpose

Q069 broadens the alpha research beyond the frozen Q067 six-sleeve construction. The five candidates are fixed ex ante and are not ranked by observed performance.

## Candidate pool

| ID | Candidate | Fixed rule | Intended distinction |
|---|---|---|---|
| C7 | LOW_MAX_21 | Long the two symbols with the lowest maximum daily close-to-close return over 21 sessions. | Extreme-return/lottery characteristic. |
| C8 | LOW_IDIO_VOL_273 | Long the two symbols with the lowest 273-session residual volatility after removing the equal-weight universe return component. | Residual risk rather than beta level. |
| C9 | LONG_TERM_REVERSAL_756 | Long the two symbols with the lowest 756-session cumulative close return. | Long-horizon contrarian signal. |
| C10 | TREND_EFFICIENCY_63 | Long the two symbols with the highest absolute 63-session net return divided by summed absolute daily returns. | Path persistence rather than raw trend magnitude. |
| C11 | VOLUME_CONFIRMED_TREND_126 | Long the two symbols with the highest 126-session return multiplied by 21-session average volume divided by prior 126-session average volume. | Price continuation conditioned on activity. |

Ties use ascending-symbol order. All targets are long-only and equally weighted, with gross exposure at most 1.0.

## Point-in-time boundary

A decision at close `t` can use only bars through `t`. Future bars and next-session OHLC/volume are prohibited. A later performance trial would enter on a subsequent open.

## Research sequence

Q069 itself performs no P&L evaluation.

1. Code-level and PIT mutation tests.
2. Fresh symbol-disjoint coverage.
3. PIT validation.
4. Separately authorized fixed-rule performance.
5. Existing 13-gate evaluation and immutable reconciliation.

No holdout observation may alter the candidate definitions.

## Literature basis

C7 is motivated by the MAX anomaly studied by Bali, Cakici & Whitelaw (2011), DOI 10.1016/j.jfineco.2010.08.014. 

C8 is motivated by Ang, Hodrick, Xing & Zhang (2006), DOI 10.1111/j.1540-6261.2006.00836.x, which studies the cross-section of volatility and expected returns. 

C9 is motivated by De Bondt & Thaler (1985), DOI 10.1111/j.1540-6261.1985.tb05004.x. 

C10 is an explicitly project-generated hypothesis; the ratio is a deterministic path-efficiency measure rather than a literature replication claim.

C11 is motivated by Lee & Swaminathan (2000), DOI 10.1111/0022-1080.00280, on the relation between price momentum and trading volume. 

These sources justify research hypotheses only; they do not constitute evidence that any Q069 candidate will pass the project gates. Jegadeesh & Titman (1993), DOI 10.1111/j.1540-6261.1993.tb04702.x, is used only as background for the momentum component. 

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False