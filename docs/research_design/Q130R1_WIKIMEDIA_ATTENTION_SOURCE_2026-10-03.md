# Q130-R1 — Wikimedia Pageviews Historical Attention Source Feasibility

## Status

SOURCE / PIT FEASIBILITY ONLY. No performance authorization.

## Objective

Test whether the public Wikimedia Pageviews stream can provide a reproducible historical attention proxy for a fixed equity universe.

Wikimedia documents that the current pageview definition is available from May 2015 and that public pageview data are available at daily and hourly granularity. The data stream is public and includes per-article counts.

## Fixed universe

Q107 frozen issuers:

- SPGI — S&P Global
- NDAQ — Nasdaq
- AMP — Ameriprise Financial
- RJF — Raymond James
- WMB — Williams Companies
- VLO — Valero Energy
- DVN — Devon Energy
- EMN — Eastman Chemical

The article-title mapping is frozen for this source-feasibility experiment. A future formal study must use an ex-ante immutable entity/page map.

## Fixed source contract

Primary source:

https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/user/{ARTICLE}/daily/{START}/{END}

Fixed feasibility window:

2025-09-20 through 2025-09-24.

For each fixed article, preserve:

- exact request URL;
- raw response SHA-256;
- returned timestamp/date rows;
- pageview counts;
- missing or zero-data states.

## PIT boundary

The historical Pageviews value is an aggregated observation for the stated day, not proof of the first moment that the final value became publicly available.

Therefore this experiment may establish:

- historical source availability;
- daily-granularity semantics;
- deterministic entity/page mapping;
- response reproducibility/fingerprinting.

It does not establish an exact historical publication clock or revision lineage. Same-day formal PIT remains blocked until a separate publication/revision contract is established.

## Mutation / robustness requirements

- article input order must not change compiled output;
- future dates must not change earlier output;
- malformed API payloads fail closed;
- negative/non-numeric view counts fail closed;
- missing article results are explicit rather than silently substituted.

## Scientific boundary

No returns, holdout use, ranking, selection, tuning, promotion, performance authorization or live execution.
