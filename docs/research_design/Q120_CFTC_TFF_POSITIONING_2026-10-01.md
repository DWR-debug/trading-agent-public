# Q120 — CFTC TFF Positioning-Divergence State

Status: **DESIGN-ONLY / FEASIBILITY**

Q120 tests an economically distinct market-state channel: disagreement between Leveraged Money and Asset Manager/Institutional positioning in the fixed E-mini S&P 500 futures market.

Fixed definition:

`AM_net = (Asset_Manager_Long - Asset_Manager_Short) / Open_Interest`

`LM_net = (Leveraged_Money_Long - Leveraged_Money_Short) / Open_Interest`

`positioning_gap = LM_net - AM_net`

State:
- `LEVERAGED_MORE_LONG` when gap > 0
- `ASSET_MANAGER_MORE_LONG` when gap < 0
- `ALIGNED` when gap = 0

The report is based on the prior Tuesday's positions but is normally published on Friday. Historical exceptional release schedules must use the actual documented public-release date rather than assuming a normal Friday publication.

Q120 is a state channel, not a ranked stock-selection rule. It is intended to complement, not duplicate, the project's 13F beneficial-ownership and Treasury-auction channels.

Next gates:
1. Historical archive and actual publication-date recovery.
2. Contract identity and field completeness.
3. Release-date PIT mutation checks.
4. Independent reproducibility.
5. Only after these gates may formal performance authorization be considered.

Governance: no performance, holdout selection, parameter/threshold/horizon/asset search, ranking, promotion, or live execution.

Sources:
- CFTC Commitments of Traders: https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm
- CFTC TFF Futures Only: https://publicreporting.cftc.gov/stories/s/TFF-Futures-Only/98ig-3k9y/
- CFTC variable definitions: https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalViewable/cotvariablestfm
