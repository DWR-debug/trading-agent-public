# Deep Research Frontier — 2026-10-03

## Scope

Broad, source-first search for economically distinct information channels that can be researched without paid data. Discovery inventory only; not performance evidence.

Research sequence:
1. mechanism hypothesis;
2. exact source and publication-time contract;
3. synthetic PIT/leakage mutation tests;
4. free/public historical feasibility;
5. immutable input preservation;
6. independent reproduction;
7. only then a fresh preregistration and separate performance authorization.

No item authorizes performance, holdout selection, parameter search, threshold search, horizon search, asset search, family ranking, promotion or live execution.

## Public source map

SEC: public EDGAR filing metadata, submissions and XBRL. Form 13F data sets are as-filed and currently cover July 2013 through August 2026. Form N-PORT data sets currently cover October 2019 through June 2026 and contain monthly portfolio holdings. Fails-to-deliver data run from February 2004 through September 2026 and represent outstanding aggregate balances by settlement date.

FINRA: Daily Short Sale Volume and bi-monthly Short Interest are separate products. FINRA explicitly distinguishes daily trade-date short volume from short-interest positions and notes that daily files are not consolidated across all trading venues.

Treasury/CFTC: Treasury auction releases expose bidder-category demand fields. CFTC COT provides long historical positioning and distinguishes report dates from release dates; the normal release clock is 3:30 p.m. ET.

FRED/ALFRED: real-time periods, release dates and vintage dates support explicit historical information sets. ALFRED is designed to retrieve what was known at earlier dates.

BEA: Input-Output tables expose direct and indirect industry requirements plus historical tables. Historical revisions must be treated explicitly.

USPTO/PatentsView: public patent metadata, assignee/inventor relationships and bulk/API access are available. Application, publication and grant dates are distinct events.

Wikimedia Pageviews: public historical attention proxy. Not equivalent to investor attention; entity mapping, redirects, missing pages and data-quality incidents must be explicit.

## New candidate mechanisms

### Q133 — Settlement-Pressure Divergence
Inputs: SEC Fails-to-Deliver, FINRA Daily Short Sale Volume, OHLCV.
Mechanism: fixed disagreement state between short-sale flow intensity and lagged outstanding FTD balance.
Orthogonality: trading flow plus settlement inventory, rather than either alone.
PIT risks: FTD is an outstanding balance, not individual fail age; semi-monthly publication; CUSIP/ticker mapping.

### Q134 — Short-Interest Stock-vs-Flow Disagreement
Inputs: FINRA Short Interest, FINRA Daily Short Sale Volume, OHLCV.
Mechanism: fixed categorical state for high-flow/low-stock, low-flow/high-stock and aligned cases.
Orthogonality: uses FINRA's explicit distinction between trade-date flow and position snapshots.
PIT risks: discrete short-interest dates and venue completeness.

### Q135 — Innovation Confirmation Gap
Inputs: SEC Form 4, USPTO patent application/publication/grant metadata, OHLCV.
Mechanism: fixed relative timing state for patent events and open-market insider purchases.
Rules: use SEC acceptance time; freeze transaction-code inclusion; distinguish application/publication/grant dates.
PIT risks: issuer/assignee mapping and event-date semantics.

### Q136 — Patent Novelty × Public Attention
Inputs: PatentsView, Wikimedia Pageviews, OHLCV.
Mechanism: backward-only technological novelty proxy combined with pageview surprise.
Critical rule: forward citations are future information and cannot define same-date novelty.
Cheap falsification: future-mutation test must fail cleanly while backward-only implementation remains invariant.

### Q137 — Disclosure-Processing Congestion
Inputs: SEC filing acceptance timestamps, OHLCV-derived market activity, filing form/category.
Mechanism: fixed rolling filing-density state before a decision point.
Research motivation: 2026 work links disclosure timing to information-processing frictions.
PIT risks: acceptance/publication time, amendments and duplicate accessions.

### Q138 — Fund-Crowding Shock
Inputs: SEC N-PORT, SEC 13F, OHLCV.
Mechanism: fixed fund-ownership overlap/concentration state from publicly disseminated filings.
Orthogonality: portfolio-network state rather than price correlation or one-manager transition.
PIT risks: N-PORT volume, dissemination cutoffs and accession lineage.

### Q139 — Treasury-Demand × Equity Rate-Sensitivity
Inputs: Treasury auction results, SEC/XBRL financial facts, OHLCV.
Mechanism: fixed issuer financing-sensitivity descriptor interacted with fixed auction-demand states.
PIT risks: XBRL concept revisions and auction publication timing.

### Q140 — CFTC Positioning × Equity Commodity-Exposure Regime
Inputs: CFTC COT, OHLCV, fixed industry/issuer exposure descriptors.
Mechanism: fixed positioning state × fixed lagged commodity-exposure state.
PIT risks: COT report date versus release date and future classification leakage.

### Q141 — Institutional Calendar Collision × Liquidity
Inputs: historical index-rebalance calendars, ETF rebalance/roll schedules, futures expiry/roll calendars, options expiration calendars, OHLCV.
Mechanism: fixed count of coincident scheduled institutional-demand events plus fixed liquidity state.
PIT risks: historical event reconstruction and pre-announcement membership.

### Q142 — Supply-Chain Macro Shock Exposure
Inputs: BEA Input-Output requirements, FRED/ALFRED, issuer/industry mapping, OHLCV.
Mechanism: fixed industry exposure matrix multiplied by the correct real-time macro vintage.
PIT risks: BEA revisions, concordance and issuer classification.

### Q143 — Public OSS Release Externality
Inputs: public GitHub repositories/releases, SEC issuer disclosures, OHLCV.
Mechanism: material public software release as an ecosystem information shock for pre-registered complements/competitors.
PIT risks: historical event retention and meaningful-release classification.
Cheap falsification: start with a small hand-registered event set.

### Q144 — Attention-Response Gap
Inputs: SEC EDGAR, Wikimedia Pageviews, OHLCV.
Mechanism: immutable post-filing pageview-surprise state followed only by a separately authorized next-session study.
Relationship to Q130: Q130 studies the information-to-response clock; Q144 isolates abnormal attention response.
PIT risks: page-title/entity mapping and measurement latency.

### Q145 — Cross-Asset Policy State
Inputs: Treasury auction results, CFTC COT, FRED/ALFRED, OHLCV.
Mechanism: fixed state machine for unusual Treasury demand plus unusual CFTC positioning, with explicit release clocks and macro vintages.
PIT risks: mixed frequencies and asynchronous clocks.

## Feasibility priority

Lowest-cost, highest-information candidates: Q133, Q134, Q135, Q137, Q139, Q140 and Q144.

Heavier but potentially useful: Q138 and Q142.

Exploratory and tightly bounded: Q143 and Q145.

Absence of a free historical source is a valid negative result. No look-ahead approximation is permitted.

## Source references

SEC Form 13F: https://www.sec.gov/data-research/sec-markets-data/form-13f-data-sets
SEC Form N-PORT: https://www.sec.gov/data-research/sec-markets-data/form-n-port-data-sets
SEC Fails-to-Deliver: https://www.sec.gov/data-research/sec-markets-data/fails-deliver-data
FINRA Short Sale Volume: https://www.finra.org/finra-data/browse-catalog/short-sale-volume
CFTC Historical COT: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/index.htm
CFTC Release Schedule: https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm
FRED observations and vintages: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
ALFRED real-time periods: https://fred.stlouisfed.org/docs/api/fred/realtime_period.html
BEA Input-Output: https://www.bea.gov/data/industries/input-output-accounts-data
