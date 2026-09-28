# Q073 — Expanded Orthogonal Candidate Search — 2026-09-28

## Status

**DESIGN_ONLY_UNRANKED**

Q073 expands the candidate frontier beyond the fixed Q069 OHLCV bank and the Q072 information-source bank. It is a discovery/design layer only.

No candidate is ranked, tuned, backtested, selected or promoted by this document.

## Research objective

The current formal evidence repeatedly fails on drawdown/stability rather than on absence of any positive return observation. Q066 therefore identified common-mode alpha risk and diversification as a more relevant target than further parameter tuning.

Q073 broadens the search in two directions:

1. cross-sectional mechanisms that interact different return/limits-to-arbitrage dimensions rather than repeating momentum variants;
2. orthogonal public information channels with explicit historical public-availability anchors.

## Candidate families

| ID | Mechanism | Channel | Initial PIT posture |
|---|---|---|---|
| C12 | SAME_CALENDAR_MONTH_SEASONALITY | daily price history | next-session after completed month |
| C13 | REVERSAL_ILLIQUIDITY_INTERACTION | price + volume | next-session |
| C14 | MOMENTUM_TURNOVER_INTERACTION | price + volume | next-session |
| C15 | MARKET_STATE_BETA_RESPONSE | market + cross-sectional beta | next-session |
| I7 | SEC_13F_INSTITUTIONAL_CROWDING_CHANGE | SEC 13F | filing acceptance datetime, then next session |
| I8 | SEC_8K_EARNINGS_INFORMATION_FLOW | SEC 8-K / XBRL | filing acceptance datetime, then next session |
| I9 | CBOE_VOLATILITY_STATE | VIX/VVIX | completed daily observation, then next session |
| I10 | CROSS_SOURCE_DISAGREEMENT | independent public sources | max verified source cutoff, then next session |

The set remains unranked.

## C12 — Same-calendar-month seasonality

Use only completed historical observations from the same calendar month in prior years. The fixed mechanism must define the minimum history, aggregation rule and cross-sectional portfolio construction before coverage.

Rationale: published work documents return seasonality by same-calendar-month histories across stocks, anomalies, commodities and international indices.

Primary risk: with daily equity data, the usable number of same-calendar-month observations is much smaller than the full daily sample. Coverage, minimum-history geometry and multiple-comparison risk must therefore be explicit.

## C13 — Reversal × illiquidity interaction

Construct a deterministic short-horizon reversal signal and condition it on a fixed price-impact proxy using absolute return divided by dollar volume.

Rationale: recent anomaly-interaction research finds short-term reversal and limits-to-arbitrage variables, especially illiquidity, among the most persistent interaction clusters.

Primary risk: the apparent interaction can be compensation for trading costs. Cost stress is therefore a first-class gate, not an afterthought.

## C14 — Momentum × turnover interaction

Condition an already fixed medium-horizon momentum measure on a lagged turnover/volume state. No momentum horizon or turnover threshold may be searched after observing results.

Rationale: the anomaly-interaction literature identifies momentum/turnover interactions as a recurrent family.

Primary risk: overlap with the existing Q069 volume-confirmed trend candidate. Q073 should only keep C14 if its exact information geometry is demonstrably distinct rather than a naming variant.

## C15 — Market-state beta response

Estimate a fixed rolling beta to the broad market and condition the cross-sectional interpretation on a preregistered market-return state.

Rationale: recent asset-pricing work documents state-dependent beta/return relations.

Primary risk: high overlap with risk-control research. This must be treated as a return-state mechanism, not an excuse to retune beta windows or market-state thresholds.

## I7 — SEC 13F institutional crowding change

Measure changes in disclosed institutional holdings between completed 13F reports.

PIT rule: use EDGAR acceptance datetime as the public-availability anchor and act only on the next eligible session.

The raw accession, filing header, report period, manager identity and information-table records must be retained immutably.

Primary risks:
- filing frequency is quarterly;
- report-period date is not the public-availability date;
- 13F coverage excludes some positions and managers;
- entity/security identifier mapping can introduce hidden selection.

## I8 — SEC 8-K earnings information flow

Use first-publicly-filed earnings/revenue information from 8-K / 10-Q / 10-K documents, with filing acceptance time as the PIT anchor.

The initial implementation should use only facts reconstructible from the first accepted filing and should avoid later restatements/revisions.

Primary risks:
- XBRL context selection;
- subsequent amendments;
- company-specific fiscal calendars;
- filing bundles containing administrative rather than economically new information.

## I9 — Cboe volatility state

Use daily VIX/VVIX state information as an orthogonal market-risk regime variable. No derivative trade is required for the research candidate; it can instead condition equity exposure or cross-sectional selection.

Cboe publishes long historical VIX daily closes.

Primary risk: this is primarily a state variable, so the design must specify exactly how it changes exposure without becoming a free-form risk tuner.

## I10 — Cross-source disagreement

Combine two already validated independent information channels and use only their disagreement state.

Example class:
- insider-flow positive while public attention remains low;
- short-flow shock disagrees with insider-flow direction.

This is deliberately retained as a higher-risk research direction because interaction logic can create strong data-mining incentives. It requires the component sources to be frozen independently before their combination is evaluated.

## Governance

For every Q073 family:

1. source/schema feasibility;
2. exact historical public-availability / vintage PIT contract;
3. frozen entity/universe mapping;
4. fresh disjoint coverage;
5. mutation PIT test;
6. separate fixed-rule performance authorization;
7. unchanged 13-gate evaluation.

Forbidden:
- parameter search,
- threshold search,
- asset search after observing metrics,
- family ranking before preregistered performance,
- holdout selection,
- automatic promotion,
- live execution.

## Evidence basis

Q073 is motivated by:
- anomaly-interaction evidence in Review of Asset Pricing Studies (2025);
- international evidence on same-calendar-month return seasonality;
- SEC EDGAR's acceptance datetime and structured filing APIs;
- Cboe's historical VIX data.

These sources motivate hypotheses only. They are not evidence that any Q073 candidate works in this project.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
