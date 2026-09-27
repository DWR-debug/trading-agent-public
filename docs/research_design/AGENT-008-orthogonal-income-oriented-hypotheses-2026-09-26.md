# AGENT-008 / Issue #280 — Orthogonal income-oriented hypothesis families

**Stand:** 2026-09-27  
**Status:** DESIGN_ONLY — unranked research material; no experiment authorized

## Purpose and limits

This document describes eight mechanically distinct families for possible future
research in support of the long-term goal of safe, potentially withdrawable
household income from a system that might be validated in the future. It is not
evidence that any mechanism exists, is profitable, or can support withdrawals.
Labels A–H are identifiers, not a ranking or priority order.

The families are separated by their proposed source of economic information or
risk transmission, not by a claim that their signals are statistically
independent. Apparent overlap or redundancy would itself require a separate,
prospectively specified research question. No performance calculations,
backtests, data selection, or scientific selection were performed for this
catalog.

Known negative and diagnostic findings constrain the design rather than nominate
a winner. In particular, the recurring risk-gate and control-relative failures
in T041/T042/T044/T045, the coverage-invalid T032/T033 relative-value attempts,
the weak or unstable historical momentum/trend and risk-control extensions, and
Q020's negative Treasury-auction result do not justify retuning or reopening
those trials. Later Q023/Q025 evidence established date-level PIT separation
for the fixed Treasury events, while Q024 could not reproduce historical
intraday publication timestamps from the official RSS archive; none of those
source-feasibility results is performance evidence. Separately, Q026 remains
`DATA_INVALID` because its fixed candle request exceeded the available common
calendar, with no performance analysis. The synthetic capital-income stress
record illustrates sequence-of-returns sensitivity; it is not a forecast or
strategy evidence.

The families below are research designs, not source-feasibility findings.
Where they depend on SEC endpoints, note that Q018's fixed `data.sec.gov`
issuer-submission requests returned HTTP 403 in the GitHub Actions runner.
Access, history, and coverage for the particular SEC material proposed here
must therefore be independently established in any future coverage
preflight; this catalog does not assume that source access is available.

## Candidate families

### A — Point-in-time macro-information innovations

- **Economic mechanism:** A newly published macro observation or revision may
  change expectations about growth, inflation, or discount rates before that
  information is fully reflected in relevant prices. This is an information
  innovation hypothesis, not a general market-regime gate.
- **Required point-in-time source:** Public FRED/ALFRED series with vintage
  history, release calendars, and an auditable first-availability timestamp.
  Each value must be reconstructed as it was available at the decision time.
- **Possible signal definition:** A change between the latest publicly
  available vintage and the previous available vintage, mapped to a
  pre-specified economic series and instrument relationship.
- **Expected failure modes:** Prices may anticipate the release; revisions may
  be noise rather than new information; relationships may be unstable across
  regimes; series may be delayed, revised, or weakly connected to a traded
  instrument.
- **Coverage / provenance risks:** Missing vintage snapshots, inconsistent
  release calendars, timezone ambiguity, revised histories substituted for
  real-time values, and series-definition changes can create look-ahead or
  incomplete coverage.
- **Later preregistration conditions:** Fix the exact series, vintage and
  timestamp rules, mapping, signal formula, population, falsification rule, and
  handling of revisions before inspecting outcomes. Verify complete real-time
  vintage coverage first; otherwise stop as `DATA_INSUFFICIENT`.

### B — Public positioning and crowding

- **Economic mechanism:** Crowded positioning may amplify forced unwinds or
  create a different return response when positioning changes. This differs
  from price momentum: the proposed information is reported exposure, not the
  observed price path.
- **Required point-in-time source:** CFTC Commitments of Traders reports, with
  report period, public-release timestamp, contract identity, and category
  definitions retained from the contemporaneous publication.
- **Possible signal definition:** A pre-specified change in a defined
  participant category's net position relative to its open interest, usable
  only after publication.
