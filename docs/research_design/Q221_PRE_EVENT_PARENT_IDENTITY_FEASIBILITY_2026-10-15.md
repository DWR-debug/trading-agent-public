# Q221 — pre-event parent-identity feasibility audit

**Workpack:** `Q221_PRE_EVENT_PARENT_IDENTITY_FEASIBILITY`  
**Mode:** bounded source-feasibility audit; not a randomized sample, scientific validation, or performance study  
**Frozen transaction boundary:** `research/evidence/q221_historical_public_boundary_latest.json`, receipt `9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4` (348 rows, 247 recipient identities)  
**Current-parent leads:** source run [#38305074104](https://github.com/DWR-debug/trading-agent-public/actions/runs/38305074104), artifact [11772786096](https://github.com/DWR-debug/trading-agent-public/actions/runs/38305074104/artifacts/11772786096), receipt `ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602`.

## Question

For four frozen recipient rows, does a parent's own SEC subsidiary list—filed before the row's transaction date—name the exact child legal entity? A fifth row is a temporal-control case: the current parent label is a later successor-name/merger construct. The audit tests date discipline and source existence only.

The five rows, transaction keys, UEIs, recipient IDs, current parent names/UEIs, filing accessions, filing dates, exact URLs and text markers are frozen in `research/preregistrations/q221_pre_event_parent_identity_feasibility_2026_10_15.json`. Selection is purposeful and informed by public source availability during design, so the results cannot be treated as prevalence estimates.

## Bounded protocol

The workflow may make at most five one-shot HTTPS requests, only to fixed `www.sec.gov` URLs. No automatic retries; 250,000 bytes per response, 1,000,000 bytes total, 30-second timeout, one-second minimum request gap. It checks that each frozen boundary row is still unmapped and that the current-parent artifact and all fingerprints still match.

For the four parent-exhibit cases, the parser requires the exact legal name to appear in the official parent filing and the filing date to precede the frozen transaction date. That creates a **pre-event subsidiary-list observation**, not an authenticated UEI/recipient-ID bridge: SEC exhibit lists are legal-entity statements and do not themselves prove that the contract row's UEI identified that entity on the transaction date.

The fifth source is expressly a post-event control. Raytheon/United Technologies filed that the transaction and successor-name change occurred on 2020-04-03, after the frozen 2020-01-02 row. It may only warn against retrojecting current parent labels; it cannot identify the actual parent as of the transaction date.

## Outcomes and prohibited inferences

A successful run means the fixed documents were fetched under the bounded budget, the four exact subsidiary names were found in pre-event parent filings, the temporal control remained post-event, and x64/ARM64 reproduced the same analysis fingerprint. It does **not** mean any recipient-to-issuer mapping is frozen. The original boundary must remain unchanged; all five rows remain `UNMAPPED_NO_FROZEN_PRE_EVENT_IDENTITY_RECEIPT`.

Historical first-public observation, Q221 historical parent lineage, issuer mapping authority, performance authorization, holdout selection, ranking, tuning, promotion, orders and live execution remain false. If any fixed source is unavailable, malformed, over budget, or date-invalid, the workflow fails closed and preserves the blocked state.

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`; paid API budget USD 0.
