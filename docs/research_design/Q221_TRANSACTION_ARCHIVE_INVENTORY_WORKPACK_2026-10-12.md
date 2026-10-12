# Q221 — Frozen transaction archive-inventory workpack

**Registered:** 2026-10-12 07:25 UTC  
**Stage:** read-only source feasibility; not PIT proof, scientific evidence, or performance authorization.

## Frozen input

This workpack is bound to `research/evidence/q221_historical_public_boundary_latest.json`, Git blob `b78cf6f7b48af3f914ee7c6d06a38f6485b0438f`, receipt fingerprint `9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4`. It contains 348 unique transaction keys across seven fixed fiscal-year partitions: FY2019 (49), FY2020 (50), FY2021 (50), FY2022 (50), FY2023 (50), FY2024 (49), FY2025 (50). Any source change causes the request gate to reject the run instead of silently changing the sample.

## Bounded procedure

The run submits at most seven read-only metadata POST requests to the official USAspending monthly-file catalog (one per frozen target fiscal year, `agency=all`, `type=contracts`). Each request has a 30-second timeout and 5 MB response ceiling. Raw response hashes, content length, catalog rows and the frozen input identities are saved in an uploaded receipt. No contract archive ZIP is downloaded during this phase.

Official interface contract: [monthly files API contract](https://github.com/fedspendingtransparency/usaspending-api/blob/03b9e2554837998c4c261c65e2947dc79f23855a/usaspending_api/api_contracts/contracts/v2/bulk_download/list_monthly_files.md). Implementation inspected: [dated archive listing logic](https://github.com/fedspendingtransparency/usaspending-api/blob/03b9e2554837998c4c261c65e2947dc79f23855a/usaspending_api/download/v2/list_monthly_downloads.py).

## Decision rule

- `DATED_ARCHIVE_SERIES_FOUND`: a separate reviewed workpack may select a small, deterministic subset of the fixed keys and the minimum eligible dated files for row-presence testing.
- `ARCHIVE_LISTING_OK_NO_VERSION_SERIES_FOUND`, `ARCHIVE_LISTING_EMPTY`, `ARCHIVE_LISTING_INCOMPLETE`, or `REQUEST_REJECTED`: stop the route or repair the specific infrastructure/input error; no clock claim is permitted.

A file name or `updated_date` is not evidence of when the file first became publicly downloadable. Presence in a dated archive can at most support a verified *known-available-by-snapshot* bound; absence from a previous archive does not prove absence from the live API/UI. The current API's transaction dates remain distinct from any first-publication time.

## Safety and governance

The request is read-only and paper-only. The 348-key sample and the seven-year allocation are frozen. It does not set `historical_first_public_observation_proven`, `event_level_public_boundary_proven`, `scientific_evidence`, or `performance_authorization` to true. Holdout selection, ranking, tuning, promotion, orders, and live execution remain disabled. The uploaded artifact is the evidence output; the workflow does not auto-commit probe output to the repository.
