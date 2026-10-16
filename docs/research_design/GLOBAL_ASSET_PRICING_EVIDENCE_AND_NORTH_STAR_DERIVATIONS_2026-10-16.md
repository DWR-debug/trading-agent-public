# Global Asset-Pricing Evidence and North Star Derivations — 2026-10-16

**Classification:** global literature synthesis; design and governance implications only  
**Repository basis:** public master verified at 56b82878539202d987a54aff3642c8a39c23e14d before this research change  
**Research lanes reviewed:** factor replication and publication decay; multiple testing/backtest selection; tradability and transaction costs; global machine learning; institutional ownership and disclosure clocks; SEC/XBRL information processing; government procurement/R&D; portfolio estimation risk; capital preservation and withdrawal rules.  
**Decision status:** no candidate gate changes; no performance authority; paper-only.

## Executive decision

The shortest defensible route to the North Star is not to increase the number of candidate signals or to use a more complex model by default. It is to prove one candidate's information boundary and economic mechanism, independently reproduce it, then assess whether its net return remains useful under conservative trading and capital-preservation assumptions. Global research supports both sides of this view: many return-predictive relationships replicate under some methods and markets, while a material portion weakens under multiple-testing controls, value-weighting/liquidity restrictions, later samples or real implementation costs.

The evidence suggests five governing conclusions:

1. **Novelty must be incremental, not nominal.** A new dataset, model class or candidate ID does not establish a new return mechanism. Evaluate each frozen hypothesis against a fixed benchmark and adjacent mechanism families, with model-selection error acknowledged.
2. **Information time is part of the economic variable.** Event dates, quarter ends, regulatory acceptance timestamps, source-modification dates, publication/reveal dates and our own observation times are different clocks. A candidate whose historically available values cannot be reconstructed is not ready for a return test.
3. **Gross backtest performance is not the product.** Factor research finds sizable implementation shortfalls between paper factors and attainable exposures. Turnover, spread, slippage, short borrow, liquidity, capacity and missed trades need their own predeclared, auditable model.
4. **The active Q104:I19, Q220 and Q221 candidates connect along a plausible information chain but are not yet a valid composite.** Institutional demand, structured/narrative accounting information and procurement demand may all influence how information reaches prices. That relationship is a set of falsifiable links, not proof of independent alpha.
5. **The North Star's cashflow condition is downstream of capital preservation.** The canonical North Star says available capital is €0 and the €2,000 reference is simulation-only. No sustainable-withdrawal rate, family-support income or candidate-success probability can be inferred from literature or research readiness. The system must earn any future authorization through formal evidence and must never infer withdrawals from gross or unrealized P&L.

**Operational recommendation:** preserve the three-candidate execution lock. Keep Q104:I19 and Q220 blocked at their current source/PIT gates; keep Q221 blocked at its historical public-clock and pre-event identity gates. Use the synthesis below to sharpen future preregistrations and cheap falsifiers only after their existing gates are satisfied. This document does not open a performance phase, create a new candidate, or change the formal gate contract.

## 1. Scope and evidence standard

This was a multi-pass, cross-domain search rather than a formal systematic review or a new empirical test. Search angles included U.S. and international anomaly replication; Bayesian and frequentist multiple-testing approaches; backtest overfitting and model-selection uncertainty; implementation shortfall; global machine learning; 13F institutional holdings; XBRL and filing-processing costs; government procurement and R&D; and sequence-of-returns/withdrawal policy. The most material claims were checked against journal/publisher pages, NBER records, official SEC documents or linked primary papers. Working papers and secondary indexes are identified as such.

Four evidence classes must not be conflated:

- **Literature result:** what another study found for its own data, sample, methods and period.
- **Source feasibility:** whether a data source can be queried or whether its schema describes a field.
- **Project evidence:** a frozen receipt produced under the repository's own contract and code.
- **Authorization:** a formal project decision allowing a later experiment. None of the cited papers or this synthesis grants such authority.

A worldwide sample is not automatically an independent replication. Markets share global shocks, firms, investors, currencies, exchanges and research designs. A global panel is valuable if dependence and market structure are modelled; it is not a free multiple of independent observations.

## 2. Global evidence on whether signals survive

### 2.1 The replication debate is real and method-dependent