- **Expected failure modes:** Reported categories may not represent directional
  intent; hedging can look like speculation; weekly data can be stale; crowded
  positions can persist rather than unwind; the effect may reverse by market.
- **Coverage / provenance risks:** Contract rolls, category-definition
  changes, report revisions, symbol mapping, release lags, and incomplete
  historical publications can distort the signal or its availability.
- **Later preregistration conditions:** Fix report vintage and release-time
  rules, category and contract mapping, treatment of rolls and missing reports,
  and one falsifiable mechanism before analysis. Establish complete
  point-in-time report coverage and preserve raw source records.

### C — Trading-participation and liquidity shocks

- **Economic mechanism:** An unusual change in market participation may reflect
  information arrival or temporary liquidity demand and could affect either
  subsequent price formation or implementation costs. These are distinct
  predictions; a future study must specify which one it tests.
- **Required point-in-time source:** The canonical daily OHLCV snapshot or a
  reproducible public exchange volume series. Only completed bars available by
  the decision time may be used. Daily volume is a proxy, not a direct
  observation of spread or executable capacity.
- **Possible signal definition:** Turnover or volume unusual relative to a
  reference computed solely from earlier completed observations, with the
  future study choosing one pre-specified outcome mechanism (continuation,
  normalization, or cost/capacity diagnosis).
- **Expected failure modes:** Volume spikes may be non-directional, caused by
  corporate actions, or already reflected in price; a volume proxy may not
  predict spreads or market impact; results may disappear after realistic
  costs.
- **Coverage / provenance risks:** Missing or duplicated bars, adjusted-price
  and volume inconsistencies, exchange-calendar differences, survivorship,
  and absent quote-level data. Do not infer intraday execution quality from
  daily OHLCV.
- **Later preregistration conditions:** Lock the single mechanism, source
  version, bar-availability and corporate-action rules, fixed population,
  costs, and falsification criterion. Run coverage and data-integrity checks
  before any outcome evaluation; do not search across volume references or
  response directions.

### D — Point-in-time operating cash-generation changes

- **Economic mechanism:** A sustained change in operating cash generation or
  cash conversion may convey information about a firm's capacity to withstand
  adverse conditions. The hypothesis concerns underlying cash generation, not
  a high quoted yield.
- **Required point-in-time source:** SEC EDGAR filings and XBRL facts with
  accession identifiers, filing acceptance timestamps, fiscal-period metadata,
  and original filing values. Any supplementary source must preserve its
  publication time and versions.
- **Possible signal definition:** A newly filed, pre-specified cash-flow or
  cash-conversion measure changing relative to the issuer's previously
  available filing, mapped to an ex-ante fixed investable population.
- **Expected failure modes:** Accounting values may be noisy or seasonal;
  reported cash flow may not persist; business models differ; apparent
  improvement may reflect working-capital timing, financing, or one-off items.
- **Coverage / provenance risks:** Q018's SEC endpoint-access failure,
  restatements, amended filings, XBRL
  taxonomy changes, inconsistent fiscal periods, accession-time versus first
  public-release time, missing issuer histories, and survivorship can leak
  future information or create incomparable records.
- **Later preregistration conditions:** Specify one accounting construct,
  filing-time and restatement rules, comparability and missing-data treatment,
  fixed population, falsification test, and source snapshots. Demonstrate
  point-in-time reconstruction and coverage before considering performance.

### E — Distribution durability and payout continuity

- **Economic mechanism:** The persistence and coverage of declared cash
  distributions may be relevant to the reliability of income available for
  eventual withdrawal. A distribution is not itself evidence of economic
  return, capital preservation, or sustainable income.
- **Required point-in-time source:** Issuer distribution declarations and
  effective dates from contemporaneous regulatory filings or archived issuer
  announcements; SEC-filed financial statements for any payout-coverage
  measure. Preserve announcement, ex-date, record date, and payment date
  separately.
