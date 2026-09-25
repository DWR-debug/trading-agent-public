# Q017 Orthogonal Hypothesis Design Round — 2026-09-25

## Status

**DESIGN_ONLY**. This artifact is research design material, not performance evidence and does not authorize a performance trial.

## Evidence basis

Q010's frozen cross-trial diagnosis reports the same structural bottleneck across the four performance-valid trials: 4/4 exceeded the 10% research drawdown gate and 4/4 failed at least one fixed-control non-deterioration condition; 3/4 also failed the OOS/IS threshold and 3/4 the 10% holdout-drawdown gate. Positive holdout return alone was therefore insufficient.

Q014 found strong redundancy within the fixed GDELT intensity/breadth group and materially lower redundancy of tone against that group, but return associations were mixed and remained descriptive.

Q016 was an exact temporal replication of Q015. Its frozen execution produced **DATA_INSUFFICIENT** with zero observations/event windows, so the GDELT mechanism-discrimination line does not currently authorize a performance study.

Therefore Q017 deliberately moves away from:
- portfolio-risk controls;
- volatility scaling;
- trend-signal consistency;
- position-lifecycle exits;
- the Q011–Q016 GDELT feature family.

## Candidate mechanism families

The families below are deliberately presented without ranking or selection.

### A — Macro-surprise state transition

**Mechanism:** market prices can respond differently when newly released macro information differs from the prior information set, because the information shock changes the expected path of rates/growth/inflation before slower price-trend signals fully adapt.

**Data source:** ALFRED/FRED vintage macro series with release/publication metadata. Candidate fixed inputs for preregistration: a small, explicitly enumerated set of release series and their published values only.

**Point-in-time rule:** use the first vintage/value available at or before the decision timestamp; never use later revisions. Signal state is computed only from information that was public at the timestamp.

**Fixed-rule concept:** convert each preregistered macro release into a signed surprise relative to its immediately preceding available vintage/observation and aggregate by a fixed sign map stated before data evaluation.

**Expected mechanism:** an information-state transition may alter short-horizon cross-asset return distributions and/or reduce the persistence of a stale prior positioning state.

**Falsification criterion:** on the preregistered disjoint universe and horizon, the fixed rule must fail to show an improvement over the fixed control on the preregistered primary statistic and must not create a statistically/economically meaningful improvement after costs. No post-hoc release, sign, horizon or asset changes are allowed.

**Cost contract:** free/public historical macro data; cache the exact vintages and release metadata immutably; no paid data feed.

**Coverage contract:** every required release vintage must be present and timestamp-resolvable for the complete preregistered period, otherwise the study is DATA_INSUFFICIENT.

**Disjoint validation:** fresh symbol-disjoint assets versus all earlier performance trials, with the universe and horizon fixed before evaluation.

### B — CFTC positioning / crowding state

**Mechanism:** large changes in disclosed speculative positioning can represent crowding, de-crowding or forced repositioning that is not equivalent to price trend or portfolio risk management.

**Data source:** CFTC Commitments of Traders public weekly reports, using only data available from the report's publication time onward.

**Point-in-time rule:** a weekly positioning observation becomes usable only after the public report timestamp; no later corrections or revised historical classifications may leak backward.

**Fixed-rule concept:** use one preregistered normalized positioning state and its fixed direction-to-return mapping, with no asset-by-asset tuning.

**Expected mechanism:** extreme or rapidly changing positioning can alter forward return asymmetry through crowding and subsequent flow.

**Falsification criterion:** the fixed rule fails if it does not meet the preregistered primary out-of-sample criterion after transaction/holding-cost assumptions, or if any apparent effect disappears under the fixed control comparison.

**Cost contract:** free/public CFTC data; immutable raw-report cache plus transformation fingerprint; no paid positioning feed.

**Coverage contract:** publication dates, report contents and asset mapping must be complete for the full preregistered period; otherwise DATA_INSUFFICIENT.

**Disjoint validation:** fresh symbols/assets not used by prior performance trials, with any required benchmark mapping fixed before evaluation.

### C — Abnormal turnover / liquidity shock

**Mechanism:** an abnormal change in traded volume relative to a fixed historical baseline can reflect attention, liquidity demand or forced participation without relying on a long-horizon trend signal.

**Data source:** Yahoo Finance daily OHLCV, fetched once per frozen study window and stored with SHA-256 provenance.

**Point-in-time rule:** only OHLCV through the decision date may be used; the signal for day t is generated from data no later than the close used by the rule and acts on the next allowed bar.

**Fixed-rule concept:** fixed abnormal-turnover statistic based on volume relative to a preregistered trailing baseline, with one fixed direction rule declared before data evaluation.

**Expected mechanism:** liquidity/participation shocks may predict short-term continuation or reversal through temporary price pressure and subsequent normalization.

**Falsification criterion:** the fixed rule fails if the primary statistic does not beat the fixed control after costs and if the predefined risk/non-deterioration gates are not met. No baseline-window, threshold or asset search is permitted.

**Cost contract:** public daily OHLCV only; no paid intraday data.

**Coverage contract:** complete OHLCV coverage for every required asset/date, otherwise DATA_INSUFFICIENT.

**Disjoint validation:** fresh symbol-disjoint universe; no asset chosen after inspecting signal results.

## Common governance contract

All three families are design candidates only.

Before any performance execution:
1. exactly one fixed rule must be selected by the formal research-governance process, not by holdout performance;
2. the full rule, universe, horizon, costs, gates and falsification criteria must be frozen;
3. data coverage must be preflighted before performance execution;
4. validation must use a fully symbol-disjoint universe;
5. no parameter, threshold, asset, feature, release, horizon or holdout selection is permitted after observing results;
6. negative evidence is used to define research boundaries, not to tune the candidate;
7. Q017 itself creates no performance evidence and no promotion rights.

## Resource policy

Agent/Codex usage is limited to:
- hypothesis generation;
- adversarial review;
- coverage/governance design;
- code review.

Deterministic GitHub Actions runners perform reproducible computations. Public-repository standard runners are preferred because GitHub documents them as free. No paid agent/API budget is required for Q017 design.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