Hou, Xue and Zhang's peer-reviewed study, [“Replicating Anomalies”](https://academic.oup.com/rfs/article/33/5/2019/5236964) (*Review of Financial Studies*, 2020), re-examines 452 published anomalies using a more conservative design, including NYSE breakpoints and value-weighted portfolios to mitigate microcap influence. They report that a substantial majority do not clear conventional significance thresholds under their design; using a more stringent multiple-testing hurdle further reduces the set of supported anomalies. This is a warning against treating the published factor inventory as an investable inventory.

Jensen, Kelly and Pedersen's [“Is There a Replication Crisis in Finance?”](https://doi.org/10.3386/w28432) (NBER Working Paper, 2021) reach a more optimistic conclusion using a Bayesian hierarchical model over 153 factors and 93 countries. They find that many factors cluster into a smaller number of themes and that global evidence can strengthen posterior support after explicitly accounting for dependence among markets and factors. Their conclusion is not a mechanical contradiction of Hou et al.: the statistical model, factor selection, portfolio construction, cross-market structure and meaning of “replication” differ.

Jacobs and Müller, [“Anomalies across the globe: Once public, no longer existent?”](https://doi.org/10.1016/j.jfineco.2019.06.004) (*Journal of Financial Economics*, 2020), study 241 anomalies across the U.S. and 38 international markets. They find a robust post-publication profitability decline in the U.S. but no comparably robust decline across the other 38 markets in their sample. They discuss segmentation and barriers to arbitrage as possible explanations; the international sample ends in 2015 and should not be read as proof that a particular signal remains profitable today.

**Joint interpretation:** the literature neither justifies rejecting every anomaly nor treating broad published predictability as a menu of ready-to-trade strategies. Results depend on sample, model, liquidity, weighting, publication period and market structure. Global tests add information, but only when cross-market dependence and implementation differences are controlled.

### 2.2 New factors must prove incremental explanatory power

Feng, Giglio and Xiu, [“Taming the Factor Zoo: A Test of New Factors”](https://consensus.app/papers/taming-the-factor-zoo-a-test-of-new-factors-feng-giglio/9cd7d142463256aba0cd20b1d130726f/?utm_source=chatgpt) (*The Journal of Finance*, 2019), propose testing whether a candidate factor adds explanatory power beyond a high-dimensional set of existing factors while accounting for model-selection mistakes. They find that many proposed factors are redundant, while some, including profitability in their application, contribute beyond the existing collection. Their methodology is explicitly motivated by the instability of naïve variable selection.

Harvey, Liu and Zhu, [“… and the Cross-Section of Expected Returns”](https://doi.org/10.1093/rfs/hhv059) (*Review of Financial Studies*, 2016), show how multiple testing raises the hurdle for declaring a newly discovered factor. Their often-cited t-statistic threshold above 3 is a research-literature proposal, not an automatically applicable project gate; transferring any numeric threshold would require project-specific statistical review, sample-size reasoning and formal approval.

The engineering lesson is more important than the particular cutoff: candidate lineage must include abandoned concepts, source probes, model variations and rejected runs. A “best result” cannot be interpreted without knowing how many trials were tried and how selection occurred. The repository already separates discovery, formal readiness and performance authorization; this synthesis reinforces that separation rather than replacing it.

### 2.3 Machine learning may capture interactions, but model choice itself is a source of uncertainty

Azevedo, Kaiser and Mueller, [“Stock market anomalies and machine learning across the globe”](https://link.springer.com/article/10.1057/s41260-023-00318-z) (*Journal of Asset Management*, 2023), examine roughly 1.9 billion stock-month-anomaly observations from 1980–2019 across international markets. They report that some nonlinear and composite predictors outperform linear baselines in their research setting, including under the cost assumptions they evaluate. The scale and result motivate testing fixed interaction models after source/PIT readiness; they do not imply that a particular neural network is suitable for our data, universe, timing or cost contract.

A more recent working paper, [“Design choices, machine learning, and the cross-section of stock returns”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5031755) (Chen, Hanauer and Kalsbach; revised 2026), systematically varies more than a thousand modelling designs. It reports that non-standard error arising from design choices is larger than conventional standard error in its experiment. This is not yet a reason to add another model family; it is a reason to avoid unconstrained model search and to report design sensitivity instead of cherry-picking a configuration.

**Derived rule:** if nonlinear modelling is eventually authorized, compare a single predeclared low-complexity baseline with a small, justified challenger set. Freeze features, labels, horizons, splits and preprocessing first. Report the results of the registered alternatives and their uncertainty together. Never expand the search grid because the first result is disappointing.

## 3. The bridge from a predictive pattern to realizable net P&L

### 3.1 Implementation shortfall is economically material

Patton and Weller, [“What you see is not what you get: The costs of trading market anomalies”](https://public.econ.duke.edu/~ap172/Patton_Weller_2020_JFE.pdf) (*Journal of Financial Economics*, 2020), develop a way to infer implementation costs by comparing on-paper factor exposure with mutual-fund returns. After accounting for their estimated costs, typical funds in their study earn low returns to value and no returns to momentum. The method avoids prescribing one exact simulated trading rule, but its implementation-cost estimates still depend on the studied fund universe and the relationship between funds and factor exposures.

Johansson, Sabbatucci and Tamoni, [“Tradable Risk Factors for Institutional and Retail Investors”](https://doi.org/10.1093/rof/rfae034) (*Review of Finance*, published 2025), construct tradable factor benchmarks using liquid funds and ETFs, including shorting costs. They report an annual 2–4 percentage-point gap between standard on-paper factors and their tradable versions; transaction costs and shorting fees account for a large share of that gap. The exact magnitude should not be transferred to our intended paper portfolio, but the existence of an implementation shortfall is a central design constraint.

Li, Chow, Pickard and Garg, [“Transaction Costs of Factor-Investing Strategies”](https://doi.org/10.1080/0015198X.2019.1567190) (*Financial Analysts Journal*, 2019), model implicit market-impact costs from the rebalancing of established factor indexes. They connect costs to turnover and turnover concentration. This reinforces that a flat commission estimate alone does not represent the cost of a high-turnover strategy.

### 3.2 Estimation risk makes simple allocation a serious baseline

DeMiguel, Garlappi and Uppal, [“Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?”](https://doi.org/10.1093/rfs/hhm075) (*Review of Financial Studies*, 2009), compare a set of sample-based mean-variance portfolios and extensions against equal weighting across seven datasets. None of the 14 models consistently outperforms the 1/N rule across Sharpe ratio, certainty-equivalent return and turnover in their tests. This does not prove equal weights are always optimal. It demonstrates that estimated expected returns and covariances can be noisy enough to erase the theoretical benefit of optimization.

**Derivation for Trading Agent OS:** the eventual performance layer needs both a gross prediction assessment and an executable, net, risk-constrained portfolio assessment. Before complex optimization, the benchmark should be intentionally simple, deterministic, turnover-aware and capped. The optimizer must justify its own incremental benefit after all costs and estimation uncertainty—not merely produce a higher in-sample Sharpe ratio.

### 3.3 Minimum requirements for any future cost-aware evaluation

These are recommended requirements for a future preregistered contract, not a new authorization or a change to any current gate.

- Freeze a price/volume universe that was actually known and investable at each decision time, including delisting and corporate-action policy.
- Freeze when a signal becomes actionable, its execution delay, rebalance schedule, price convention and missing-data rules.
- Include commissions/fees, bid-ask spread, slippage, turnover, short-borrow costs where relevant, position and liquidity limits, and a documented market-impact sensitivity.
- Report gross return, cost components, net return, turnover, capacity assumptions, drawdown and tail loss separately. Avoid aggregating all frictions into an opaque single haircut.
- State the break-even round-trip cost and which assumptions would eliminate the measured edge.
- Compare the result with a simple benchmark built under the same universe, timing, constraints and cost model.
- Do not use observed performance to select assets, thresholds, horizons, market segments or cost assumptions. Any such search requires separate preregistration and controls for multiplicity.

A signal that passes PIT but fails the cost test is useful negative evidence. It does not justify changing the signal after seeing returns.

## 4. What the literature means for the active candidates

### 4.1 Q104:I19 — institutional demand × accounting state

The official SEC [Form 13F FAQ](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f) states that quarterly Form 13F reports can be filed up to 45 days after quarter-end. The disclosed position therefore is a delayed public snapshot, not an observation of the institution's actual trading decision in real time. Its quarter-end holdings and later filing acceptance must not be treated as the same clock.

Wang, [“Institutional trading, news, and accounting anomalies”](https://www.sciencedirect.com/science/article/pii/S0165410124000168) (*Journal of Accounting and Economics*, 2024), finds that institutional trading direction varies with the type of accounting anomaly: institutions tend to trade in the predicted direction of underreaction anomalies but often trade in the opposite direction of overreaction anomalies, with news sentiment offered as a mechanism. This is a useful caution for I19: institutional ownership changes can reflect institutional reaction to news and can sometimes amplify rather than correct price errors.

**Derived mechanism hypothesis—not evidence:** the interaction between institutional demand and a fixed accounting state may identify contexts in which ownership disclosures reflect slow processing of fundamentals. But it may also be redundant with news direction, earnings expectations or the accounting state itself.

Required treatment after the existing source/PIT gates are resolved:

1. Retain 13F observation only from the actual public filing timestamp; never backdate a published holdings disclosure to quarter-end.
2. Compare the frozen institutional-demand variable with frozen accounting variables and a predeclared news/earnings context as alternative explanations. This is an orthogonality/measurement audit, not permission to add or tune features based on future returns.
3. Preserve amendment lineage, CUSIP/security mapping, filer identity and position interpretation. Reported long positions are not a complete map of institutional exposures or trades.
4. Do not build the historical compiler or independent reproduction for the full set while the present source/acceptance blockers remain open.

The current repository state is binding: 53 unique residual accession keys remain unresolved. Only 36 verified date-mismatch rows are admissible for a non-destructive research sidecar. Seven identity-conflict rows and ten complete-submission HTTP 404 cases remain outside that review. Production filing-date precedence, historical PIT, performance and authorization remain blocked. Literature cannot resolve these row-level source conflicts.

### 4.2 Q220 — narrative/structured filing representation

The SEC's [EDGAR API documentation](https://www.sec.gov/search-filings/edgar-application-programming-interfaces) says the submissions and extracted XBRL APIs update throughout the day as filings are disseminated and are available without API keys. It also warns implicitly against treating every API output as a historical vintage: the Company Facts and Frame endpoints summarize facts across filings, use taxonomy/context rules, and the Frame endpoint aligns to calendar periods rather than every issuer's exact fiscal calendar. A current XBRL API response is therefore not, on its own, a complete as-known historical series.

XBRL research also points in both directions. Blankespoor, [“The Impact of Information Processing Costs on Firm Disclosure Choice: Evidence from the XBRL Mandate”](https://doi.org/10.1111/1475-679X.12268) (*Journal of Accounting Research*, 2019), finds that adoption of detailed tagging requirements is associated with more quantitative footnote disclosure. Dong, Li, Lin and Ni, [“Does Information-Processing Cost Affect Firm-Specific Information Acquisition? Evidence from XBRL Adoption”](https://doi.org/10.1017/S0022109016000235) (*Journal of Financial and Quantitative Analysis*, 2016), report improved incorporation of firm-specific information after XBRL adoption. In contrast, Efendi, Park and Smith, [“Do XBRL filings enhance informational efficiency? Early evidence from post-earnings announcement drift”](https://www.sciencedirect.com/science/article/pii/S0148296313002555) (*Journal of Business Research*, 2014), report effects that differ across news direction and periods. The implication is that machine readability can reduce processing friction; it does not guarantee a universal exploitable price response.

**Derived mechanism hypothesis—not evidence:** a deterministic discrepancy between a filing's narrative TextBlock and its structured facts may identify information-processing difficulty or semantic mismatch. To qualify as a distinct mechanism it must differ from simple accounting-fact surprise, filing complexity, missing taxonomy mappings and ordinary disclosure drift.

Required treatment:

1. Freeze the accession, full filing identity, acceptance clock, taxonomy, XBRL contexts, units and period alignment.
2. Derive TextBlock and presentation/relationship mapping from deterministic structural fields. Manual semantic substitution or LLM-generated mapping must not determine scientific state.
3. Test for taxonomy drift, missing concepts, unit mismatches, instant/duration mismatch, duplicated contexts and custom-tag handling before forming a candidate feature.
4. A future feature must be mutation-tested so a later amendment, restatement or later filing cannot rewrite the information that was available at an earlier decision time.
5. Preserve the present lineage problem. The current Q220 compiler is blocked, with 55/55 primary-document hash mismatches; historic receipts attest an earlier 55/55 match, but the original complete-response bytes needed for an offline re-hash were not retained. Do not redownload multi-gigabyte Feeds or primary documents, rewrite expected hashes or treat the old positive receipt as current-context independent reproduction. Continue offline provenance reconciliation or preserve the block.

### 4.3 Q221 — public procurement, R&D and follow-on demand

Evidence on government contracts is heterogeneous, and this matters for the economic meaning of Q221.

Pyun, [“Trading on government contracts: The investment potential of public procurement awards”](https://www.sciencedirect.com/science/article/pii/S0165176525001727) (*Economics Letters*, 2025), reports that larger awards correlate with subsequent stock performance in its sample of U.S. government awards from 2020–2023. The result is a useful motivating study but is not itself independent project replication, and its sample/window and source clock do not prove an investable first-public timestamp for our frozen transaction rows.

Esqueda, Ngo and Susnjara, [“The effect of government contracts on corporate valuation”](https://doi.org/10.1016/j.jbankfin.2019.07.003) (*Journal of Banking & Finance*, 2019), find that government contractors as a broad group can have lower valuations and sales growth, with differences across economic conditions and strategically important sectors. Dong et al., [“Impact of Government Outsourcing Contracts on High-Tech Vendors: An Empirical Study”](https://consensus.app/papers/impact-of-government-outsourcing-contracts-on-hightech-dong-hu/46d87e6e08ab585c98dce6c522aa1555/?utm_source=chatgpt) (*Journal of Management Information Systems*, 2024), find that government customers can affect how markets value earnings at high-tech vendors, attributing this in part to earnings persistence and accrual/cash-flow alignment. Arora, Belenzon, Cioaca and Ferracuti, [“The Private Value of Innovating for the Government”](https://doi.org/10.3386/w33880) (NBER Working Paper, 2025), study U.S. federal R&D contracts for publicly traded firms from 1984–2015. They report strongly skewed private value and argue the highest value can arise when R&D contracts are linked to future noncompetitive production contracts for firms with the necessary production capabilities. It is a working paper, not a project replication.

These findings support a **conditional contract-economics mechanism**, not the assumption that awards are always bullish. Plausible conditioning variables include surprise versus expected award, award size relative to issuer scale, award type and duration, competition/sole-source status, strategic-sector classification, government customer dependence, and later earnings persistence. Each is a candidate design hypothesis only. It would be methodological error to search across those variables after observing historical returns.

The decisive issue in the repository remains source validity rather than outcome selection:

- No first public-observation timestamp is proven for 348/348 frozen transactions.
- The 247 distinct recipient identity candidates are not mapped to issuers with a frozen pre-event identity proof.
- The five archived USAspending policy-document vintages do not prove the individual public clock for any transaction.
- The SAM.gov API requires a protected API key that is not configured. The documented publicDeltaDate parameter filters by Last Modified Date or Reveal Date, but reviewed documentation does not prove arbitrary historical-version retrieval or expose a record-level first-public timestamp under the current contract.
- The previous exact FPDS Atom route redirected 4/4 requests and was intentionally not followed. Arquivo.pt TimeMap returned 404 for all four exact queries. Wayback CDX returned valid empty arrays for the four exact feed URLs, which is a route-specific no-capture result only. The Common Crawl attempt on 2026-10-16 returned three HTTP 504s and one HTTP 503, so that lookup was incomplete, not a valid empty result. No WARC payload was downloaded.

Accordingly, do not repeat those routes or infer historical absence. A new Q221 experiment should be considered only if a materially new, authorized source contract documents transaction-level version retrieval/publication semantics and a defensible pre-event recipient-to-issuer bridge. Until then, no performance-oriented Q221 sample expansion is justified.

## 5. The hidden relation between I19, Q220 and Q221

The literature motivates an information-processing graph:

**economic event / institutional action → public disclosure → machine or human interpretation → beliefs and expected cash flows → price response.**

The three active candidates measure different possible parts of this graph:

| Candidate | Proposed observable | Important adjacent explanation | What must be proven first |
|---|---|---|---|
| Q104:I19 | Public institutional-ownership change interacting with a fixed accounting state | Delayed 13F disclosure, news-following, earnings/accrual state itself, filer/security mapping errors | Complete security/13F identity and historical acceptance/PIT chain; current residuals remain closed |
| Q220 | Narrative/structured XBRL representation discrepancy | Ordinary accounting surprise, filing complexity, taxonomy drift, missing facts, current API revision | Deterministic filing/version/TextBlock/presentation lineage and current source-hash provenance |
| Q221 | Government award/modification state and contract context | Firm size/stability, sector/strategic status, expected award, reporting delay, later financial outcomes, recipient mapping | Historical first-public boundary, transaction class/agency applicability and pre-event issuer exposure |

This graph is useful to direct future falsifiers, but it does not show that all three are independent or composable. In particular, government contracting may later change earnings persistence and accounting reporting; institutional filings may react to news and accounting states; and structured filing data may reduce the processing cost of those signals. A composite built now could simply count the same fundamental/news information three times.

**Rule:** do not make a meta-signal, rank candidates or design a weighting scheme until individual candidate definitions and their independent PIT chains pass existing gates and a frozen mechanism-signature/non-overlap audit demonstrates the incremental object. Negative findings that two candidates are redundant should lead to merge/kill, not extra tuning.

## 6. From net return to the North Star's realized-cashflow condition

The North Star concerns sustainable realized-P&L cashflow while preserving capital, not merely a strategy with a positive historical mean.

The international withdrawal literature reinforces the prudence of a separate, downstream cashflow layer. Anarkulova, Cederburg, O’Doherty and Sias, [“The safe withdrawal rate: evidence from a broad sample of developed markets”](https://doi.org/10.1017/s1474747225000010) (*Journal of Pension Economics & Finance*, 2025), use asset-class returns across 38 developed countries to study constant-percentage withdrawal rules. They report a 2.31% annual withdrawal rate in one specified retirement scenario with a 5% probability of financial ruin, lower than conventional rule-of-thumb rates. This is not a suitable withdrawal number for our project: its horizon, assets, household assumptions and return distributions are different. Its contribution is to show that withdrawal sustainability is highly assumption-dependent and that “a safe rate” should not be imported as universal.

Clare et al., [“Measuring Sequence of Returns Risk”](https://doi.org/10.3905/jor.2020.1.066) (*The Journal of Retirement*, 2020), discuss the outsized effect of unfavorable returns near accumulation/decumulation boundaries. For a trading system, this supports modelling path risk and reserves, not just long-run average returns.

Before withdrawal logic can be activated under formal future authorization, a paper-only simulator should at minimum reconcile:

- realized gains/losses separately from unrealized marked-to-market changes;
- execution prices, fees and slippage against the frozen decision/price reference;
- peak-to-trough drawdown, tail loss, concentration and strategy/candidate exposure;
- reinvestment needs and a dedicated risk reserve before any distributable balance exists;
- cashflow policy behavior under long flat periods, loss clusters, regime change and adverse return sequences;
- the distinction between paper-account P&L and money actually available to the household.

No actual capital is currently listed as available. Therefore a euro-denominated family-withdrawal projection or a strategy success probability would be fabricated. The correct current output is a simulation-only operational contract, not a cashflow promise.

## 7. Concrete derivations for the project

These derivations translate external evidence into changes to the research process. They do **not** alter current gates.

### D1 — Use a source/PIT state machine as the shared primitive

For every event row, represent at least: exact event identity; exact source version; evidence for the first admissible public boundary; source-specific state transition; frozen entity/security exposure; correction/amendment lineage; uncertainty interval; and the receipt/code fingerprint that validates the row. If the exact public time is unknown, keep it unknown or bound it by supported evidence; do not create an exact timestamp from Action Date, quarter-end, source Last Modified Date, a download date or a generic publication rule.

### D2 — Make candidate orthogonality a pre-return falsifier

For each candidate, state (a) the economic object, (b) a fixed baseline/nearest comparator, (c) the alternative explanation that would make the candidate redundant, and (d) the decisive failure condition. Examples:

- I19 must distinguish institutional-demand × fixed accounting state from delayed disclosure and news-following.
- Q220 must distinguish narrative/structured discrepancy from simple accounting surprise and taxonomy/parser error.
- Q221 must distinguish event-specific award/option value from firm size/stability, sector, anticipated award and delayed publication.
  
If it cannot be distinguished without outcome-guided feature choice, merge or reject it. Do not rescue it by broadening the model or parameter search.

### D3 — Make source lineage failure a first-class stop state

A current response can differ from a historically frozen representation. A receipt that once passed is not current independent reproduction; a currently matching hash is not proof of historical public availability. Keep original receipts immutable, identify the precise missing evidence and allow offline analysis when it adds information. Do not repeat expensive source requests unless the new contract materially changes the source hypothesis and has been preregistered.

### D4 — Track model-design uncertainty, not just regression uncertainty

The run ledger should preserve candidate variants and their reasons for inclusion, including failed runs. A future authorized model comparison should report uncertainty across frozen design choices in addition to standard statistical error. Constrain the number of variants in advance; if a model search is justified, use a formal protocol for multiplicity and out-of-sample evidence rather than winner selection. Do not automatically import one paper's t-statistic hurdle or PBO formula without a method review.

### D5 — Add the implementation shortfall as a separate acceptance layer

A future signal cannot pass on gross predictive returns alone. Evaluate net return after predeclared costs under a fixed decision-to-execution delay and benchmark; report break-even costs and robustness to costs. In parallel, compare against a simple turnover-controlled portfolio so a complex optimizer must justify its incremental benefit. Performance analysis remains prohibited for the active candidates until their existing gates and formal authorizations clear.

### D6 — Keep withdrawal/capital rules downstream and path-aware

Future withdrawal logic must depend on realized P&L after costs, reinvestment and reserve constraints; it must be tested under adverse paths as well as expected returns. Do not import a 2.31%, 4% or any other generic withdrawal rate. Keep “available cash,” “unrealized equity,” “realized net P&L,” “risk reserve” and “distributable amount” as distinct, reconciled states.

## 8. Prioritized next steps under the existing lock

| Priority | Lane | Immediate action | Positive completion means | Stop rule / not authorized |
|---|---|---|---|---|
| 1 | Q104:I19 — Formal Readiness | Resolve the already-frozen residual-key/source chain without restarting the census; preserve the 36-row sidecar boundary and the seven identity conflicts/ten 404 branches. | A new immutable receipt demonstrates exact identity, usable source evidence and acceptance-time completeness for the specific frozen rows. | No bulk date-precedence change, no assumption from 13F quarter-end, no full compiler/independent PIT while required rows remain unresolved, no performance. |
| 2 | Q220 — Formal Readiness | Continue offline source-vintage and expected-hash lineage reconciliation from preserved receipts/code/artifacts. | Explain the expected-hash provenance with verifiable immutable evidence or preserve the blocked state with an exact missing-evidence statement. | No redownload of multi-GB Feeds or primary documents, no hash/population rewrite to force a pass, no performance. |
| 3 | Q221 — Frontier/PIT | Close the latest archive route as unavailable/incomplete. Consider only a materially different documented source contract with historical per-record version/public-boundary semantics and a pre-event identity path. | Bounded, authorized source feasibility yields a versioned row that can be exactly paired to frozen transaction identity, or a documented no-go. | No repeat of FPDS redirects, exact Wayback CDX, Arquivo.pt TimeMap or the failed Common Crawl query contract; no WARC payload; no assumed SAM key; no 348-key expansion. |
| 4 | Shared governance | Use the same future preregistration template for PIT boundary, row identity, revision semantics, mutational falsifier, source budget, alternative explanation and cost contract. | Fewer ambiguous receipts and more decision-relevant reuse across lanes. | No candidate addition, no resource filler jobs, no gate relaxation. |
| 5 | Future only, after formal prerequisites | Freeze a simple benchmark and a small challenger set; then assess OOS, robustness, net implementation shortfall and capital-preservation behavior. | Independently reproducible evidence after the designated formal gates. | No current authorization for performance, holdout selection, ranking, tuning, promotion, orders or live execution. |

## 9. What this synthesis does and does not decide

**Decided:** Global replication results are heterogeneous and method-dependent; the project should prioritize independent falsification, correct information clocks, incremental mechanism testing, and net implementation. Q104:I19, Q220 and Q221 should remain the only active execution candidates under the current lock. Their current source/PIT blockers are not overridden by outside literature. The procurement literature supports testing conditional contract mechanisms but does not establish a universal positive award effect. XBRL evidence supports a processing-cost mechanism but not a guaranteed return premium. Institutional ownership reports are lagged disclosures and may be news-following rather than direct skill.

**Not decided:** whether any project candidate has positive expected net returns; how likely any strategy is to succeed; the optimal portfolio allocation, withdrawal rate, or future cashflow; whether an external paper's reported effect survives the project's exact universe and costs; or any authorization to run performance, choose holdouts/assets/horizons, rank, tune, promote, place orders or trade live.

**Governance:** this document is literature synthesis and a proposed research-process derivation. External papers and language-model synthesis are not scientific evidence for project candidates. Paper-only remains enforced; actual capital remains €0; the €2,000 amount in the North Star remains simulation-only. No current project gate or candidate definition is modified here.

## References

### Factor replication, multiple testing and model selection
1. Hou, Xue and Zhang (2020), [“Replicating Anomalies”](https://academic.oup.com/rfs/article/33/5/2019/5236964), Review of Financial Studies.
2. Harvey, Liu and Zhu (2016), [“… and the Cross-Section of Expected Returns”](https://doi.org/10.1093/rfs/hhv059), Review of Financial Studies.
3. Jensen, Kelly and Pedersen (2021), [“Is There a Replication Crisis in Finance?”](https://doi.org/10.3386/w28432), NBER Working Paper.
4. Jacobs and Müller (2020), [“Anomalies across the globe: Once public, no longer existent?”](https://doi.org/10.1016/j.jfineco.2019.06.004), Journal of Financial Economics.
5. Feng, Giglio and Xiu (2019), [“Taming the Factor Zoo: A Test of New Factors”](https://consensus.app/papers/taming-the-factor-zoo-a-test-of-new-factors-feng-giglio/9cd7d142463256aba0cd20b1d130726f/?utm_source=chatgpt), The Journal of Finance.
6. Bailey et al. (2016), [“The Probability of Backtest Overfitting”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253), Journal of Computational Finance.
7. Bailey and López de Prado (2014), [“The Deflated Sharpe Ratio”](https://www.davidhbailey.com/dhbpapers/deflated-sharpe.pdf), The Journal of Portfolio Management.
8. Chen, Hanauer and Kalsbach (2026 revised working paper), [“Design choices, machine learning, and the cross-section of stock returns”](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5031755).

### Global predictability and implementation
9. Azevedo, Kaiser and Mueller (2023), [“Stock market anomalies and machine learning across the globe”](https://link.springer.com/article/10.1057/s41260-023-00318-z), Journal of Asset Management.
10. Patton and Weller (2020), [“What you see is not what you get: The costs of trading market anomalies”](https://doi.org/10.1016/j.jfineco.2020.02.012), Journal of Financial Economics.
11. Johansson, Sabbatucci and Tamoni (2025), [“Tradable Risk Factors for Institutional and Retail Investors”](https://doi.org/10.1093/rof/rfae034), Review of Finance.
12. Li, Chow, Pickard and Garg (2019), [“Transaction Costs of Factor-Investing Strategies”](https://doi.org/10.1080/0015198X.2019.1567190), Financial Analysts Journal.
13. DeMiguel, Garlappi and Uppal (2009), [“Optimal Versus Naive Diversification”](https://doi.org/10.1093/rfs/hhm075), Review of Financial Studies.

### Institutional disclosures, XBRL and procurement
14. U.S. SEC, [Form 13F FAQs](https://www.sec.gov/rules-regulations/staff-guidance/frequently-asked-questions-about-form-13f).
15. Wang (2024), [“Institutional trading, news, and accounting anomalies”](https://www.sciencedirect.com/science/article/pii/S0165410124000168), Journal of Accounting and Economics.
16. U.S. SEC, [EDGAR Application Programming Interfaces](https://www.sec.gov/search-filings/edgar-application-programming-interfaces).
17. Blankespoor (2019), [“The Impact of Information Processing Costs on Firm Disclosure Choice: Evidence from the XBRL Mandate”](https://doi.org/10.1111/1475-679X.12268), Journal of Accounting Research.
18. Dong, Li, Lin and Ni (2016), [“Does Information-Processing Cost Affect Firm-Specific Information Acquisition? Evidence from XBRL Adoption”](https://doi.org/10.1017/S0022109016000235), Journal of Financial and Quantitative Analysis.
19. Efendi, Park and Smith (2014), [“Do XBRL filings enhance informational efficiency? Early evidence from post-earnings announcement drift”](https://www.sciencedirect.com/science/article/pii/S0148296313002555), Journal of Business Research.
20. Pyun (2025), [“Trading on government contracts: The investment potential of public procurement awards”](https://www.sciencedirect.com/science/article/pii/S0165176525001727), Economics Letters.
21. Esqueda, Ngo and Susnjara (2019), [“The effect of government contracts on corporate valuation”](https://doi.org/10.1016/j.jbankfin.2019.07.003), Journal of Banking & Finance.
22. Dong et al. (2024), [“Impact of Government Outsourcing Contracts on High-Tech Vendors: An Empirical Study”](https://consensus.app/papers/impact-of-government-outsourcing-contracts-on-hightech-dong-hu/46d87e6e08ab585c98dce6c522aa1555/?utm_source=chatgpt), Journal of Management Information Systems.
23. Arora, Belenzon, Cioaca and Ferracuti (2025), [“The Private Value of Innovating for the Government”](https://doi.org/10.3386/w33880), NBER Working Paper.

### Capital preservation and withdrawals
24. Anarkulova, Cederburg, O’Doherty and Sias (2025), [“The safe withdrawal rate: evidence from a broad sample of developed markets”](https://doi.org/10.1017/s1474747225000010), Journal of Pension Economics & Finance.
25. Clare et al. (2020), [“Measuring Sequence of Returns Risk”](https://doi.org/10.3905/jor.2020.1.066), The Journal of Retirement.