- **Possible signal definition:** A pre-specified change in distribution
  continuity or in declared distributions relative to cash-flow coverage,
  using only information public by the decision time. Do not define the signal
  as selecting the highest observed yield.
- **Expected failure modes:** Distributions can be cut after apparent
  stability; debt-funded payouts can mask weak operations; nominal payouts can
  coexist with capital loss or inflation erosion; payment timing and taxes can
  make cash received differ from quoted yield.
- **Coverage / provenance risks:** Q018's SEC endpoint-access failure,
  announcement archives may be incomplete;
  declarations can be revised; corporate actions, special distributions,
  currencies, withholding, and stale fundamentals complicate continuity and
  payout calculations.
- **Later preregistration conditions:** Define the distribution event and
  income-reliability outcome separately from total return, fix the issuer
  population and event chronology, model costs and applicable cash-flow
  accounting consistently, and specify a falsification rule. Require complete
  event and filing provenance; never infer household withdrawal safety from a
  dividend-only measure.

### F — Price discovery after public corporate disclosures

- **Economic mechanism:** A material corporate disclosure may be incorporated
  into prices gradually when investors differ in attention or interpretation.
  This is a post-disclosure information-diffusion question, not a search for
  favorable event types after the fact.
- **Required point-in-time source:** SEC EDGAR filings and, where necessary to
  establish first public availability, archived issuer announcements with
  reproducible publication timestamps. Filing acceptance alone may not be the
  first public disclosure.
- **Possible signal definition:** A pre-specified, mechanically extractable
  change in a defined filing item, becoming usable at the verified first-public
  timestamp and mapped to a fixed post-availability observation rule.
- **Expected failure modes:** The information may be anticipated or immediately
  priced; filing timestamps may lag the announcement; event effects may be
  heterogeneous or overwhelmed by simultaneous news; event scarcity may make
  inference unreliable.
- **Coverage / provenance risks:** Q018's SEC endpoint-access failure,
  incomplete issuer-release archives, filing
  amendments, timestamp/timezone errors, survivorship, ambiguous event
  classification, and selective inclusion of only salient disclosures.
- **Later preregistration conditions:** Fix one event definition, parsing
  rule, first-public timestamp hierarchy, fixed population and event mapping,
  minimum coverage contract, and falsification rule before looking at
  post-event outcomes. If first-public timestamps cannot be verified, stop as
  `DATA_INSUFFICIENT`. Do not reopen Q020 or infer a preferred direction from
  its result.

### G — Cross-market relative-value dislocations

- **Economic mechanism:** A temporary divergence between economically linked
  instruments may normalize as relative pricing returns toward a stable
  relationship. This is distinct from ranking assets by recent performance;
  the relationship itself must have an economic basis fixed in advance.
- **Required point-in-time source:** Synchronized, corporate-action-aware
  canonical Yahoo OHLCV snapshots (or another public source qualified in a
  future contract) for the fixed linked instruments, plus public source data
  needed to justify the relationship. Each leg must have reproducible
  timestamps and common-session mapping.
- **Possible signal definition:** A deviation of the observed relative price
  from a pre-specified relationship estimated using only permitted prior
  information. No pair, hedge ratio, threshold, or observation window is
  selected in this document.
- **Expected failure modes:** The relationship may structurally break; apparent
  convergence may be compensation for hidden risk; borrow, financing, or
  rebalancing costs may dominate; shared market exposure can masquerade as
  convergence.
- **Coverage / provenance risks:** T032/T033 were invalidated before
  performance evaluation because of coverage. Non-synchronous calendars,
  missing legs, corporate actions, instrument changes, short availability,
  and incomplete borrow/financing histories remain material risks.
- **Later preregistration conditions:** State the ex-ante economic linkage and
  fixed instrument mapping, relationship-estimation rule, cost and financing
  contract, complete common-calendar coverage criteria, and falsification rule.
  Coverage failure means no performance test. Do not repair the prior trials
  by changing their universe or data geometry.

### H — Downside dependence and income-path resilience

