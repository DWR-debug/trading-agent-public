# Frontier Candidate Seeds — 2026-10-01

This is an out-of-band candidate seed list. It does not modify the frozen active candidate inventory, create performance authorization, or rank candidates.

Admission requires a separate design contract, explicit deduplication against the active inventory, source/PIT feasibility, ex-ante preregistration, and only then (if still justified) a separate performance authorization. No holdout, parameter, asset, threshold, horizon, family or variant selection may be used for admission.

## S05 — PRE_PUBLIC_ANOMALY_ANTICIPATION_STATE

Hypothesis seed: some anomaly signals may become partially predictable before the accounting/event inputs that formally publish the anomaly signal become public. A deterministic adaptation would model only the publication-lag structure of already-frozen anomaly inputs and ask whether a fixed pre-publication state exists.

Potential public reconstruction: existing SEC/XBRL filing timestamps plus a frozen, already-defined anomaly signal family. The state would use only information public before the anomaly signal's formal availability timestamp; no post-hoc prediction target, horizon or feature search.

PIT constraints: EDGAR acceptance time is the information boundary; report period is never treated as publication time; future amendments cannot rewrite prior states.

Primary feasibility risk: this can easily become circular if the anomaly definition or target is allowed to move after observing outcomes. The entire anomaly source set and publication-lag contract must therefore be frozen before any test.

External inspiration: Bowles, Reed, Ringgenberg & Thornock, "Predicting Anomalies" (2026 revision), which reports predictable patterns before publication of anomaly trading signals. This is hypothesis inspiration only, not project evidence.

Status: DESIGN_SEED_ONLY.

## S06 — INSIDER_INSTITUTIONAL_DISAGREEMENT_STATE

Hypothesis seed: the market-information content of a publicly disclosed insider open-market purchase may differ when institutions simultaneously increase, maintain or reduce the same issuer/security exposure.

Potential public reconstruction: SEC Forms 3/4/5 transaction data + SEC 13F quarterly holdings/transition data + SEC issuer/security identity contract. Use only qualifying open-market purchase transactions and PIT 13F states already public at each decision timestamp.

PIT constraints: Form 4 acceptance time and 13F filing acceptance time remain separate clocks; quarter-end holdings are not treated as visible at quarter-end; amendments are separate lineage; no transaction-type or manager subset may be selected after outcomes are observed.

Primary feasibility advantage: SEC insider transaction data are publicly available in as-filed data sets, and the project already has a source-feasible 13F transition population path.

Status: DESIGN_SEED_ONLY.

## S07 — CROSS_ISSUER_FILING_SYNCHRONY_STATE

Hypothesis seed: an issuer's response to a fresh filing may differ when economically related issuers experience an unusual cluster of newly public filings in the same information window.

Potential public reconstruction: SEC filing acceptance timestamps from fixed forms + a frozen issuer relationship map (for example, fixed SIC/industry mapping or an already validated peer graph). The state is the deterministic contemporaneous cross-issuer filing synchrony, not the filing content itself.

PIT constraints: peer membership and form inclusion must be frozen; only filings accepted by the decision cutoff enter the state; later filings and amendments must not rewrite earlier synchrony states.

Primary feasibility advantage: Q104:I22 already has a deterministic filing-arrival compiler and public SEC acceptance-time boundary; this seed is deliberately separated from text similarity and uses event synchrony as the distinct mechanism.

Status: DESIGN_SEED_ONLY.

## S08 — SHAREHOLDER_EXPERIENCE_X_FILING_ARRIVAL

Hypothesis seed: the same filing-arrival shock may have different implications depending on whether the current shareholder cohort is predominantly in accumulated gain or loss.

Potential public reconstruction: the deterministic shareholder-experience construction described by Q082 + the frozen Q104:I22 filing-arrival state. Shares outstanding must be point-in-time valid; filing arrival remains anchored to EDGAR acceptance time.

PIT constraints: shareholder shares-outstanding facts and filing events must be independently cutoff-valid; no post-hoc cohort-window, event-window or interaction-direction search.

Primary feasibility advantage: both information legs already have project-specific design contracts and public-data feasibility paths. The integration itself would still require a separate design contract and mutation testing before any performance work.

Status: DESIGN_SEED_ONLY.

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

These seeds are deliberately not ranked. They are candidates for future feasibility work only.