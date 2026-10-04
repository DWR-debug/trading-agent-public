# Q185-Q186 — A-Priority Patent-Network and Legal-State Frontier

## Objective

This wave deliberately targets information channels that are economically orthogonal to price-only momentum/reversal families and to SEC filing-arrival signals.

**Q186:** upstream patent grant shock → fixed technological dependency graph → exposed downstream issuer.

**Q185:** legal-state machine → issuer exposure, using the earliest reproducibly observable public state rather than a return-derived lawsuit event.

## Literature basis

### Q186 — technological knowledge spillovers

Aghdasi and Tagade (LSE CEP Discussion Paper 2117, August 2025) study directed patent citations among publicly listed U.S. companies. They construct downstream exposure to new patents granted to technologically upstream firms and report positive abnormal returns around the upstream grant, with effects concentrated in immediate technological connections. They also separate technological knowledge spillovers from product-market rival and supplier channels.

This is substantially different from patent counts: the hypothesis is about **network-mediated information**, not firm innovation volume.

Primary literature:
- https://cep.lse.ac.uk/_NEW/PUBLICATIONS/abstract.asp?index=11712
- https://doi.org/10.1111/1475-679X.70071

### Q185 — corporate litigation

Billings, Holthausen, Petrovits and Wang (Journal of Accounting Research, 2026) assemble 174,782 federal-district-court lawsuits against 218,437 public-company lawsuit-defendants from 2006–2021. They document substantial heterogeneity in litigation and find that aggregate legal exposure is associated with increased return volatility and lower profitability; 23% of defendants experience a market-value decline exceeding 10% of current assets around the lawsuit filing.

The important design implication for this project is that litigation is a **persistent state process**, not merely a one-day event. The state machine is therefore explicitly separated from outcome labels.

Primary source:
- https://doi.org/10.1111/1475-679X.70071

## Public-source feasibility

### Q186

USPTO states that PatentsView Q4 2025 data contain disambiguated patent data through December 31, 2025 and are distributed through the USPTO Open Data Portal. USPTO patent-grant bibliographic data cover weekly patent grants from 1976 to present. USPTO also states that patent grants are issued electronically through Patent Center and are available immediately upon issue.

Sources:
- https://www.uspto.gov/subscription-center/2026/patentsview-releases-q4-2025-data-update
- https://developer.uspto.gov/product/patent-grant-bibliographic-datasgml
- https://www.uspto.gov/patents/apply/patent-center/egrants
- https://www.uspto.gov/learning-and-resources/official-gazette/official-gazette-patents

### Q185

CourtListener's RECAP archive contains millions of PACER dockets/documents and exposes dockets, docket entries, parties and attorneys through its PACER-data model. Coverage is broad but not universal; therefore a **coverage census is mandatory** and no universal federal-court coverage assumption is permitted.

Sources:
- https://courtlistener.com/coverage/
- https://courtlistener.com/recap/
- https://wiki.free.law/c/courtlistener/help/api/rest/v4/pacer-data

## Candidate contracts

### Q186 — UPSTREAM_PATENT_GRANT_SHOCK × TECHNOLOGY_EXPOSURE

1. Freeze a directed exposure graph from prior public patent citations and disambiguated assignee organizations.
2. At each patent grant, expose only downstream issuers whose relationship was observable before the grant decision point.
3. Use the grant/issue event as the information-state transition; never substitute later assignment or citation updates.
4. Keep corrections/withdrawals as later states.
5. Do not search citation depth, CPC/IPC taxonomy, event windows, thresholds, assets, firms or horizons.

The key falsification condition is **citation-publication ordering**: if the dependency edge was not observable before the grant, it cannot be used for that grant's exposure.

### Q185 — FEDERAL_LITIGATION_STATE × ISSUER_EXPOSURE

1. Construct a fixed state machine:
   `NO_KNOWN_CASE → CASE_FILED → ACTIVE_LITIGATION → MATERIAL_PROCEDURAL_TRANSITION → RESOLVED/TERMINATED`.
2. State changes are generated only from docket information observable by the proven public boundary.
3. The first public state is retained permanently in the historical prefix.
4. Later docket additions, corrections and outcome information cannot rewrite an earlier state.
5. Party/issuer identity mapping is frozen independently of returns.
6. Outcome labels are excluded from state construction.
7. No case-type, court, outcome, return or event-window search is allowed.

Where CourtListener does not provide a proven public intraday boundary, the conservative next-session rule remains in force.

## Required gates before formalization

Both candidates must pass:
- universal pre-formal robustness gate;
- public source access;
- historical archive/census coverage;
- exact public observation boundary or conservative next-session fallback;
- immutable revision/amendment lineage;
- frozen entity mapping with coverage evidence;
- independent reproduction.

No member of this wave is authorized for performance, holdout selection, tuning, ranking, promotion or live execution.

## Research priority

1. **Q186 first:** strongest direct literature support and a clean public grant clock.
2. **Q185 second:** unusually broad historical population, but harder coverage and public-time semantics.

Do not compose Q185 and Q186 before each passes its own PIT contract.

Safety invariants remain:
- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- ORDERS_ENABLED=False
- AUTOMATIC_PROMOTION=False
