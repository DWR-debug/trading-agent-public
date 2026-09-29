# Q097 — Public Short-Flow / Ownership Frontier — 2026-09-29

**Status:** PREREGISTERED_DESIGN_ONLY / unranked
**Scope:** source and PIT feasibility only; no performance evaluation

## I15 — Fails-to-Deliver Stress Change

Source: SEC Fails-to-Deliver Data. The SEC publishes settlement-date FTD balances, with public history from February 2004. Before September 16, 2008, only records with at least 10,000 shares were included; from that date onward all securities with an FTD balance are included.

Frozen feasibility construction:
- use settlement date as the source observation date;
- use only records publicly released by the SEC before the decision cutoff;
- preserve CUSIP, symbol, quantity and source file fingerprint;
- normalize only mechanically; no search for thresholds, windows or sign conventions;
- treat the pre-2008 coverage rule change as an explicit regime boundary rather than silently pooling the distributions.

Potential signal object: change in issuer-level FTD stress relative to the issuer's own previous reported FTD state. Any precise transformation must be frozen before performance authorization.

## I16 — Short-Interest Change

Source: FINRA Short Interest Reporting. FINRA requires member firms to report short positions twice monthly, with publication dates determined by the reporting schedule.

Frozen feasibility boundary:
- settlement date is the economic observation date;
- publication date is the information-availability boundary;
- a short-interest value becomes visible only after the official publication cutoff;
- issuer/security identifiers and corporate-action mapping must be fixed before validation;
- no publication-schedule backfilling from later files is allowed.

Potential signal object: change in reported short interest or days-to-cover state between two published observations. Thresholds, horizons and normalization are not yet frozen.

## I17 — Beneficial-Ownership Change

Source: SEC Schedule 13D/13G. SEC guidance and EDGAR entity pages expose Schedule 13D/13G filings and amendments.

Frozen feasibility boundary:
- use EDGAR acceptance timestamp as PIT anchor;
- distinguish 13D, 13D/A, 13G and 13G/A explicitly;
- preserve the accession identifier and amendment chain;
- map beneficial owner, issuer and security through stable identifiers;
- never use a later amendment to rewrite an earlier as-of state.

Potential signal object: newly disclosed beneficial-ownership increase/decrease or ownership-state transition. Exact aggregation and sign mapping must be frozen before performance.

## I18 — Proposed Insider-Sale Flow

Source: SEC Form 144. Since April 13, 2023, certain Form 144 notices must be filed electronically on EDGAR; SEC guidance states the submissions are publicly disseminated the same day. A current EDGAR filing demonstrates the public accepted timestamp and issuer/reporting-person linkage.

Feasibility consequence:
- this channel cannot silently be treated as a 2011–2025 backtest input;
- the electronic historical window begins only with the applicable 2023 requirement;
- any performance use would require an explicitly frozen study start and a separate coverage analysis;
- proposed sale quantity, reporting person, issuer and security mapping must be preserved with acceptance timestamps;
- pre-electronic paper-era observations must not be reconstructed from later data.

## Historical PIT anchors added in Q098

The source-depth audit uses concrete public EDGAR anchor filings rather than assuming that the oldest submission chunk contains every form family:

- Schedule 13G: accession 0001020066-11-000014, accepted 2011-06-09.
- Form 144: accession 0001921094-23-000806, accepted 2023-11-06.

These anchors demonstrate historical public visibility and provide acceptance-time PIT anchors for subsequent coverage work. They do not constitute performance evidence.

## Research governance

All four candidates remain unranked. No performance authorization, holdout selection, parameter search, asset selection or automatic promotion is permitted.

Required sequence:

1. source archive coverage;
2. PIT/security/entity mapping;
3. immutable source snapshots;
4. mutation and release-timestamp checks;
5. fresh symbol-disjoint validation;
6. separate one-shot performance authorization.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

## External source basis

SEC Fails-to-Deliver Data: https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data
FINRA Short Interest Reporting: https://www.finra.org/filing-reporting/regulatory-filing-systems/short-interest
SEC Beneficial Ownership / Schedule 13D/13G: https://www.sec.gov/rules-regulations/staff-guidance/corporation-finance-interpretations/exchange-act-sections-13d-13g-regulation-13d-g-beneficial-ownership-reporting
SEC Form 144 electronic filing: https://www.sec.gov/submit-filings/filer-support-resources/how-do-i-guides/file-form-144-electronically