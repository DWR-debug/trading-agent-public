# Q202–Q204 Information-Timing Wave — 2026-10-04

## Purpose

This is a discovery-only extension of the orthogonal information frontier. It translates literature findings about delayed disclosure, financing channels, heterogeneous information-processing speeds and data-vintage contamination into fixed candidate contracts.

No market-return results, ranking, holdout selection, parameter search, threshold search, asset search, promotion or live execution is permitted in this wave.

## Q202 — Clinical-trial reporting deadline breach / missing-result state

### Mechanism

A missing or delayed mandatory clinical-trial result is not merely absence of text. It is a publicly observable information state at a fixed reporting boundary. The literature documents strong time-lag and publication bias: positive findings are more likely to be disseminated and are disseminated faster than null/negative findings.

### Design

For an applicable trial, reconstruct the registry state at the fixed statutory reporting boundary. Exclude valid certification/extension states already public by that boundary. The candidate event occurs at the first reproducible public snapshot showing the deadline miss.

The strategy must never use the later result contents to define the original event. Results, later QC comments, FDAAA violation notices and corrections are separate later states.

### Gate

Historical version snapshots at the deadline, legal applicability/extension lineage, frozen sponsor-to-issuer mapping, and independent PIT reproduction are mandatory.

### Literature

- Showell et al. (2024), *Time to publication for results of clinical trials*, Cochrane Database Syst Rev, PMID 39601300.
- Kim et al. (2017), *The significance of the trial outcome was associated with publication rate and time to publication*, PMID 28238789.
- ClinicalTrials.gov documentation distinguishes first submission, first posting, results submission, results first posted, QC-comment posting and FDAAA 801 violations.

The literature motivates the mechanism; it does not establish equity-return predictability.

## Q203 — Government-demand award × ex-ante financing constraint

### Mechanism

A public procurement award may do more than signal demand. It can relax financing constraints and expand access to credit, creating a second-order transmission channel from government demand to firm capacity.

### Design

Start with the same fixed historical procurement award event as Q197. At the event boundary, join a financing-constraint measure taken only from the latest admissible pre-event public filing. The financing state is frozen before any outcome observation.

No post-award balance-sheet data may enter the event definition.

### Gate

Historical award-state reconstruction, pre-event accounting vintage, frozen recipient/entity mapping, amendment/correction lineage and independent PIT reproduction are mandatory.

### Literature

- Hebous & Zimmermann (2021), *Can government demand stimulate private investment? Evidence from US federal procurement*, Journal of Monetary Economics.
- Gabriel (2024), *The credit channel of public procurement*, Journal of Monetary Economics.
- *What Can 240,000 New Credit Transactions Tell Us About the Impact of NGEU Funds?* (2025, arXiv:2504.01964), whose analysis reports increased new lending after procurement awards and no pre-award anticipatory lending effect in its sample.

This creates a candidate-specific economic channel beyond unconditional procurement exposure. It is not a performance claim.

## Q204 — Public-information release-lag surprise

### Mechanism

The speed at which an event moves from an underlying administrative state to an observable public record can itself contain information about how much lead time the broader market plausibly had. The key state variable is therefore information latency, not event content.

### Design

For a fixed event class and official source, compute the elapsed interval between a fixed underlying administrative date and the first reproducible public-observation timestamp. A rolling pre-event-only latency distribution may provide a fixed surprise score.

Occurrence/action/submission dates are metadata unless their public availability at the same boundary is independently proven.

### Gate

Candidate-specific timestamp completeness, a fixed event-class definition, pre-event-only latency calibration, revision/correction lineage and independent PIT reproduction are mandatory.

### Literature

- *Fast Numbers, Slow Language: Bridging Quantitative and Qualitative Earnings Signals* (2026 preprint, arXiv:2606.29734) documents distinct information-processing speeds within the same earnings event.
- *Buy the Rumor, Sell the News: When Is News Priced In?* (2026 preprint, arXiv:2608.14014) studies how price adjustment concentrates around information arrival and distinguishes pre-publication from publication effects.
- Ahmad (2026), *Time-Series Foundation Models That Understand Data Revisions* (arXiv:2609.28576), explicitly separates observation time from information-availability time and demonstrates that hindsight contamination can materially distort evaluation.

The first two are recent working papers/preprints; they are used as hypothesis-generating evidence, not as established consensus.

## Cross-candidate relation

The three candidates target different stages of the information pipeline:

1. Q202: **absence / delayed mandatory disclosure**.
2. Q203: **economic transmission through financing capacity**.
3. Q204: **speed / latency of public information arrival**.

They should remain separate until each independently clears source/PIT gates. No composite is permitted merely because the mechanisms appear complementary.

## Falsification priority

The cheapest high-value tests are structural:

- Q202: mutate future registry versions and verify the historical deadline-miss prefix is unchanged.
- Q203: inject post-award accounting values and verify the frozen event state rejects them.
- Q204: permute public timestamps inside fixed calendar blocks and verify the latency state changes while the event identity remains fixed.

A failing gate is a successful scientific result: the mechanism is not promoted to formal validation.
