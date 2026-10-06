# Q232 — EPA/ECHO Regulatory Escalation State

**Date:** 2026-10-06  
**Issue:** #1106  
**Status:** DISCOVERY / SOURCE-PIT FEASIBILITY ONLY

## Economic mechanism

Q232 tests whether transitions through an environmental regulatory state machine contain incremental information about an issuer's operational and legal exposure. The focus is on regulator-implied **state escalation** rather than a generic ESG score or raw violation count:

inspection/evaluation -> violation/noncompliance -> significant noncompliance -> enforcement -> settlement/remediation

A cross-program escalation (for example, air + water + hazardous-waste records affecting the same facility/parent) is potentially more informative than an isolated event because it reflects broader regulatory exposure.

## Candidate information state

- inspection/evaluation intensity and recency
- severity / significant-noncompliance transition
- enforcement stage and action type
- penalty or relief magnitude when already public and fixed
- cross-program escalation
- repeat-offender / unresolved-case state
- facility-to-parent aggregation through FRS

No direction is assumed ex ante.

## Public-information clock

EPA's ECHO data are normally refreshed weekly. That is **not** proof of an exact market-observable timestamp. The formal clock must therefore come from an immutable historical release/snapshot chronology; absent such a clock, the candidate must use the next regular trading-session boundary. The violation/enforcement date itself must never be substituted for public observability.

## Source/PIT gates

1. Historical ECHO / ICIS-FE&C archive and download completeness.
2. Reconstructable public refresh/publication chronology.
3. Frozen FRS facility/program/parent relation map; ownership/name changes must not rewrite the historical prefix.
4. Correction/re-reporting lineage for violation and enforcement records.
5. Independent PIT reconstruction on symbol-disjoint issuers.

## Cheap falsification ladder

First test whether the stage representation is mechanically reproducible. Then ask whether it adds anything beyond firm size, industry, prior regulatory exposure and already-public issuer disclosure. Any useful historical state must survive correction/re-reporting mutation tests and an independent entity mapping.

## Primary sources

- https://echo.epa.gov/tools/data-downloads
- https://echo.epa.gov/resources/echo-data/about-the-data
- https://echo.epa.gov/tools/data-downloads/frs-download-summary

## External economic evidence

A 2026 Accounting & Finance study finds EPA enforcement actions are followed by changes in nearby property values, and a 2026 Finance Research Letters study links facility-level environmental violations to subsequent changes in corporate leverage. These support the economic channel but do not constitute Trading Agent project performance evidence.

- https://doi.org/10.1111/acfi.70222
- https://doi.org/10.1016/j.frl.2026.110601

## Boundary

Discovery only. No performance, holdout selection, ranking, parameter/threshold/horizon tuning, promotion or live execution.
