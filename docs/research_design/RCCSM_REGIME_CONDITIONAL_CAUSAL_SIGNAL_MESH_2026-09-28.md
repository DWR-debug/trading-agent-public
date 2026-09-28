# Research Design: Regime-Conditional Causal Signal Mesh (RCCSM)

Date: 2026-09-28
Status: DESIGN-ONLY / NO PERFORMANCE AUTHORIZATION
Safety: PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; ORDERS_ENABLED=False; AUTOMATIC_PROMOTION=False

## 1. Research objective

Build a project-specific research architecture in which heterogeneous alpha mechanisms are not simply averaged or ranked globally. Instead, the system first determines whether the current information state makes a mechanism structurally admissible, and only then allows that mechanism to contribute.

Research question:

Can a frozen collection of orthogonal mechanisms become more robust when allocation is conditioned on a pre-specified, lagged market-state topology rather than on a global return ranking?

This is an architecture hypothesis, not a claim that the method is novel in the academic literature or that it will produce positive returns.

## 2. Core idea

The RCCSM has three distinct layers.

### Layer A — Mechanism nodes

Each node is a fixed research family with a frozen definition, for example:

- trend / trend efficiency
- cross-sectional momentum
- reversal
- volatility / downside-risk state
- event timing
- fundamental profitability
- public-information persistence
- industry-relative residuals

A node is never re-parameterized inside the validation experiment.

### Layer B — State topology

The system observes only lagged, pre-registered state descriptors. Examples:

- cross-asset dispersion
- market breadth
- volatility level and volatility change
- trend coherence
- correlation concentration
- event-density state
- liquidity / turnover state

The state layer must not inspect future returns, future labels, holdout outcomes, or post-period statistics.

### Layer C — Admissibility routing

Instead of predicting returns directly, the state layer produces a binary/ternary admissibility decision per mechanism:

- ADMISSIBLE
- NEUTRAL
- INADMISSIBLE

The first implementation should use a deterministic rule table fixed before the performance trial. The rules may be derived only from historical research data under a declared freeze procedure. No continuous optimizer is permitted in the first feasibility version.

The key hypothesis is about conditional stability, not raw predictive magnitude.

## 3. Novel project-level property

The differentiator is a strict separation between:

1. discovering a mechanism,
2. describing the market state,
3. deciding whether that mechanism is admissible in that state,
4. allocating risk among admissible mechanisms.

These decisions are kept in different immutable contracts.

This allows a negative result to be diagnostic: the project can distinguish “the mechanism failed” from “the mechanism may only be state-dependent” from “the state descriptor itself was unstable.”

## 4. Anti-overfit constraints

The initial RCCSM experiment MUST enforce:

- no asset search during evaluation;
- no parameter search after freeze;
- no threshold search on holdout;
- no family deletion because of holdout performance;
- no state definition derived from holdout returns;
- no post-hoc state reclassification;
- no selector trained on the final holdout;
- no hidden ensemble weighting;
- no live execution path.

Any violation is a governance failure, not a tuning opportunity.

## 5. Information timing

Every state observation must carry:

- observation timestamp;
- source timestamp;
- availability timestamp;
- acceptance timestamp where the source supplies one;
- feature fingerprint;
- source contract fingerprint.

A state is eligible at decision time t only if its complete input set was available no later than the declared decision cutoff for t.

For event/news/fundamental sources, the evidence model must use publication/acceptance chronology rather than report-period chronology.

## 6. Research sequence

### RCCSM-0 — Feasibility

No performance evaluation.

Deliverables:

- immutable mechanism registry;
- immutable state descriptor registry;
- deterministic state calculation;
- timing/PIT audit;
- synthetic leakage tests;
- contradiction tests;
- provenance manifest.

### RCCSM-1 — Frozen synthetic validation

Use synthetic return processes designed to contain known state-dependent and state-independent mechanisms.

Success criteria are structural:

- routing activates only under intended states;
- future information cannot change past routing;
- identical inputs reproduce byte-identical outputs;
- intentionally leaked inputs are detected.

### RCCSM-2 — Fresh disjoint observational validation

Only after RCCSM-0 and RCCSM-1 pass.

Use a completely fresh, symbol-disjoint input set under the project's normal preregistration and one-shot evidence contract.

The performance evaluator remains unchanged.

### RCCSM-3 — Mechanism-level attribution

If a performance trial passes the formal evidence contract, decompose the result into:

- contribution by mechanism;
- contribution by state;
- turnover/cost contribution;
- drawdown contribution;
- disagreement contribution;
- concentration contribution.

This decomposition is for diagnosis, not post-hoc strategy selection.

## 7. Disagreement as an explicit state variable

A particularly important extension is the mechanism disagreement field.

For each decision date, measure whether independent mechanism nodes agree, disagree, or are silent.

The architecture must not assume disagreement is bad.

Instead, pre-register three interpretations to test separately:

- broad agreement may indicate stronger common regime structure;
- strong disagreement may identify transition states;
- high silence may indicate insufficient information.

The first experiment should test the structural behavior of these states before assigning them any performance preference.

## 8. Risk allocation principle

RCCSM must not maximize expected return.

The first allocator should be a bounded, deterministic risk-budget allocator over admissible nodes, subject to:

- gross exposure cap;
- per-node risk cap;
- correlation/concentration cap;
- turnover cap;
- portfolio drawdown guard;
- financing/borrow-cost contract where relevant.

Allocator failure must degrade to lower exposure or zero exposure, never to uncontrolled substitution.

## 9. Why this direction fits the project

The project has already accumulated evidence that isolated positive holdouts are insufficient when rolling stability and drawdown behavior are weak.

RCCSM attacks a different question:

Is robustness improved by explicitly modelling when a mechanism is structurally plausible, rather than assuming every discovered signal should be active at all times?

That question is compatible with the existing evidence discipline and can be tested without sacrificing the holdout.

## 10. Required evidence contract

Before any performance authorization, the experiment must produce:

1. frozen mechanism manifest;
2. frozen state manifest;
3. PIT/timing audit;
4. disjointness audit;
5. deterministic replay fingerprint;
6. synthetic leakage tests;
7. governance test result;
8. preregistration record;
9. explicit performance authorization file set to false until preflight passes.

No result may be promoted because it is economically attractive.

## 11. Non-goals

This document does not authorize:

- optimization of thresholds;
- automatic strategy promotion;
- leverage expansion;
- live trading;
- holdout selection;
- cherry-picking of mechanisms;
- claims of guaranteed or regular income.

The project goal remains robust, eventually withdrawable cashflow, subject to scientific validation and capital preservation.

## 12. First implementation target

The first code artifact should be a feasibility-only registry and deterministic router with synthetic data tests.

It should consume frozen mechanism IDs and state IDs and emit only:

state_id, mechanism_id, admissibility, provenance_fingerprint

No P&L, ranking, Sharpe ratio, or optimization output belongs in RCCSM-0.