- **Economic mechanism:** Changing downside dependence among fixed portfolio
  components may affect the sequence and clustering of losses, and therefore
  the stability of any hypothetical future withdrawals. This is a portfolio
  resilience question, not a directional alpha claim or a new market/cash
  gate.
- **Required point-in-time source:** Canonical, synchronized component-return
  snapshots and their source positions, with all dependence estimates formed
  only from observations available before each decision. A withdrawal-path
  analysis, if separately authorized, would require its own fixed cash-flow
  assumptions.
- **Possible signal definition:** A pre-specified estimate of downside
  co-movement or loss clustering across an unchanged component set, used to
  describe or test a fixed risk response against an unchanged comparator.
- **Expected failure modes:** Dependence estimates are unstable and lagging;
  correlations can rise in stress; apparent diversification can vanish;
  risk-scaling may suppress recoveries or income without preventing large
  losses. Existing market/cash-gate and portfolio-risk trials did not establish
  a reliable protective effect.
- **Coverage / provenance risks:** Asynchronous calendars, missing return
  periods, changing holdings, corporate actions, and look-ahead in risk
  estimates. Synthetic withdrawal scenarios do not establish real-world
  income reliability.
- **Later preregistration conditions:** Keep holdings and existing gates fixed;
  define the dependence measure, update timing, comparator, costs, and
  falsification rule prospectively. Separate return/risk evidence from
  withdrawal-policy assumptions, satisfy unchanged evidence gates, and make
  no promotion or live-execution inference.

## Common conditions before any later formal study

Each family would require its own new, immutable preregistration and one
explicit falsifiable question. Before performance work, that record must fix
the mechanism, formula, point-in-time source and timestamp semantics, source
versioning, population and mapping, study split, costs, missing-data policy,
coverage requirements, comparator, and analysis plan. Coverage/PIT preflight
must pass first; data failures remain `DATA_INVALID` or `DATA_INSUFFICIENT`,
not performance outcomes.

No family may be selected by expected return, by inspecting a holdout, or by
retrospectively changing parameters, assets, thresholds, horizons, variants,
universe, or gates. Evidence gates and holdout separation remain unchanged.
Agent-generated design material is not evidence. A future result cannot
authorize promotion or live trading.

The income objective adds no shortcut: any later income-sustainability
question must distinguish distributions from total return, model sequence
risk under prospectively fixed assumptions, and treat capital preservation and
withdrawal reliability as separate outcomes. This document makes no promise
about income, returns, or financial outcomes.

## Canonical basis

- `docs/PROJECT_CONTEXT.md` — objective, safety contract, and historical
  failure summary.
- `research/evidence/trial_ledger.json` — immutable trial records and statuses.
- `research/evidence/cross_trial_failure_diagnosis_2026_09_25.json` —
  recurring control-relative, risk, stability, and data-validity failures.
- `docs/research_design/AGENT-010-q020-failure-mechanism-diagnosis-2026-09-26.md`
  and `docs/research_design/AGENT-011-q022-treasury-failure-followup-design-2026-09-26.md`
  — Q020 failure signatures, timing uncertainty, and unranked follow-up rules.
- `research/preregistrations/q017_orthogonal_hypothesis_design_round_2026_09_25.json`
  — prior design material on macro vintages, positioning, and participation.
- `research/evidence/capital_income_scenario_stress_2026_09_24.json` —
  synthetic, non-predictive illustration of sequence sensitivity.
- `research/evidence/q018_source_feasibility_2026_09_26.json` and
  `research/evidence/q023_treasury_release_timestamp_pit_feasibility_2026_09_27.json`,
  `research/evidence/q024_treasury_auction_result_timestamp_pit_feasibility_2026_09_27.json`,
  `research/evidence/q025_treasury_auction_date_pit_feasibility_2026_09_27.json`
  — source and PIT feasibility limitations.

Safety invariants remain:

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`  
`automatic_promotion=False`
