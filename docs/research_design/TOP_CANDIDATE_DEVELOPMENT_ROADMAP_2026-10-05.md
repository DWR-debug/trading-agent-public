# Top Candidate Development Roadmap — 2026-10-05

## Purpose

This roadmap converts the current research frontier into a bounded development sequence toward the earliest scientifically admissible one-shot Performance Run.

It is a **readiness roadmap, not a return forecast**. No candidate is ranked by observed returns here. Ordering uses only mechanism distinctness, source/PIT maturity, reproducibility, expected falsification value, implementation complexity, and proximity to a complete authorization chain.

The project remains:

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `ORDERS_ENABLED=False`
- `AUTOMATIC_PROMOTION=False`

No performance run is implied by design/source readiness alone.

## Current decision

### Near-term performance frontier

**P0 — Q104:I19 exact-XBRL × institutional-transition state**

Why first:
- Q104 source feasibility and downstream gates are already recorded complete.
- Q105 historical PIT feasibility is complete.
- Q106 PIT join structural validation is complete.
- Q107 fresh-equity coverage is complete.
- Q108 PIT integration is complete on a fixed symbol-disjoint universe.
- I19 is a frozen three-concept accounting state joined to the deterministic Q114 13F transition compiler.
- Remaining work is therefore predominantly historical 13F/security completeness, candidate-specific PIT compilation, independent reproduction, preregistration reconciliation and authorization.

This is the fastest route to an admissible Performance Run **provided the remaining gates pass without repair or redesign**.

### High-value orthogonal frontier

**P1 — Q220 narrative–structured/XBRL representation gap**

Mechanism: disagreement/corroboration between narrative disclosure change and contemporaneous structured XBRL change. This is materially different from document length, generic novelty and simple filing sentiment. The SEC's current API documentation confirms continuous dissemination of submissions/XBRL data and distinguishes standard taxonomy facts from custom extensions. citeturn948019search4

Primary bottleneck: synchronized historical narrative/XBRL reconstruction, deterministic text-block/presentation mapping, amendment lineage and independent PIT.

**P1 — Q228 SEC filing-review dialogue / disclosure-scrutiny state**

Mechanism: publicly observable SEC-originated comment letters and filer responses expose a regulatory scrutiny process around issuer disclosure. The SEC confirms public correspondence in EDGAR from 2005 onward, UPLOAD/CORRESP form distinctions, multiple review/response rounds, and a minimum 20-business-day public-release rule after completion/effectiveness. citeturn948019search1turn948019search5turn948019search7

Primary bottleneck: deterministic review-cycle linkage and first-public-observation clock. The selective nature of SEC review is a mandatory selection limitation; no model may infer the latent review-selection process from post-event outcomes.

**P1 — Q224 EDGAR document-demand / acquisition shock**

Mechanism: post-publication demand for a specific filing/asset as observed in SEC EDGAR server logs. The SEC's modern log schema contains an explicit timestamp and URI path from which CIK/accession can be deterministically recovered. The current official archive separates the modern 2020–2025 dataset from the older 2003–2017 dataset and documents the 2017–2020 gap. citeturn948019search2turn948019search44

Primary bottleneck: large-file ingestion, completeness/mutation audit, traffic automation contamination and strict prohibition on silently splicing incompatible log schemas.

## Secondary frontier

**P2 — Q227 SEC FOIA information-acquisition state**

Potentially strong because the observable object is a discretionary regulator-facing information request rather than ordinary EDGAR access. The SEC currently publishes FOIA logs monthly through August 2026. citeturn948019search0

Primary bottleneck: reconstructing the historical public-observation batches and deterministic issuer/topic/requester mapping. The private request date must never be used as a public trading clock.

**P2 — Q221 government R&D → procurement-option-value state**

Interesting cross-domain mechanism because competitive structure, agency/PSC state and pre-event capability are part of the information object rather than award size alone. Main bottleneck is the historical public-observation clock and frozen recipient-to-issuer mapping.

**P2 — Q218 mandatory–voluntary disclosure semantic wedge**

Potentially distinct, but text-channel classification and strict channel/event pairing are heavier than Q104:I19 and less mechanically mature than Q220.

**P2 — Q219 filing-change × options-response processing wedge**

Potentially strong as an information-processing differential, but option-contract/calendar stability and end-of-day observation timing create a materially larger PIT burden.

## Explicitly not promoted to the active four

Q226 remains a nested Q224 subcandidate until historical-vs-current acquisition composition proves incremental information beyond total acquisition intensity.

Q222 remains nested under the disclosure-verification family until the external implementation clock is shown to be historically reconstructable.

Q217 remains subordinate to Q131 and is merge/kill constrained if filing complexity fully explains it.

Q118 composite/consensus structures remain deferred until the underlying components independently survive source/PIT and robustness gates. This prevents the project from constructing a composite because it looks promising in advance.

