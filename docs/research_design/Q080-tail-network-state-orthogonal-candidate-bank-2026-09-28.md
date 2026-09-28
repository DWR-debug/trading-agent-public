# Q080 — Tail, Network and State Orthogonal Candidate Bank

**Date:** 2026-09-28
**Status:** PREREGISTERED_DESIGN_ONLY / unranked

## Research objective

Q080 expands the candidate search into mechanisms structurally different from the current Q069 OHLCV bank and Q078 information-source bank. The emphasis is on firm-specific tail behavior, cross-asset information transmission and state-dependent market exposure.

The candidates are exploratory mechanisms. This document creates no performance evidence and authorizes no performance execution.

## Fixed candidate bank

### C17 — INDUSTRY_ADJUSTED_REVERSAL_21

At each decision close, compute the prior 21-session return of each asset and subtract a fixed equal-weight return of its assigned industry over the same completed window. Rank assets by the resulting firm-specific reversal score using the preregistered monotonic direction.

**Required prerequisite:** a historical industry/security mapping with a point-in-time effective date. A current classification backfilled across history is not acceptable.

**Primary risk:** classification survivorship and post-hoc industry reclassification.

### C18 — RESIDUAL_LEFT_TAIL_126

At each decision close, estimate firm-specific daily returns by removing the contemporaneous equal-weight universe return. Over the previous 126 completed sessions, compute the fixed statistic LTS = downside-semivariance(5% tail) minus upside-semivariance(95% tail). Rank ascending and use the two lowest LTS values as the long side; no threshold optimization or sign inversion is allowed.

**Required prerequisite:** deterministic residual construction and explicit handling of missing observations.

**Primary risk:** accidental future information through window alignment or distributional normalization.

### C19 — PEER_SPILLOVER_252_21

Build a return-similarity graph from the previous 252 completed sessions. For each asset, calculate the next-period peer signal as a deterministic correlation-weighted aggregate of peers' prior 21-session returns, then rank descending and use the two highest signals as the long side. The graph and weights are frozen for the decision; no future observations may alter the graph used for that decision.

**Required prerequisite:** PIT-safe rolling graph construction with no future recomputation.

**Primary risk:** graph instability, concentrated peer weights and latent common-mode exposure.

### C20 — DOWNSIDE_BETA_STATE_252

Estimate rolling downside beta versus the market using only completed sessions in the previous 252-session window. Rank downside beta ascending and use the two lowest downside-beta assets as the long side; no threshold search or direction reversal is allowed.

**Required prerequisite:** market benchmark and a deterministic definition of downside observations.

**Primary risk:** state leakage and accidental selection of a beta definition after observing returns.

### C21 — NEWS_VOLUME_VOL_DISAGREEMENT

Around independently timestamped public-news events, measure the volume/volatility relation using only observations available by the event cutoff. The candidate is the fixed disagreement signal described in the Q080 issue; rank the resulting elasticity descending and use the two highest-elasticity observations as the long side. The event source, public-availability timestamp and aggregation horizon must be frozen before any performance work.

**Required prerequisite:** reproducible event corpus, public-availability timestamp, entity mapping and mutation-PIT tests.

**Primary risk:** timestamp leakage and news-source revisions.

## Scientific governance

Before any Q080 candidate can reach performance:

1. Freeze source definitions, candidate formula, monotonic direction and decision horizon.
2. Validate data coverage and the exact point-in-time contract.
3. Run future/next-session mutation tests.
4. Use a fresh symbol-disjoint universe selected only by a fixed coverage contract.
5. Freeze the complete performance input bundle.
6. Issue a separate one-shot performance authorization.
7. Run the unchanged 13-gate contract with the existing cost model.
8. Reconcile immutable evidence before interpreting the result.

No candidate ranking, parameter search, threshold search, holdout selection, family selection or promotion is permitted.

## Literature context

The design is motivated by recent empirical work reporting:
- short-term reversal that becomes more visible after industry adjustment;
- cross-sectional return predictability from idiosyncratic asymmetry;
- peer-network effects in cross-stock return predictability;
- asymmetric downside/upside beta behavior;
- investor disagreement measures derived from the volume/volatility relation around firm news.

These papers are hypothesis-generation inputs only. They are not evidence for this project.

## Safety

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
