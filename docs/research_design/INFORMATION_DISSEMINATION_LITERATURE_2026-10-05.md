# Information Dissemination Literature Synthesis — 2026-10-05

## Scope

This memo records literature-derived mechanism hypotheses for the public-information frontier. It is research inspiration only. It does not constitute performance evidence, ranking, parameter selection, holdout selection, promotion or live-trading authorization.

## High-value findings

### 1. Event time is multi-stage, not a single timestamp

Kargarzadeh et al., *Buy the Rumor, Sell the News: When Is News Priced In?* (arXiv:2608.14014, 2026), separates first reports from follow-up coverage and finds that price movement associated with news is concentrated before and at publication. The paper explicitly warns that repeated coverage can inflate an apparent pre-publication effect and that coverage presence itself is a baseline.

Project implication:
- preserve first-observation versus follow-up status;
- never substitute occurrence time for public availability;
- treat coverage presence and event direction as separate constructs;
- keep source provenance as part of the event definition.

### 2. Public-web archives can provide deterministic historical information-flow inputs

Jazbec et al., *On the impact of publicly available news and information transfer to financial markets* (arXiv:2010.12002, 2020), demonstrates a reproducible pipeline using Common Crawl news archives to study propagation of publicly available information to markets.

Project implication:
- public historical archives can be used as source material when the archived capture boundary is independently frozen;
- a public-web information channel should be treated as a historical archive problem, not simply as a current API;
- article/story deduplication is necessary because repeated reporting is not independent information.

### 3. A single economic event can release information at different speeds

Yu, Liu, Zhang & He, *Fast Numbers, Slow Language: Bridging Quantitative and Qualitative Earnings Signals* (arXiv:2606.29734, 2026), distinguishes rapid quantitative earnings information from later qualitative conference-call information.

Project implication:
- information-latency features can be economically distinct from information content;
- same-event multi-stage clocks are worth testing;
- Q204 should remain focused on release latency rather than news sentiment.

### 4. Information diffusion can be networked, but network effects are easily confounded

Ren et al., *The Effect of Investor-Driven Information Diffusion on Excess Comovement: Evidence from Retail and Institutional Investors in China and the United States* (arXiv:2605.08726, 2026), reviews and measures supply- and demand-side diffusion channels across stocks and finds that diffusion speed can differ across connected securities. Importantly, the paper also emphasizes that common information and investor behavior can create apparent links.

Project implication:
- Q207 should be a diffusion-speed hypothesis, not a return-correlation strategy;
- the relation graph must be frozen before outcomes;
- common-shock controls and graph-history integrity are first-order gates;
- a current network reconstructed after the fact is not admissible as a PIT graph.

## Candidate decisions

### Q206 — Cross-channel arrival dispersion

Decision: merge into Q204.

Reason: the cleanest interpretation is as a special case of information-release latency. A standalone family would create unnecessary multiplicity unless an independent economic mechanism is demonstrated.

### Q207 — Network information propagation lag

Decision: retain as design-only.

Reason: it remains genuinely orthogonal to price-only signals and to pure event-content features. The decisive burden is historical graph provenance. The cheapest falsifier is to freeze a pre-event graph and verify that future graph mutations cannot alter the historical relation set.

### Q208 — Science-to-patent translation

Decision: merge into the Q196/Q199 patent-information architecture.

Reason: the economically interesting object is the public technology-disclosure sequence and citation provenance. A separate family would largely duplicate patent-publication/citation timing.

### Q209 — ESG disclosure timing disparity

Decision: discard for now.

Reason: high risk of proprietary-provider dependence, weak source independence and unclear historical reproducibility relative to the existing public-source frontier.

### Q210 — Public-information dissemination breadth

Decision: retain as design-only.

Definition:
At a fixed historical decision boundary, count the number of genuinely independent public channels that have disclosed the same event/state. The construct measures dissemination breadth/salience, not sentiment and not raw media volume.

Minimum requirements:
- immutable historical snapshots for every channel;
- a predeclared channel-independence taxonomy;
- earliest defensible public-observation timestamp per channel;
- event/entity mapping frozen before outcome observation;
- correction/withdrawal lineage;
- independent historical reproduction.

Cheap falsifiers:
1. collapse channels that share an upstream feed;
2. insert future channel observations and require historical breadth to remain unchanged;
3. substitute occurrence/action time for public-observation time and require a contract failure;
4. mutate later corrections/withdrawals and require preservation of the original prefix;
5. permute channel observations within calendar blocks and verify that the construction does not create an artifact.

## New research principle

The frontier should distinguish three related but non-identical dimensions:

- **Speed** — how long information takes to become public (Q204).
- **Dispersion** — how differently two legitimate channels expose the same information (Q206 as a Q204 subcase).
- **Breadth** — how widely the information has independently propagated by a fixed boundary (Q210).

The three dimensions must not be combined into a composite score before component-level PIT validity. Any later composition would itself require a new frozen contract and independent validation.

## Scientific boundary

No item in this memo authorizes:
- performance;
- holdout selection;
- return-based ranking;
- parameter, threshold or horizon search;
- asset selection;
- promotion;
- live execution.

All conclusions above are hypothesis-generation / design guidance and must be independently reproduced by deterministic project tooling.
