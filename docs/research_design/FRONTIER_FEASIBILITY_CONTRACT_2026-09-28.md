# Frontier Feasibility Contract — 2026-09-28

## Scope

This document freezes the first machine-testable feasibility layer for the
unusual frontier. It does not authorize performance, ranking, holdout
selection or promotion.

The first two mechanisms entering executable feasibility are:

- C29 — ILLUSION_MOMENTUM_GAP
- M4 — INDUSTRY_RELATIVE_REVERSAL_RESIDUAL

The purpose is to separate mechanism integrity from data acquisition and from
performance evaluation.

## C29 — Illusion Momentum Gap

Fixed construction:

1. Take completed daily simple returns through decision time t.
2. Compute the cumulative compounded return:
   prod(1 + r_d) - 1.
3. Compute the arithmetic sum of the same simple returns:
   sum(r_d).
4. Signal quantity:
   compound_return - arithmetic_sum.

The first machine-testable implementation fixes a 21-session history solely as
the feasibility contract. No lookback, transformation, threshold, ranking or
asset search is permitted after this freeze.

The literature source is Iwanaga & Hirose (2026), Illusion momentum and
cross-sectional returns, DOI 10.1016/j.pacfin.2026.103063. The published
paper describes the predictor as the gap between cumulative and cumulative-sum
returns and reports evidence in Japanese and U.S. stocks. The project does not
treat those published results as project evidence.

PIT contract:

- decision-time calculations may read only observations at or before t;
- mutation of every observation after t must leave the result unchanged;
- mutation of t+1 must leave the result unchanged.

## M4 — Industry-Relative Reversal Residual

Fixed construction:

1. At decision time t, compute each stock's trailing 21-session simple return.
2. Compute the equal-weight mean trailing return inside each industry.
3. Residual:
   stock_return - industry_mean_return.

The eventual reversal exposure is a deterministic sign transformation of this
residual; the current feasibility layer intentionally stops before portfolio
formation.

M4 requires a point-in-time industry/security mapping. A current industry
classification is not sufficient for historical validation if membership or
classification can change. The project must therefore freeze the security
master/industry mapping before performance authorization.

Literature source: Stosik & Zaremba (2026), Short-term reversal
persists globally—If properly measured, Economics Letters 267, 113113,
DOI 10.1016/j.econlet.2026.113113. The paper reports industry-adjusted
reversal evidence across 64 countries. It states that its underlying data
cannot be shared; the project will therefore build its own reproducible public
price/PIT-classification implementation rather than copy the research sample.

## Feasibility status of the remaining frontier

### C30 — Risk-Text Peer Propagation

The SEC provides public EDGAR submissions history and XBRL APIs without API
keys, and also exposes the EDGAR filing archive. This establishes a public
data channel, but it does not by itself establish a historical, complete,
PIT-safe text dataset for every required issuer/date. The next gate is an
archive-completeness and acceptance-timestamp audit before any signal code is
frozen.

Literature source: Yuan & Zhang (2026), Risk-based peer networks and return
predictability: Evidence from textual analysis on 10-K filings, Journal of Empirical Finance 88, 101754, DOI 10.1016/j.jempfin.2026.101754.

### C31 — News Sentiment Persistence State

The published study uses RavenPack data. That is not a zero-cost/public data
contract for this project. C31 therefore remains design/feasibility-only until
a public, reproducibly retained historical news corpus with article timestamps
and stable identifiers is identified and audited.

Literature source: The persistence of news sentiment: Implications for
return predictability, Economics Letters 260, 112803,
DOI 10.1016/j.econlet.2025.112803.

### M5 — Benchmark Demand Shock Clock

FTSE Russell publicly publishes reconstitution calendars and additions/deletions
around the Russell US Indexes. For 2026 the US indexes moved to a semi-annual
June/December schedule; the December 2026 dates include 13 November preliminary
lists and 11 December implementation. The public event schedule is therefore
available, but historical completeness, identifier mapping and archive
preservation must be audited before a historical research panel is frozen.

The immediate next step is a document/archive completeness audit, not an event-
window search.

Sources:
- LSEG / FTSE Russell, “FTSE Russell announces 2026 Russell US Indexes
  Reconstitution schedule”, 2026-03-02.
- LSEG / FTSE Russell, “FTSE Russell announces December 2026 Russell US Indexes
  Reconstitution schedule”, 2026-09-01.
