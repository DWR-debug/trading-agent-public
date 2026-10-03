# Deep Public-Domain Frontier II — 2026-10-03

This is a discovery-only extension of the research frontier.

## Q146 — Climate/Weather Operational Exposure

Mechanism: an exogenous weather shock can alter operations, transport, energy usage and regional demand for firms with geographically concentrated exposure.

Sources: NOAA/NCEI historical weather and climate data; SEC filings for issuer location/segment disclosures; OHLCV.

Conservative construction: freeze a public geographic exposure map from issuer disclosures; use only weather observations available before the next eligible session. Do not infer geographic exposure from future returns.

Main risks: firm-location changes, station-to-firm mapping, revisions, extreme-event timestamp semantics.

## Q147 — Electricity Load Imbalance × Industrial Exposure

Mechanism: unusual electricity demand or power-system stress may propagate differently to electricity-intensive industries.

Sources: EIA electricity operating data and bulk downloads; fixed industry exposure map; OHLCV.

Conservative construction: fixed load/deviation state using a documented public data release and a lagged industrial exposure map.

Main risks: EIA data are updated continuously rather than on a single universal release clock; use a frozen release/vintage boundary or deliberately shift to next-session use.

## Q148 — Petroleum Inventory Shock × Sector Sensitivity

Mechanism: energy inventory surprises can affect transportation, chemicals, refiners and other sectors asymmetrically.

Sources: EIA petroleum/inventory data; fixed sector sensitivity; OHLCV.

Conservative construction: use a fixed inventory state and predeclared sector exposure classes. No threshold optimization.

Main risks: publication schedule and subsequent EIA updates; require a release-date receipt and a vintage policy.

## Q149 — Federal Procurement Shock × Public Contractor

Mechanism: unusually large or newly started federal awards may create an information event for listed contractors.

Sources: USAspending API/bulk award files; SEC issuer/CIK mapping; OHLCV.

Conservative construction: fixed award-event classes based on transaction/award dates and recipient identity. The information boundary must use the public dissemination timestamp/version available to the compiler.

Main risks: transaction amendments and database updates; recipient name changes; award action date is not automatically a public-information timestamp.

## Q150 — Legal Docket Intensity × Issuer

Mechanism: abnormal public litigation activity may alter uncertainty or information-processing around an issuer.

Sources: CourtListener case-law and RECAP/PACER-derived public records; SEC issuer mapping; OHLCV.

Conservative construction: fixed daily count/state of new publicly observable proceedings for a pre-registered issuer set. Use next-session decisions unless a more exact public timestamp is proven.

Main risks: coverage is not universal; public-record availability can differ by jurisdiction; docket time and public observation time are different concepts.

## Q151 — Regulatory/Enforcement Shock

Mechanism: a newly public regulatory or enforcement event can create an exogenous information state.

Sources: SEC enforcement/administrative releases, CFTC enforcement publications, public government releases, SEC issuer mapping, OHLCV.

Conservative construction: a fixed event taxonomy and timestamp contract. No NLP score tuning in the first feasibility stage.

Main risks: release-time semantics, duplicates, amendments, event classification and entity mapping.

## Source facts supporting feasibility

EIA's current public API exposes large electricity, petroleum and natural-gas collections and offers bulk downloads without requiring an API key. The API itself requires registration and is continuously updated. This makes EIA an unusually large public source but also means the PIT boundary must be explicit.

NOAA Climate Data Online provides free historical weather and climate archives; its API uses a token with stated request limits. Bulk/archive access should be preferred when practical.

USAspending's current public API endpoint documentation states that its endpoints do not require authorization and supports award, transaction, bulk-download and reporting-publication-date endpoints.

CourtListener currently exposes thousands of jurisdictions and public case-law/RECAP-related data through APIs and bulk interfaces. Coverage is not complete and must be measured rather than assumed.

## Scientific boundary

All six candidates remain discovery/source-feasibility only. No candidate in this wave authorizes:
- performance;
- holdout selection;
- asset selection;
- parameter/threshold search;
- horizon search;
- family ranking;
- promotion;
- live execution.

## URLs

EIA Open Data: https://www.eia.gov/opendata/
EIA documentation: https://www.eia.gov/opendata/documentation.php
NOAA CDO: https://www.ncei.noaa.gov/cdo-web/
NOAA CDO API: https://www.ncei.noaa.gov/cdo-web/webservices/v2
USAspending API: https://api.usaspending.gov/docs/endpoints
CourtListener help/API: https://www.courtlistener.com/help/
