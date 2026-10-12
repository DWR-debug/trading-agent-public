# Q221 current parent identity lead map — preregistration

Registered 2026-10-12 20:25 UTC after the bounded seven-recipient feasibility probe completed successfully.

## Frozen inputs

- Historical/public-boundary source receipt: research/evidence/q221_historical_public_boundary_latest.json; Git blob SHA-1 b78cf6f7b48af3f914ee7c6d06a38f6485b0438f; receipt fingerprint 9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4.
- Feasibility run #38303469112; receipt fingerprint d4f5819f51849d7ba037ec0fa610f5e6e47b74b9353a0c534b6e2e666842509e. Its seven recipients had exact recipient ID/UEI matches and parent metadata consistent between year=all and year-specific queries. It did not prove historical parent lineage.
- Fixed population: all 247 recipient_identity_candidates from the frozen source receipt, ordered by recipient_id. No sampling, name matching, or candidate substitution.

## Method and bounds

- One GET per frozen recipient to the official USAspending recipient-profile endpoint, with year=all.
- Exactly 247 requests; 100,000-byte response cap; 25,000,000-byte aggregate response budget; 30-second timeout; at least one second between requests; no retries.
- Verify exact recipient_id and UEI against the frozen source receipt.
- Record parent_id, parent_uei, parent_name and recipient_level as current-state metadata only. Classify non-self parent UEI values as leads, not mappings.
- The output must preserve all 247 rows, including failures, and must not promote any recipient to an issuer. Current parent relations do not prove transaction-date parent identity.

## Decision boundary

This lead map can prioritize independent pre-event identity research. It cannot clear the 247/247 historical recipient-to-issuer gate, establish the 2019–2025 public-observation clock, or authorize performance, ranking, tuning, promotion, orders, or live execution.
