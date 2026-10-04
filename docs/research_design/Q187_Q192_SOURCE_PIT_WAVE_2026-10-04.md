# Q187-Q192 Orthogonal Public-Information Candidate Wave — 2026-10-04

## Purpose

Start the next candidate wave without opening a performance lane. The wave deliberately adds information channels that are operational/regulatory or disclosure-stage based and are structurally different from the tested momentum/residual-momentum families.

## Candidate set

| ID | Mechanism | Primary clock | Main unresolved risk |
|---|---|---|---|
| Q187 | Federal procurement award/action × issuer exposure | USAspending action/publication boundary | recipient mapping + dissemination timing |
| Q188 | FDA safety-labeling change × pharma exposure | FDA supplement/update/publication state | archive/update semantics + issuer mapping |
| Q189 | CPSC consumer-product recall × issuer exposure | CPSC recall publication state | historical public clock + product identity |
| Q190 | EPA enforcement/compliance transition × facility exposure | ECHO refresh/extraction boundary | revision/lag semantics + facility mapping |
| Q191 | Science-publication → patent-publication stage gap | paired public disclosure clocks | patent-paper linkage + exact chronology |
| Q192 | FDA drug-shortage state × manufacturer exposure | FDA daily update/public observation | historical observation clock + manufacturer mapping |

## Why this wave is different

The wave is not another parameterization of OHLCV momentum. Each candidate is driven by an external information clock or a state transition that is economically tied to operations, regulation, supply or innovation.

Q191 is intentionally a stage-timing construction, not:
- the Q176 publication-burst count state; or
- the Q186 patent-citation-network topology.

Q189 is intentionally consumer-product specific and does not reuse Q180's automotive/NHTSA channel.

Q188 and Q192 use FDA but represent distinct information processes: safety-label revision versus product availability/supply state.

## Immediate execution order

1. Run bounded source probes for all six candidates.
2. Record exact source URLs, markers, HTTP status and content fingerprints.
3. Run only synthetic chronology/mutation checks.
4. Reject or quarantine source routes with access, archive or timing defects.
5. For survivors, build candidate-specific PIT contracts and small fixed historical samples.
6. Only a candidate that passes the pre-formal robustness gate can enter formal readiness.

## Scientific prohibitions

This wave must not:
- inspect returns for selection;
- rank candidates by performance;
- select assets or thresholds from observed outcomes;
- tune event windows or parameters;
- access holdout results;
- authorize performance, promotion or live execution.

## Source basis

Current official source documentation supports the existence of these public channels:

- USAspending API documentation states that its API endpoints currently do not require authorization and exposes award/transaction endpoints. The public site displays award ID, modification, recipient, action date and transaction amount fields.
- FDA's SrLC database provides safety-related labeling-change data from January 2016 onward and offers search/download facilities.
- CPSC states that its Recall Data API provides machine-readable public recall information and contains decades of recall information.
- EPA ECHO provides downloadable compliance/enforcement datasets and documents weekly refreshes for downloads; some ECHO views note a longer lag/update schedule, so the candidate must use the exact frozen extraction boundary rather than event dates.
- USPTO public patent-grant/Official Gazette/eGrant resources provide historical patent disclosure boundaries; scientific-publication linkage remains candidate-specific work.
- FDA's Drug Shortages data are updated daily on the public list, and openFDA provides downloadable shortage data; historical first-public observation still has to be reconstructed.

These source facts establish feasibility hypotheses, not scientific evidence.

## Acceptance criterion for the source-feasibility wave

A source is considered probe-passed only when a public endpoint/page returns HTTP 200 and all candidate-specific required markers are present. A 401/403, marker mismatch or other fetch failure is recorded explicitly rather than silently bypassed.

No source result authorizes any candidate for performance.
