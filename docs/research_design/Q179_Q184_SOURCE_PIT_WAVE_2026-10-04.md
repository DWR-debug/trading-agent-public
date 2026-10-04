# Q179–Q184 Source/PIT Feasibility Wave — 2026-10-04

## Decision

**Launch parallel discovery wave: YES.**

This wave is intentionally independent of the blocked Q121-R6 execution path. It creates source/PIT feasibility work only. No member is performance-authorized, ranked, tuned or promoted.

## Why this wave is justified

The current Q121-R6 failures are classified as infrastructure rather than scientific falsification: the latest attempted shards reached the compiler and failed with `Q121R6_SHARD_INCOMPLETE`; the frozen 61,818-row population remains unchanged. Therefore waiting for Q121-R6 is not an information-maximizing use of the second research lane.

Lane A remains responsible for Q121-R6 / Q104 formal readiness. This wave occupies Lane B with independent information channels and cheap source/PIT falsification.

## Candidate set

### Q179 — Clinical-trial result/publication state × pharma exposure
ClinicalTrials.gov explicitly distinguishes first submitted, first posted, last update posted, results first submitted and results first posted. The first posted date follows NLM quality-control review and can lag submission, so submission date must not be treated as public availability. citeturn847540search0

**Primary falsifier:** historical first-posted/result-first-posted states cannot be reconstructed without later revisions leaking backward.

### Q180 — Vehicle recall campaign shock × automotive exposure
NHTSA provides historical recall data back to 1949, daily frequency, downloadable flat files, and supports recall searches by publication date. citeturn847540search2

**Primary falsifier:** recall publication/update history cannot be reconstructed consistently enough to establish a frozen decision-time state.

### Q181 — Workplace-safety enforcement shock × industrial exposure
OSHA makes inspection, citation and related safety datasets publicly viewable and downloadable. citeturn847540search1

**Primary falsifier:** public-availability timing or establishment-to-issuer identity cannot be established without retrospective information.

### Q182 — FERC regulatory filing/order state × utility exposure
FERC eLibrary is a free centralized archive containing more than 20 years of issued and received documents; FERC also provides public data APIs, though some Data.FERC.gov endpoints require an API key. citeturn847540search10turn847540search9

**Primary falsifier:** the free archive cannot provide a deterministic issue/receive observation boundary or sufficient historical document completeness.

### Q183 — Transportation incident publication shock × operator exposure
NTSB provides public CAROL investigation data, downloadable aviation accident datasets from 1982 onward, and daily/pending publication reports. citeturn847540search6

**Primary falsifier:** event occurrence time cannot be separated from first public observation time with enough historical precision.

### Q184 — FCC licensing transaction state × communications exposure
FCC ULS provides daily and weekly transaction files and public-domain application/license data. citeturn751655search0turn751655search23

**Primary falsifier:** historical transaction-file publication boundaries or licensee-to-issuer mappings cannot be reconstructed without leakage.

## Admission contract

Every candidate must pass:

1. source reachability and historical archive proof;
2. explicit event/publication/acceptance clock definition;
3. entity identity mapping with fixed provenance;
4. revision/amendment separation;
5. future-event mutation invariance;
6. missing-data fail-closed behavior;
7. deterministic input-order invariance;
8. independent reproduction before any formal candidate-specific PIT step.

No candidate inherits feasibility from another source. No composite signal inherits feasibility from its components.

## Governance

This wave must remain outside performance selection. In particular, no return, holdout, Sharpe, drawdown, profit factor, candidate rank or parameter result may determine admission to the next gate.

The existing universal pre-formal robustness gate remains mandatory before any member can enter a formal research phase.

## Status

`Q179–Q184 = DESIGN_INVENTORY_ONLY`

This wave is source/PIT research, not trading evidence.
