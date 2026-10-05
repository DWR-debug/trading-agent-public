# Literature Frontier Expansion — 2026-10-05

## Status
Design-only literature expansion and source/PIT feasibility. No market-performance test, holdout selection, ranking, tuning, promotion or live execution is authorized by this document.

## Three new mechanisms
- Q211 — Patent semantic information state: patent text can contain economically relevant information beyond counts and citations.
- Q212 — Supply-chain disclosure sentiment propagation: linked firms can transmit information at different speeds; network disclosure tone can add information beyond focal-firm tone.
- Q213 — News-disagreement elasticity state: disagreement around firm news can be inferred from high-frequency volume/volatility coupling.

## Q211 — Patent semantic information state
Zheng (2025), *Can investors learn from patent documents? Evidence from textual analysis*, Contemporary Accounting Research 42(2), 1331–1358, DOI 10.1111/1911-3846.13036, reports that patent text adds information beyond structured patent, firm and technology variables and predicts future earnings characteristics and stock returns. Underreaction is weaker after pre-grant publication becomes mandatory.

Project interpretation: the potential edge is the information in what the patent says, not simply patent counts, grants or citations. This is distinct from Q199 publication shock and Q196 citation provenance.

Implementation: first use deterministic fixed-vocabulary and backward-only similarity features on the historical publication corpus. No training on post-event documents. Any pretrained model requires an explicit training-corpus leakage audit.

Assessment: source feasibility HIGH because the USPTO family is already established; PIT MEDIUM because historical publication completeness and immutable assignee/issuer mapping remain binding; expected information value HIGH. Priority P1.

Cheap falsifiers: publication-date shifts, assignee-map shuffles, within-calendar text permutation, future-prosecution mutation, harmless normalization invariance.

## Q212 — Supply-chain disclosure sentiment propagation
Hertzel & Schiller (2025), *Speed Matters: Limited Attention and Supply Chain Information Diffusion*, Management Science, DOI 10.1287/mnsc.2023.00291, links limited attention to slower customer-to-supplier information diffusion. Heckmann (2026), *Sentiment and Return Predictability in Global Supply Chains*, SSRN, posted 20 August 2026, reports customer/supplier sentiment spillovers beyond focal-firm tone and stronger spillovers for low-attention firms.

Project interpretation: the distinct object is network-local information that has not yet reached the focal issuer, not another generic sentiment score.

Implementation: first test exact transcript-route source feasibility. In parallel test a separate public-only SEC-text adaptation using accepted filing timestamps. The adaptation is a new construct and cannot inherit transcript-study performance claims.

Assessment: transcript route LOW-MEDIUM; SEC-text adaptation source access MEDIUM-HIGH, relationship mapping MEDIUM; expected information value MEDIUM-HIGH. Priority P1 for feasibility only.

Cheap falsifiers: network-edge permutation, focal-only versus network-only decomposition, future amendments, public-boundary shifts, issuer-map shuffles.

## Q213 — News-disagreement elasticity state
Li & Luan (2025), *News-based investor disagreement and stock returns*, Review of Accounting Studies 30, 2312–2375, DOI 10.1007/s11142-025-09897-1, uses volume-volatility elasticity around firm news as an investor-disagreement measure. Higher elasticity indicates less disagreement; the relation survives controls for other volume/volatility measures and varies with optimism versus uncertainty.

Project interpretation: this targets interpretation disagreement rather than raw news tone or raw attention.

Implementation: source feasibility first. The current free stack does not yet prove a multi-year historical equity-intraday archive plus public-news timestamps. A recent intraday endpoint is insufficient for formal historical PIT.

Assessment: current source feasibility LOW and PIT LOW; potential information value HIGH if the historical data problem can be solved. Priority P2 contingent.

Cheap falsifiers: intraday aggregation sensitivity, publication-time shifts, event-window permutations, story-clustering perturbations, raw-volume/raw-volatility/jump baselines.

## Cross-paper relationships
- Speed, breadth, content and disagreement should remain separate state dimensions; Q204/Q207/Q210 should not be collapsed into one attention scalar.
- Multiple clocks are normal. Preserve the earliest defensible public boundary and later process-stage clocks separately.
- Apparent predictability can be a limit-to-arbitrage proxy. Muravyev, Pearson & Pollet (2025) show that excluding high-borrow-fee stocks reduces IV spread/skew predictability by at least two-thirds; options signals therefore require short-borrow de-duplication.
- Revision-aware research must distinguish information-availability time from observation time. Ahmad (2026), *Time-Series Foundation Models That Understand Data Revisions*, demonstrates how hindsight contamination can change measured performance.

## Decision
P1: Q211.
P1 feasibility only: Q212.
P2 contingent: Q213.
Governance: future PIT contracts should explicitly target the first publicly available value/state rather than the later revised value.

All three tracks remain discovery-only and non-authorizing.