# Q221 bounded recipient-parent identity feasibility probe — preregistration

Registered 2026-10-12 19:50 UTC. This is an auxiliary identity-source probe, not a replacement for the blocked historical public-observation gate.

## Frozen source and sample

Source: research/evidence/q221_historical_public_boundary_latest.json, Git blob SHA-1 b78cf6f7b48af3f914ee7c6d06a38f6485b0438f, receipt fingerprint 9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4. Seven recipient IDs are frozen from one distinct recipient per existing calendar-window sample, selected deterministically as the first transaction in each window whose recipient ID has not already been selected. The exact transaction keys, recipient IDs, UEIs, and windows are embedded in automation/q221_recipient_parent_identity_probe.py and validated against the source receipt before any HTTP request.

## Source and question

Official USAspending recipient-profile contract: https://github.com/fedspendingtransparency/usaspending-api/blob/master/usaspending_api/api_contracts/contracts/v2/recipient/recipient_id.md

The documented response can expose current recipient UEI, parent ID, parent UEI, parent name, and recipient level. The probe asks whether the public endpoint returns consistent parent-identity fields for each frozen recipient under two queries: year=all and the corresponding fiscal-year query for the frozen sample.

## Bounds

- Exactly 14 GET requests: two per recipient, no retries and no additional endpoint discovery.
- Each response capped at 1,000,000 bytes; total response-body budget 14,000,000 bytes; 30-second timeout and at least one second between requests.
- Exact recipient ID and UEI are checked against the frozen transaction sample.
- Parent metadata equality between year queries is recorded only as query consistency. It does not establish historical parent lineage, historical issuer identity, or public-observation time.
- No mapping is inferred from names. No source receipt or candidate gate is modified. No performance, holdout, ranking, tuning, promotion, orders, or live execution.
