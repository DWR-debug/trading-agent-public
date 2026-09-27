# Alpha Candidate Discovery Catalogue — 2026-09-27

## Scope
This is a literature- and mechanism-driven discovery catalogue, not a performance ranking. Inclusion means that a mechanism has a documented research rationale and a plausible future fixed-rule implementation. No holdout or observed return is used for selection.

## Candidate families and data contracts
| ID | Mechanism | Data class | First gate | Core source |
|---|---|---|---|---|
| A1 | Multi-horizon time-series momentum / trend continuation | OHLCV | PIT mutation | Moskowitz, Ooi & Pedersen (2012) |
| A1b | 52-week-high anchoring / continuation | OHLCV | PIT mutation | George & Hwang (2004) |
| A2 | Cross-sectional momentum | OHLCV | PIT mutation | Jegadeesh & Titman (1993); Asness et al. (2013) |
| A3 | Residual / idiosyncratic momentum | OHLCV + common-factor proxy | PIT mutation | Blitz, Huij & Martens (2011) |
| A4a | Post-earnings-announcement drift / earnings surprise | SEC/XBRL + exact filing timestamps | source + PIT feasibility | Bernard & Thomas (1989) |
| A4b | Macro-release reaction | official economic-release data | source + PIT feasibility | existing Q018 source-feasibility work |
| A4c | Treasury auction surprise/positioning | TreasuryDirect / CUSIP event feed | source + PIT feasibility | Q019/Q023/Q024 evidence chain |
| A4d | CFTC positioning / crowding | CFTC COT | source + PIT feasibility | CFTC official PRE |
| A5 | Low-beta / defensive premium | OHLCV | PIT mutation | Frazzini & Pedersen (2014) |
| A5b | Carry / income premium | price + distributions or futures metadata | source + PIT feasibility | Koijen et al. (2018) |
| A6 | Overnight-vs-daytime tug-of-war | OHLCV open/close | PIT mutation | Akbas et al. (2022) |
| A7 | Volatility timing | OHLCV | PIT mutation; overlay not new alpha | Moreira & Muir (2017) |
| A8 | Option-implied volatility / variance risk premium | option chain + IV | external-data feasibility | Bollerslev et al. (2011); Duarte (2024) |
| A9 | Quality / profitability | fundamentals + filing timestamps | source + PIT feasibility | Asness, Frazzini & Pedersen (2019) |
| A10 | Opening/closing auction microstructure | intraday auction data | source feasibility | Madhavan & Panchapagesan (2000) |

## Why the next implementation is price-only
Q038 produced a clean 8-symbol, 4,000-session common calendar. That makes A1, A2, A3 and A5 directly testable with the current daily OHLCV infrastructure. Q039 therefore validates only those mechanisms for point-in-time safety before any performance calculation.

## Controlled combinations
- Trend continuation + residual momentum: directional and idiosyncratic persistence.
- Cross-sectional momentum + low beta: return ranking plus defensive cross-sectional structure.
- Overnight/daytime decomposition + momentum: separates information arriving outside the session from later reversal.
- Trend + carry: mixes continuation with an economically different income source.
- Slow alpha + event alpha: event information only after exact publication-time PIT is demonstrated.

These are hypotheses, not selected portfolio constructions. No allocation weight, threshold, activation rule or family is selected here.

## Source-quality observations
- Time-series momentum has evidence across equities, currencies, commodities and bonds and a long-horizon historical extension.
- Residual momentum is directly suitable for an orthogonal residual-return construction.
- The 52-week-high relation is a distinct price-only candidate, but overlap with momentum must be tested rather than assumed.
- Overnight/daytime research is unusually accessible because the current daily OHLCV structure already contains open and close.
- SEC EDGAR exposes official XBRL/company-facts APIs, but prior hosted runs in this project encountered HTTP 403 access problems. Re-test independently before PEAD engineering.
- CFTC provides downloadable/API COT data; report date and publication date must be kept distinct.
- TreasuryDirect provides current and historical auction result material; existing Q023/Q024 evidence remains the project source chain.
- Comprehensive historical options data exist commercially, so the project does not assume an options feed is free or reproducible.

## Sources
- Moskowitz, Ooi & Pedersen (2012), Time Series Momentum, DOI 10.1016/j.jfineco.2011.11.003.
- Hurst, Ooi & Pedersen (2017), A Century of Evidence on Trend-Following Investing, SSRN 2993026.
- Asness, Moskowitz & Pedersen (2013), Value and Momentum Everywhere, DOI 10.1111/jofi.12021.
- Blitz, Huij & Martens (2011), Residual Momentum, DOI 10.1016/j.jempfin.2011.01.003.
- George & Hwang (2004), The 52-Week High and Momentum Investing, DOI 10.1111/j.1540-6261.2004.00695.x.
- Bernard & Thomas (1989), Post-Earnings-Announcement Drift, DOI 10.2307/2491062.
- Frazzini & Pedersen (2014), Betting Against Beta, DOI 10.1016/j.jfineco.2013.10.005.
- Koijen, Moskowitz, Pedersen & Vrugt (2018), Carry, DOI 10.1016/j.jfineco.2017.11.002.
- Akbas, Boehmer, Jiang & Koch (2022), Overnight Returns, Daytime Reversals, and Future Stock Returns, DOI 10.1016/j.jfineco.2021.09.019.
- Moreira & Muir (2017), Volatility-Managed Portfolios, DOI 10.1111/jofi.12513.
- Asness, Frazzini & Pedersen (2019), Quality Minus Junk, DOI 10.1007/s11142-018-9470-2.
- Madhavan & Panchapagesan (2000), Price Discovery in Auction Markets, DOI 10.1093/rfs/13.3.627.
- Duarte (2024), Very Noisy Option Prices and Inference Regarding the Volatility Risk Premium, DOI 10.1111/jofi.13365.
- SEC EDGAR APIs; CFTC Commitments of Traders Public Reporting Environment; TreasuryDirect auction results.

This catalogue is discovery infrastructure. It produces no performance evidence and no promotion decision.
