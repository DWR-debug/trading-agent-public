# Research Frontier — Unusual Candidate Families (2026-09-28)

## Purpose

This is a **design-only frontier**, not a performance authorization list. The objective is to deliberately search for mechanisms that are economically or behaviorally different from the current momentum / low-beta / overnight / risk-control families.

Every item below must pass the same sequence before performance use:

1. exact rule freeze and provenance;
2. synthetic PIT/leakage mutation tests;
3. free/public data accessibility and historical coverage audit;
4. fresh symbol/time-disjoint input bundle where applicable;
5. separate one-shot performance authorization;
6. unchanged 13-gate evaluation and immutable reconciliation.

No parameter sweep, threshold search, asset search, horizon search, family ranking, holdout selection, automatic promotion or live execution is permitted in the frontier stage.

## Current machine-feasibility status — 2026-09-28

The frontier has now crossed its first machine-testable integrity boundary:

- C29 has a deterministic price-path construction with synthetic future/t+1 mutation tests.
- C30 has a deterministic PIT-bounded SEC risk-text peer state with synthetic leakage tests.
- C31 has a deterministic public-news persistence state using a conservative observed-time boundary and synthetic leakage tests.
- M4 has a deterministic industry-relative residual construction with synthetic future/t+1 mutation tests; historical PIT industry mapping remains a required data gate.
- M5 has a deterministic public-rebalance event state with publication/effective-time validation and revision conflict protection.

These implementations are **feasibility evidence only**. None is performance-authorized, ranked, promoted or considered a project result. Before any performance use, each mechanism still requires its actual historical public-data archive audit, immutable input preservation and the same one-shot authorization plus 13-gate evaluation used elsewhere in the project.

## Candidate frontier

### C29 — ILLUSION_MOMENTUM_GAP

Mechanism: the gap between a stock's compounded cumulative return and the arithmetic sum of its simple daily returns.

A 2026 Pacific-Basin Finance Journal paper explicitly proposes this discrepancy as “illusion momentum” and reports predictive evidence in Japanese and U.S. equities. The project adaptation should be deliberately simple: compute the fixed historical discrepancy from price returns and test whether its cross-sectional ordering contains information distinct from ordinary momentum.

Constraints:
- no horizon search;
- no nonlinear fit;
- fixed cross-sectional construction;
- no use of future corporate actions or restated data.

Source: Iwanaga & Hirose (2026), DOI 10.1016/j.pacfin.2026.103063.

### C30 — RISK_TEXT_PEER_PROPAGATION

Mechanism: build peer links from disclosed risk-factor language rather than sector membership or generic price correlation.

Use public SEC 10-K risk-factor text (Item 1A), a deterministic bag-of-words/TF-IDF representation, cosine similarity and a fixed rolling peer graph. The signal is the lagged return information of risk-similar peers.

This is intentionally separated from the existing MD&A textual-comomentum design in Q088: the information channel is **risk disclosure**, not management discussion topics.

Source inspiration: Yuan & Zhang (2026), “Risk-based peer networks and return predictability: Evidence from textual analysis on 10-K filings.”

### C31 — NEWS_SENTIMENT_PERSISTENCE_STATE

Mechanism: distinguish short persistence of news sentiment from long persistence, where the same sign of sentiment may first continue and later reverse.

The feasibility version should use only a freely accessible public news corpus with article timestamps, stable identifiers and reproducible historical retention. The first implementation must be text-light and deterministic; no paid sentiment vendor and no opaque LLM dependency.

Source inspiration: 2026 Economics Letters paper “The persistence of news sentiment: Implications for return predictability”, DOI 10.1016/j.econlet.2025.112803.

### M4 — INDUSTRY_RELATIVE_REVERSAL_RESIDUAL

Mechanism: isolate idiosyncratic short-term reversal by removing the contemporaneous industry component rather than ranking raw one-month returns.

This is a useful control for the current cross-sectional reversal experiments because it asks a different question: whether reversal survives after explicitly separating stock-specific and industry-wide movement.

Source inspiration: “Short-term reversal persists globally—If properly measured”, Economics Letters 2026, DOI 10.1016/j.econlet.2026.113113.

### M5 — BENCHMARK_DEMAND_SHOCK_CLOCK

Mechanism: use mechanically scheduled benchmark rebalances as an anticipated institutional-demand state.

The research version should model only events whose timing and membership are public before the decision point. The first implementation should keep the event calendar fixed and should not optimize event windows or index families.

Source inspiration: Broner et al. (2026), “Demand shocks in equity markets and firm responses”, and Nathan (2026), “Anticipated Orders and the Measurement of Stock Demand Elasticity: Evidence from Scheduled Index Rebalances.”

## Deliberately excluded for now

LLM-heavy alpha families are not on the immediate execution path because the project has a zero paid API budget. They can still inform deterministic, public-data approximations, but only when the data lineage can be reproduced without proprietary services.

## Research principle

The frontier is intentionally broad at the **mechanism** level but narrow at the **execution** level. We are looking for information channels that plausibly fail for different reasons than the existing price-only sleeves, while preserving the same evidence discipline.

The frontier is therefore allowed to be creative before it is allowed to be profitable.
