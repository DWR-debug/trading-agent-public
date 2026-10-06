# Candidate Prospect and Source Triage — 2026-10-06

## Status
Research triage only. This document does not authorize performance testing, holdout selection, ranking for trading, tuning, promotion or live execution.

## Decision frame
Candidates are evaluated on five research dimensions:
1. economic distinctiveness;
2. historical public-observation/PIT feasibility;
3. source quality and coverage;
4. cheap falsifiability and mutation testing;
5. expected information gain per unit of compute.

This is a research-resource priority, not a performance ranking.

## Current active top-4

### 1. Q104:I19 — institutional demand × accrual state
Most mature path toward a formal gate. Exact XBRL concept freeze, dedicated 13F historical identity census, SEC acceptance-time joining and deterministic PIT compiler/mutation tests are in place. Remaining hard gate: historical security-identity/acceptance closure followed by independent reproduction.
Primary risk: the economic object may still contain simpler accounting or institutional-demand explanations. That is a downstream falsification question and not performance evidence.

### 2. Q220 — narrative/structured XBRL representation gap
Strong implementation candidate because the SEC Financial Statement and Notes Data Sets cover January 2009 through August 2026, are as-filed, and contain text, numeric, taxonomy, dimension and presentation structure. Recent XBRL research and SEC analysis make custom-tag and comparability effects economically interesting.
Distinct mechanism: representation mismatch between narrative disclosure and contemporaneous structured facts, not generic length, sentiment or novelty.
Primary risk: taxonomy/schema drift and unstable text-block/presentation mapping. Mapping must be deterministic and fail closed.

### 3. Q218 — mandatory/voluntary disclosure semantic wedge
Strong economic motivation from evidence that Form 8-K event and filing timing creates information-processing and price-discovery dynamics. Candidate object is topic allocation, omission asymmetry and secondary framing across paired disclosure channels.
Primary risk: collapse into generic timing, filing complexity or text similarity. Channel permutation and same-event alignment shuffles are required cheap falsifiers.

### 4. Q221 — government R&D → procurement option-value state
Strong economic mechanism: government R&D awards can carry private value beyond immediate contract revenue and can create an option-like path to future production procurement. The candidate intentionally conditions on competition/agency structure and pre-event capability rather than award size alone.
Primary risk: historical public-observation boundary, entity mapping and agency-specific lag. USAspending documents the standard contract-action path but also a 90-day DoD/USACE exception; the historical applicability of the whole clock must be reconstructed.

## High-value parallel reserve

### Q224 — EDGAR document-demand intensity
Highest novelty among the reserve channels and unusually strong direct literature motivation. EDGAR search activity has been shown to predict future returns/fundamentals and is stronger where information is costly to process and when current and historical filings are accessed together.
Hard blocker: SEC public log data have a gap from July 1, 2017 through May 18, 2020; modern and legacy schemas differ; the SEC warns about missing/damaged files and incomplete traffic. A deterministic traffic-quality/PIT contract is required.

### Q228 — SEC regulatory scrutiny dialogue
Distinct from filing complexity and release latency because the observable object is regulatory interrogation of the issuer disclosure and the resulting response/amendment path. SEC says review is selective, correspondence is publicly released through EDGAR, and current guidance uses UPLOAD for SEC letters and CORRESP for filer responses.
First gate: historical review-cycle linkage, exact public clock, provenance separation, topic taxonomy, amendment/closure lineage.

### Q227/Q231 — SEC FOIA acquisition state
The two current FOIA candidate descriptions are economically near-duplicates: both observe costly information acquisition through SEC FOIA with a latent request clock and a later public-log observation clock.
Decision: consolidate conceptually before spending parallel compute on both. Preserve the two-clock contract, requester taxonomy, public publication boundary and deterministic issuer mapping.

### Q230 — bond-to-equity information-processing gap
A September 2026 paper reports bond-implied signals predicting next-month equity returns in rolling OOS tests, with reported average excess return of 0.54% per month and alpha of 0.65% relative to the Fama-French five factors and momentum.
Hard blocker: free historical TRACE implementation and stable issuer/security mapping must be established before active capacity is allocated. Enhanced historical data may require paid agreements, which are outside project policy.

### Q229 — public consumer-complaint response state
CFPB publishes complaint data freely and generally daily, but only complaints sent to companies for response are eligible and are published after the company responds or after 15 days, whichever comes first. The economically interesting object is response/timing/topic composition, not raw complaint count.
Primary risk: publication selection, company mapping and historical semantics.

## Lower priority / merge candidates
Q217 cognitive-processing friction has strong conceptual support but overlaps materially with Q220 and Q224. Do not promote independently until incremental separability is demonstrated.
Q223 corroboration lag should remain a timing sub-hypothesis under Q204/Q210/Q218 unless source independence creates a genuinely new object.
The supply-chain disclosure-order idea remains a Q207/Q212 sub-hypothesis until it demonstrates separability.
Q202/Q203/Q204/Q205/Q215/Q216/Q222 and Q196/Q199 remain viable but currently carry lower expected information gain per compute because of their historical-source or identity barriers.

## Cross-domain relations worth implementing as infrastructure
`latent process/action -> first public observation -> confirmation/response -> correction/closure` should be a typed event-lineage primitive, not a trading feature.
`information acquisition intensity × processing friction` is a useful nested Q224/Q217 hypothesis, but must remain quarantined until both component contracts survive.

## Rotation rule
Do not replace the active top-4 merely because a reserve has an attractive paper result. Rotation requires a source/PIT gate showing higher expected information gain per unit compute and no dominant historical-clock or identity blocker.
