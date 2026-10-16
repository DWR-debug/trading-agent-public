# Q221 — SAM.gov Contract Awards API public-delta feasibility adjudication R1

**Review date:** 2026-10-16  
**Disposition:** `DOCUMENTATION_ONLY_LEAD_NOT_GATE_EVIDENCE`  
**Scope:** Official documentation review only. No contract-award API call, credential test, data request, historical archive query, or modification of frozen evidence was performed.

## Decision

The SAM.gov Contract Awards API is a plausible *conditional source-discovery lead* for future Q221 work because its documented query surface includes `publicDeltaDate` and its response schema exposes transaction metadata. The reviewed documentation does **not** establish that these fields provide a reproducible first-public-observation timestamp for a particular transaction, or that a request can replay all prior public versions of that transaction.

Accordingly, this review does not qualify the API as an admissible historical public-clock source and does not clear any Q221 gate. Do not dispatch an API experiment unless valid API access is already available through an approved secret/credential path and a separate bounded preregistration has been reviewed.

## Official documentation findings

### 1. Access is conditional

The official [GSA Open Technology documentation for the SAM.gov Contract Awards API](https://open.gsa.gov/api/contract-awards/) marks `api_key` as required and describes access as dependent on the account/system account. It also distinguishes revealed from unrevealed contract data, including a 90-day disclosure boundary for certain DoD awards. Personal-key rate limits vary by account type/role.

No API key is assumed to exist in this project. No credential was requested, inspected, printed, or tested. In particular, this memo does not authorize workarounds for access restrictions or reveal-gated data.

### 2. A public-delta filter is not a first-public timestamp

The same documentation defines `publicDeltaDate` as returning contracts based on their **Last Modified Date or Reveal Date**. The documentation also lists `createdDate`, `lastModifiedDate`, and transaction response fields `transactionData.createdDate`, `transactionData.lastModifiedDate`, `transactionData.approvedDate`, `transactionData.version`, and `coreData.coreVersionId`.

These names and filters are useful metadata, but they do not by themselves prove the earliest time a specific award action was publicly observable. A query parameter selecting by modification/reveal date does not equal a stored event-time field, and the reviewed documentation does not define `transactionData.createdDate` as the first-public timestamp.

The examples also show why these clocks must stay distinct: one example reports transaction `createdDate` in 2015 and `lastModifiedDate` in 2025. That can evidence a long gap between two recorded metadata fields; it does not, by itself, establish when each field or the relevant action first became publicly accessible.

The `documentVersion` parameter is documented as a text filter, with an example value such as `1.5`. The reviewed documentation does not establish that this parameter retrieves an archived prior public snapshot or enumerates a transaction's full version history. The presence of a version label is not proof of historical replay semantics.

### 3. USAspending pipeline timing is useful context, not transaction-level proof

The official [USAspending Data Sources guide](https://www.usaspending.gov/data/data-sources-download.pdf) says that USAspending data refresh daily after a nightly pipeline while source systems have different update requirements. For FPDS contract data, it describes submission within three days, subsequent availability to USAspending, and publication on the following day; its example maps a Thursday action to Tuesday reporting, Wednesday availability, and Thursday publication. It separately documents a 90-day delay to the FPDS source system for DoD and USACE award data.

Those are documented system-level rules/examples, not a timestamped historical record of when any one of Q221's sampled transactions first appeared in public data. They cannot be used to calculate or impute a transaction's exact first-public time. The [FAR contract-reporting rules](https://www.acquisition.gov/far/subpart-4.6) similarly establish reporting obligations, not a complete public-version archive.

## Q221 relevance and limits

The frozen Q221 public-boundary sample remains 348 transaction rows. Existing evidence does not establish first-public-observation time for any of the 348 rows, and the 247 recipient identity candidates remain unmapped to issuers under the frozen pre-event identity contract. The previous four-key FPDS public-Atom probe returned HTTP 302 for all four requests and, under its no-redirect contract, correctly followed none of them. That negative result does not prove that all possible contract-award data sources are unavailable.

This documentation review is a distinct discovery result only. It made no API request and does not amend the failed FPDS route, the 348-row sample, transaction keys, agency-specific timing rules, recipient identity mappings, frozen source receipts, or any research gate.

## Conditions for a possible next test

A future source probe is eligible only after all of the following are satisfied:

1. An approved SAM.gov API key is already available through a protected workflow-secret mechanism. Its value must not enter logs, artifacts, receipts, PR text, or generated status. If access is not available, stop without requests.
2. A separate preregistration freezes at most four exact existing transaction keys and distinguishes PIID, modification number, transaction number, action date, created date, approved date, last-modified date, reveal date, and any returned version identifiers. It specifies one-shot request limits, response-size limits, no retries unless separately authorized, and offline receipt validation.
3. The test checks whether the API exposes a retrievable prior-version/public snapshot for those exact actions, not merely a current record with timestamps. A field can be labelled first-public only if its semantics are documented and independently supported by timestamped historical/public-version evidence.
4. The result is fail-closed if current metadata cannot demonstrate the historical public boundary. No broad query across the 348 rows is authorized by this memo, and no absent timestamp may be inferred from the action, signature, creation, approval, last-modified, or reveal date.

## Non-authorization record

- `source_requests_made = 0`
- `sam_api_requests_made = 0`
- `historical_snapshots_retrieved = 0`
- `frozen_transaction_rows_modified = 0`
- `recipient_identity_mappings_added = 0`
- `historical_public_clock_gate_cleared = false`
- `performance_authorization = false`
- `holdout_selection = false`
- `ranking = false`
- `tuning = false`
- `promotion = false`
- `live_execution = false`

**Conclusion:** preserve SAM.gov Contract Awards as a conditional lead, not yet a dispatch-ready source contract. Q221 remains blocked on record-level historical publication time and pre-event recipient-to-issuer identity; Paper-Only and all existing research gates remain unchanged.
