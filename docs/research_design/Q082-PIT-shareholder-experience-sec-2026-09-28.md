# Q082 — PIT Shareholder-Experience Signal via SEC Shares Outstanding

**Date:** 2026-09-28  
**Status:** PREREGISTERED_DESIGN_ONLY / unranked  
**Issue:** #580

## Motivation

Riley & Zhou (2026), *Shareholder-weighted returns and stock return predictability*, constructs shareholder-cohort weights from daily turnover and uses them to estimate cumulative shareholder return, average shareholder return and a scale-invariant gain/loss ratio. The paper reports predictive relationships across one-, three- and six-month horizons. These findings are literature inputs only and are not project evidence.

The project currently has daily OHLCV data but not a daily historical shares-outstanding field. Q075 already contains feasibility probes for SEC Submissions and SEC Company Facts. The SEC documents `dei:EntityCommonStockSharesOutstanding` as an instant fact, while EDGAR filing metadata exposes acceptance timestamps.

## Proposed candidate family

Q082 is an adaptation, not a paper replication. It attempts to construct the same economic object using freely accessible SEC/XBRL data plus the project's canonical daily OHLCV data.

### C22 — SHAREHOLDER_WEIGHTED_CUM_RETURN

At each decision close, reconstruct the current shareholder-cohort weights from daily turnover using the latest shares-outstanding fact that was publicly available no later than the decision timestamp. Apply the fixed five-year daily survival-weighting construction and the seven-day lag convention. Compute the weighted cumulative return of the inferred current-holder cohorts.

### C23 — SHAREHOLDER_WEIGHTED_AVG_RETURN

Use the identical frozen cohort weights as C22. Compute the corresponding weighted average daily return of the inferred current-holder cohorts.

### C24 — SHAREHOLDER_GAIN_LOSS

Use the identical frozen cohort weights as C22. For each cohort, apply only the sign of its cumulative return and compute the weighted net fraction of current holders estimated to be above versus below their purchase price.

### C25 — SHAREHOLDER_EXPERIENCE_COMPOSITE

Equal-weight C22, C23 and C24 after deterministic within-decision normalization specified before validation. The normalization itself must be fixed before any performance work and must not be selected from results.

## PIT SEC data contract

For each security:

1. Freeze a security/CIK mapping with explicit historical effective dates.
2. Retrieve SEC Company Facts containing `dei:EntityCommonStockSharesOutstanding` and the associated reporting contexts.
3. Retrieve SEC Submissions or filing-header metadata that provides the EDGAR acceptance timestamp.
4. For a decision timestamp `t`, only facts from filings accepted on or before `t` are eligible.
5. Where multiple eligible facts exist, apply one deterministic source-order rule fixed before validation.
6. Carry the selected shares-outstanding value forward until a later eligible filing supersedes it.
7. Never infer a historical value from a later filing or from a current share-count snapshot.
8. Reject ambiguous multi-class/security cases unless the mapping explicitly defines which share class is represented by the traded symbol.

The SEC states that Company Facts are available through the XBRL API and that APIs are updated as filings are disseminated. EDGAR documentation describes acceptance timestamps as the time the submission was accepted. The project must nevertheless freeze the exact fetched source bytes and timestamps for every performance input.

## Turnover weighting

Use daily turnover derived from:

`turnover_t = volume_t / shares_outstanding_t`

The five-year cohort construction follows the literature's fixed seven-day lag and survival-product idea. The exact project implementation, including any necessary treatment of turnover above one, missing share counts, corporate actions and normalization, must be frozen as a source contract before coverage/PIT testing.

No arbitrary turnover cap, smoothing parameter, lookback search or sign reversal is permitted after seeing performance.

## Prerequisites

Before performance authorization:

- Complete historical security/CIK mapping with effective dates.
- Complete SEC source coverage for the candidate universe.
- Complete OHLCV coverage on the same decision calendar.
- PIT mutation tests for filing updates, ticker changes, share-count revisions and future-data insertion.
- Explicit multi-class handling.
- Immutable source snapshots and fingerprints.
- Fresh symbol-disjoint validation.
- Complete performance input bundle freeze.
- Separate one-shot performance authorization.

## Scientific governance

Q082 is exploratory and unranked. No candidate is promoted, discarded, ranked or combined based on performance before the preregistered validation sequence. Literature claims are not project evidence.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False

## Primary references

- Riley & Zhou (2026), International Review of Financial Analysis 118, 105367, DOI: https://doi.org/10.1016/j.irfa.2026.105367
- SEC EDGAR APIs: https://www.sec.gov/search-filings/edgar-application-programming-interfaces
- SEC EDGAR XBRL Guide 2026: https://www.sec.gov/file/xbrl-guide-2026-01-16
