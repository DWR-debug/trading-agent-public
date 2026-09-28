# C30 — Risk-Text Peer Propagation Feasibility — 2026-09-28

## Status

DESIGN / MACHINE-FEASIBILITY COMPLETE

This document freezes the mathematical feasibility layer only. It does not
authorize performance, rank C30 against other mechanisms, select a holdout or
permit promotion.

## Information channel

C30 uses completed SEC 10-K Item 1A risk-factor text rather than price
correlation, industry membership or MD&A topic similarity.

The 2026 Journal of Empirical Finance paper by Yuan & Zhang describes a
risk-similarity peer network derived from 10-K risk disclosures and reports
return predictability. The project treats that published result as external
hypothesis evidence, not as project evidence.

Source:
Yuan & Zhang (2026), Risk-based peer networks and return predictability:
Evidence from textual analysis on 10-K filings, Journal of Empirical Finance
88, 101754, DOI 10.1016/j.jempfin.2026.101754.

## Frozen deterministic feasibility construction

### 1. Filing visibility / PIT

Each filing record contains:

- issuer symbol;
- SEC acceptance timestamp;
- stable accession identifier;
- extracted Item 1A risk-factor text.

At decision time t, only filings with acceptance timestamp <= t are visible.
For each symbol, the latest visible filing is used.

Two filings for the same symbol at exactly the same acceptance timestamp are
a hard error. The feasibility layer does not invent an amendment tie-break.

### 2. Text representation

The first implementation uses:

- lowercase ASCII alphanumeric tokenization;
- no learned tokenizer;
- no external stop-word list;
- term frequency within the visible filing;
- smoothed inverse document frequency:
  log((1 + N) / (1 + df)) + 1;
- L2 normalization.

The vocabulary and IDF are fit only from the complete visible as-of corpus.

### 3. Peer graph

Cosine similarity of the normalized risk-text vectors is used as the peer
weight.

All non-self visible peers are eligible. There is no top-K search and no
similarity threshold. Because TF-IDF vectors are non-negative, the raw cosine
weights are non-negative.

### 4. Lagged peer state

For issuer i at decision time t:

signal_i(t) =
  sum_j!=i similarity(i,j,t) * prior_return_j(t)
  / sum_j!=i similarity(i,j,t)

where only visible filings are used and prior returns are supplied separately.

A zero denominator produces a neutral state of 0.0 rather than a fabricated
peer value.

## PIT / leakage contract

The following must hold before any performance validation:

- a filing accepted after t cannot alter the signal at t;
- a future replacement of the current filing cannot alter the signal at t;
- the t+1 filing cannot enter the t decision;
- future text cannot alter the as-of vocabulary or IDF;
- missing or contradictory filing identity fails closed.

Synthetic mutation tests for the first four conditions are included in the
machine-feasibility suite.

## Public data feasibility

The SEC states that EDGAR submissions history and XBRL APIs are publicly
accessible without authentication or API keys, and the EDGAR filing archive is
publicly accessible. This establishes the data channel, but historical
completeness of the Item 1A text and exact acceptance timestamps still require
a repository-specific archive audit before performance authorization.

Project source for this infrastructure decision:
SEC EDGAR Application Programming Interfaces, reviewed 2026-09-28.

## Required next gate

Build a historical SEC archive audit on the actual planned research universe:

1. issuer/CIK/ticker mapping;
2. filing accession and acceptance timestamps;
3. Item 1A extraction completeness;
4. coverage by issuer and study date;
5. immutably persisted raw filing artifacts before any PIT transformation;
6. snapshot fingerprint and governance receipts.

No performance evaluation is part of this gate.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