## Common gate sequence to Performance

Every candidate follows the same scientific chain:

`G0 structural robustness`
→ `G1 source feasibility + source coverage`
→ `G2 historical PIT / mutation / lineage`
→ `G3 independent reproduction`
→ `G4 frozen preregistration + immutable authorization reconcile`
→ `G5 one-shot Performance Run`
→ `G6 Trial Ledger + gate interpretation`

No return-based ranking, holdout selection, parameter search, threshold search or horizon search occurs before the authorized Performance boundary.

## Timeline from 2026-10-05 23:15 CEST

These are **engineering/research duration estimates**, not promises of success. A failed gate shortens the path by killing/merging the candidate; a queue outage or required source repair lengthens calendar time.

| Candidate | Remaining work estimate | Earliest plausible Performance Run | Main uncertainty |
|---|---:|---:|---|
| **Q104:I19** | ~2–5 h | **2026-10-06 ~01:30–04:30 CEST** | 13F/security completeness; independent PIT; final authorization |
| **Q220** | ~6–14 h | **2026-10-06 ~07:30–17:00 CEST** | historical narrative/XBRL synchronization and deterministic mapping |
| **Q228** | ~8–18 h | **2026-10-06 ~09:30–23:30 CEST** | review-cycle linkage + public-release clock + selection controls |
| **Q224** | ~10–20 h | **2026-10-06 ~11:30–2026-10-07 ~07:30 CEST** | archive scale, log integrity, traffic artifacts |
| **Q227** | ~12–24 h | **2026-10-06 ~15:30–2026-10-07 ~15:30 CEST** | public-batch chronology + target/topic mapping |
| **Q221** | ~12–24 h | **2026-10-06 ~15:30–2026-10-07 ~15:30 CEST** | transaction-publication clock + entity mapping |
| **Q218** | ~10–20 h | **2026-10-06 ~11:30–2026-10-07 ~07:30 CEST** | deterministic channel taxonomy |
| **Q219** | ~16–30 h | **2026-10-06 ~15:30–2026-10-07 ~05:30 CEST** | options PIT/calendar integrity |

The earliest defensible Performance opportunity is therefore **Q104:I19**, not because it is expected to outperform, but because its scientific prerequisites are currently closest to complete.

## Parallel allocation

### Lane A — Formal Readiness

1. Complete Q104:I19 remaining historical/security PIT work.
2. Independent reproduce the exact frozen I19 contract.
3. Freeze preregistration and request the single immutable Performance authorization only after the independent result reconciles.

### Lane B — Frontier Discovery

1. Q228: compile the historical correspondence population and provenance split.
2. Q220: build the narrative/XBRL synchronized source census and mapping audit.
3. Q224: perform the modern EDGAR-log archive census, integrity and accession-decoding gate.
4. Q227: reconstruct FOIA public-observation batches and requester/target taxonomy feasibility.

These four should remain independent. A failure in one line does not alter another line's frozen contract.

### Auxiliary capacity

- Windows self-hosted slots: deterministic local reproduction, archival parsing, source QA and long-running compilers.
- GitHub-hosted x64: canonical deterministic source/PIT jobs.
- Hosted ARM64: independent governance/reproduction and non-authorizing cross-checks.
- Free AI pool: bounded adversarial review of contracts, taxonomy, provenance and failure modes only.
- S10: mechanical QA/support only; never scientific authority.
- No resource is assigned filler work. A free resource receives the next genuinely useful bounded task, otherwise remains idle.

## Abort / merge policy

The project should prefer a clean negative result over a rescued candidate.

Immediate merge/kill examples:
- Q220 collapses to filing complexity or non-reproducible XBRL mapping.
- Q228 collapses to complexity, enforcement or release latency.
- Q224 collapses to generic attention or unbounded bot traffic.
- Q227 collapses to Q224 / generic attention after public-clock controls.
- Q218 collapses to document size/complexity or channel-label artifacts.
- Q219 collapses to options-only or text-only effects.

No parameterization should be added after a candidate fails one of these tests.

## External evidence used for prioritization

The prioritization is consistent with the current public source landscape:

- SEC EDGAR modern logs expose request timestamps and filing-identifying URI paths. citeturn948019search2turn948019search44
- EDGAR correspondence is publicly released in EDGAR, with UPLOAD/CORRESP provenance and a defined minimum release delay. citeturn948019search1turn948019search7
- SEC FOIA logs currently run from January 2006 through August 2026. citeturn948019search0
- SEC's XBRL APIs disseminate filing/XBRL data in real time and provide bulk archives, supporting a deterministic source layer for Q220. citeturn948019search4
- Academic literature reports return predictability associated with EDGAR acquisition activity, but this literature is mechanism motivation only and does not constitute project evidence. 

## Governance

This roadmap changes no performance authorization and no execution setting. The only permitted conclusion at this stage is **development readiness**.
