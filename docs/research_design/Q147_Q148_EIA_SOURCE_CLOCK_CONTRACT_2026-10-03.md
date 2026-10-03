# Q147/Q148 EIA Source Clock Contract — 2026-10-03

## Purpose

This is a PIT/data-source contract only for Q147 and Q148. It does not evaluate returns, rank the two candidates, select assets, tune parameters, select a holdout, authorize performance, promote or trade.

## Q147 — electricity-load / industrial exposure

The current EIA APIv2 is a continuously updated public database interface. Its current API documentation explicitly states that APIv2 has no update field and that public-facing databases are updated constantly rather than at regular intervals.

Therefore the current API is not accepted as the sole historical PIT source for a formal Q147 study.

The admissible historical clock is the dated publication/release record of a fixed EIA electricity product. The candidate-specific series, publication product, and historical release files must be frozen before any formal PIT compiler is accepted.

Required fields:
- observation period;
- product/release identity;
- release date/time;
- downloaded file fingerprint;
- correction/revision notice identity when present;
- fixed industry/issuer exposure mapping.

## Q148 — petroleum inventory shock / sector sensitivity

For Q148 the preferred historical backbone is the Weekly Petroleum Status Report issue archive rather than the continuously updated API.

The WPSR publishes dated issues and states its normal release timing. Holiday weeks have explicit alternate release dates/times. EIA also publishes revision/correction notices, demonstrating that later corrections can occur and therefore must be represented explicitly in a PIT lineage.

The candidate-specific series, table number, issue-date mapping and revision policy must be frozen before a formal PIT compiler is accepted.

Required fields:
- week-ending date;
- release date/time;
- issue identifier/page identity;
- table/file fingerprint;
- revision/correction lineage;
- fixed sector sensitivity mapping.

## Conservative classification

Q147: PIT_CONTRACT_DEFINED_PENDING_SERIES_FREEZE

Q148: PIT_CONTRACT_DEFINED_PENDING_SERIES_FREEZE

These classifications are strictly upstream of performance evidence.

## References

- https://www.eia.gov/opendata/faqs.php
- https://www.eia.gov/electricity/data.php
- https://www.eia.gov/petroleum/supply/weekly/
- https://www.eia.gov/petroleum/supply/weekly/schedule.php
- https://www.eia.gov/petroleum/supply/weekly/includes/revision-notice.php