# Candidate Composition Contract — 2026-10-01

## Purpose

Create a deterministic, leakage-resistant layer for combining already-frozen candidate outputs later.

This document is **design-only**. It does not authorize performance evaluation, holdout use, candidate ranking, parameter/threshold/horizon search, promotion, or live execution.

## Design principle

A combination is a new research object with its own provenance. Component candidates remain independently identifiable; the composition layer may only consume outputs that already satisfy their own coverage/PIT contracts.

The composition layer must never become a hidden optimizer for weak candidates.

## Required component contract

Every component supplied to a composition must expose, at minimum:

- candidate/family identifier
- decision timestamp and eligible session
- deterministic direction and/or scalar score
- source/evidence fingerprint
- universe membership or entity mapping fingerprint
- availability/missingness state
- explicit signal-direction convention
- component version / preregistration identity

A component without a complete contract is **incompatible**, not silently repaired.

## Composition compatibility gate

Before any combined signal can be considered for formal research, the combination compiler must verify:

1. **PIT alignment** — every component value was public by the common decision cutoff.
2. **Entity alignment** — issuer/security/peer identifiers resolve deterministically.
3. **Session alignment** — all components are mapped to the same eligible decision session.
4. **Family lineage** — component outputs are frozen and independently fingerprinted.
5. **Missingness semantics** — missing values follow a fixed rule; no outcome-based imputation is permitted.
6. **Direction semantics** — sign conventions are frozen before any result is observed.
7. **No recursive leakage** — a component may not consume a later-stage combination that itself depends on the component.
8. **No duplicate information masquerading as independence** — correlated/derived components may be marked as the same mechanism lineage rather than counted as independent families.

Failure of any item yields `COMPOSITION_INCOMPATIBLE` with no performance interpretation.

## Predeclared composition families

The initial composition inventory is intentionally unranked:

### C1 — Sign Consensus State

Reduce each available frozen family to its predeclared direction and expose deterministic counts/dispersion of positive, negative and neutral family states.

No learned weights.

### C2 — Equal-Weight Family Score

Combine component scores with equal ex-ante family weights after each component passes the common contract.

No weight fitting and no return-conditioned scaling.

### C3 — Cross-Sectional Rank Consensus

Where a component contract defines a cross-sectional score, convert it to its already-declared cross-sectional rank representation and combine ranks using a fixed aggregation rule.

The rank convention must be part of the component preregistration; it may not be chosen after observing outcomes.

### C4 — Reliability Overlay

Apply the existing Q104:R9-style reliability/consensus state as a separate meta-state over an already frozen bundle.

The reliability layer is descriptive and deterministic; it cannot select the component family with the best observed performance.

### C5 — Abstention / No-Consensus State

Represent insufficient cross-family agreement as an explicit neutral/abstain state rather than forcing a position.

The abstention rule must be fixed before formal evaluation.

These are parallel design forms, not a ranking.

## Bundle templates

Future feasibility work may instantiate several orthogonal bundle templates without selecting a winner:

- **B1 Orthogonal Triad:** one price/market-state family + one SEC/information family + one cross-asset or demand family.
- **B2 Information Mesh:** multiple independently timestamped SEC information channels (for example filing arrival, 13F transition, Form 4, 13D/13G) with explicit clock separation.
- **B3 Reliability-Wrapped Bundle:** any already-frozen bundle plus the Q104:R9-style reliability state.
- **B4 Cross-Clock Interaction:** two components with distinct public-availability clocks, only after each clock passes its own PIT contract and the join contract proves the temporal ordering.

Templates are research shapes, not selected portfolios.

## Structural validation before performance

The first composition run must be structural only and use synthetic fixtures / controlled mutations to verify:

- future-event injection is detected;
- component fingerprint changes invalidate the bundle;
- issuer/security mismatches fail closed;
- session misalignment fails closed;
- missingness behavior is deterministic;
- duplicate lineage is detected;
- component ordering cannot change the resulting bundle fingerprint;
- the composition manifest records every component and its exact version;
- no holdout/performance field is consulted by the compiler.

Only after a valid structural receipt exists may a separately governed coverage/PIT/performance path be considered.

## Governance

- performance_authorized: false
- holdout_selection_allowed: false
- parameter_search_allowed: false
- asset_search_allowed: false
- threshold_search_allowed: false
- horizon_search_allowed: false
- family_ranking_allowed: false
- automatic_promotion: false
- paid_data_required: false
- live_trading_enabled: false
- orders_enabled: false
- paper_only: true

## Relationship to existing work

Q104:R9 already defines a cross-family consensus/reliability hypothesis. This contract makes the integration boundary explicit so future combinations can be built from independently frozen candidates without silently introducing selection or leakage.

Candidate-specific feasibility remains the first gate. Composition is downstream of component validity, not a substitute for it.
