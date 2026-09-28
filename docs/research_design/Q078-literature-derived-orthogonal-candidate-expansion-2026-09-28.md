# Q078 — Literature-Derived Orthogonal Candidate Expansion — 2026-09-28

## Status

**DESIGN_ONLY_UNRANKED**

Q078 expands the research frontier using documented interactions and information channels. It does not establish any performance conclusion.

## Candidate catalog

| ID | Family | Core construction | Primary data | PIT anchor |
|---|---|---|---|---|
| I11 | SEC_13F_TRADE_DISPERSION | cross-institution dispersion in quarterly holding changes | SEC 13F | filing acceptance datetime |
| I12 | SEC_13F_COMMON_OWNERSHIP_PEER_MOMENTUM | return signal propagated across firms with common institutional owners | SEC 13F + prices | filing acceptance datetime + prior completed returns |
| I13 | SEC_13F_ABNORMAL_OWNERSHIP_CHANGE | abnormal institutional ownership change after disclosed filings | SEC 13F + prices | filing acceptance datetime |
| I14 | EARNINGS_DISCLOSURE_NOVELTY | deterministic text novelty of first public earnings disclosure × fixed surprise state | SEC 8-K/10-Q/10-K/XBRL | filing acceptance datetime |
| O1 | IMPLIED_VOLATILITY_BORROW_PROXY | option-implied volatility spread/skew as a proxy for stock borrow conditions | option market data | source-specific timestamp / completed session |
| C16 | REVERSAL_MAX_INTERACTION | short-horizon reversal conditioned on prior-week maximum daily return | OHLCV | completed prior sessions |

## Ex-ante definitions

### I11 — Institutional trade dispersion

For each issuer and quarter, compute a fixed cross-sectional dispersion measure of institutional ownership changes across reporting managers. The action date is the first eligible trading session after the latest relevant filing acceptance cutoff.

The implementation must retain accession number, manager identifier, report period, filing acceptance timestamp and underlying holdings records.

### I12 — Common-institutional-ownership peer momentum

Construct the peer set from the overlap of institutional owners disclosed in 13F filings. The signal uses only completed historical returns from peers whose ownership relationship was publicly observable at the time of the decision.

No graph threshold, weighting scheme or lookback may be optimized after seeing performance.

### I13 — Abnormal institutional ownership change

Decompose disclosed institutional ownership into a fixed characteristic-expected component and an abnormal residual. Use only the first public filing information available before the action session.

The design must explicitly model the statutory disclosure delay and exclude subsequent amendments from earlier information sets.

### I14 — Earnings-disclosure novelty

Avoid non-deterministic LLM inference in the first implementation. Define novelty from a frozen vocabulary/term-frequency representation over the first public filing text, combined with a pre-specified earnings surprise measure derived from contemporaneously available XBRL facts.

This is deliberately a two-stage feasibility problem:
1. verify exact first-public filing and XBRL vintage;
2. only then test the deterministic text statistic.

### O1 — Option-implied borrow proxy

Use option-implied volatility spread/skew as an information variable rather than assuming that it is a free alpha source. The current literature indicates that much of its return predictability can be related to stock borrow fees; therefore the research contract must include explicit borrow/cost sensitivity and must not claim that the option signal itself is causal.

Historical option data availability is a hard gate. No candidate enters performance without complete historical coverage and exact timestamps.

### C16 — Reversal × MAX interaction

Condition a fixed short-horizon reversal statistic on the prior week's maximum single-day return. The objective is to test whether extreme recent price moves alter the reversal mechanism.

The construction uses only prior completed daily observations.

## Scientific sequence

1. source and schema feasibility;
2. fixed PIT contract;
3. frozen entity/security mapping;
4. fresh disjoint coverage;
5. mutation test;
6. fixed-rule performance authorization;
7. unchanged 13-gate evaluation.

No family is ranked before its pre-registered performance result. Holdout results cannot be used to choose between families.

## Motivation from external literature

- Comprehensive anomaly-interaction research documents recurring interaction clusters involving reversal, illiquidity, turnover and other limits-to-arbitrage variables, while also highlighting data-mining and trading-cost risks.
- Recent work on institutional holdings reports predictive content in 13F-based ownership measures, including institutional trade dispersion and common-ownership links.
- Recent work on option-implied volatility spread/skew argues that part of the apparent return predictability may proxy for stock borrow fees.
- Recent work on earnings disclosures finds that textual information can explain incremental short-window price variation beyond conventional earnings-surprise measures.

These papers motivate hypotheses only; none is evidence that a Q078 mechanism will pass this project's gates.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
