# Frontier Candidate Seeds — 2026-09-30

This document is an out-of-band candidate seed list. It does not modify the frozen
48-candidate inventory and does not create performance authorization.

All seeds remain unranked. Admission to the active research inventory requires a
separate source/PIT feasibility contract, explicit deduplication, and ex-ante
preregistration. No holdout, parameter search, asset search or performance result
may be used for admission.

## S01 — Foreign-institution ownership change

**Hypothesis seed:** distinguish changes in short-term foreign institutional
ownership from domestic institutional ownership.

**Potential public reconstruction:** SEC Form 13F holdings + public filer/manager
metadata, with the publication lag preserved and manager domicile fixed before
observation.

**PIT constraints:** quarter-end holdings are not visible at the quarter-end
decision time; the EDGAR filing/publication timestamp must define the earliest
usable state. Manager identity, amendments and security identifiers must be
immutable.

**Dedup note:** likely a refinement of the existing Q073:I7/Q078 institutional
ownership family and must be explicitly compared before admission.

**Status:** SOURCE_FEASIBILITY_SEED_ONLY.

Literature pointer: O. K. et al., “Can foreign investors predict better? investment
horizons, investor domicile, and stock return predictability” (Finance Research
Open, 2026), DOI 10.1016/j.finr.2026.100154.

## S02 — Policy-risk disclosure exposure state

**Hypothesis seed:** measure pre-event policy-risk language in public company
filings and relate it to a deterministic, externally timestamped policy shock.

**Potential public reconstruction:** SEC 10-K/10-Q text + a separately versioned
public government/event calendar. The event taxonomy and text representation must
be frozen before any performance work.

**PIT constraints:** filing acceptance time is the disclosure boundary; event
publication/announcement time and effective time must remain separate; no
post-event revisions may enter the pre-event state.

**Status:** DESIGN_SEED_ONLY; historical/event-family generalization is unresolved.

Literature pointer: “Tariff-risk disclosure in 10-Ks and stock market responses to
the Liberation Day shock” (Economics Letters, 2026), DOI
10.1016/j.econlet.2026.112947.

## S03 — Validated corporate narrative/evidence alignment

**Hypothesis seed:** distinguish dated corporate claims that can be linked to
independent contemporaneous evidence from claims that cannot.

**Potential public reconstruction:** public filings + independently archived,
timestamped external evidence. Any language-model component would require a
deterministic labeling protocol, immutable prompts/models, and a non-LLM
replication path before it could become formal research input.

**Status:** DESIGN_SEED_ONLY; reproducibility and free historical evidence are the
primary gates.

Literature pointer: “Validated corporate narratives and return predictability:
Evidence from China’s STAR Market” (Finance Research Letters, 2026), DOI
10.1016/j.frl.2026.110352.

## S04 — Small-trade / order-splitting state

**Hypothesis seed:** trade-size composition may contain information about
institutional order splitting.

**Data gate:** the cited study uses trade-level information. A complete, free,
historical U.S. security-level tick dataset has not been established for this
project.

**Status:** BLOCKED_BY_FREE_HISTORICAL_DATA_POLICY unless a reproducible public
archive is independently verified.

Literature pointer: “Small trades, order splitting, and stock returns: Evidence
from China's stock markets” (2026), ScienceDirect.

## Governance

- performance_authorized: false
- holdout_selection_allowed: false
- parameter_search_allowed: false
- asset_search_allowed: false
- family_ranking_allowed: false
- automatic_promotion: false
