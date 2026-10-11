# Research OS Evidence Bus — schema v2 clock provenance

**Date:** 2026-10-11  
**Status:** implemented as an opt-in receipt schema; no existing v1 receipt is rewritten.  
**Authority:** operational provenance only. A receipt is not scientific evidence or performance authorization.

## Why this change exists

The v1 Evidence Bus requires timestamp fields to be present, but allows `available_at: null` without an explicit clock explanation. It also checked that the receipt fingerprint *looked like* a SHA-256 digest without recomputing it from the receipt payload. These are separate defects:

- A time value can be syntactically valid and still represent event/action time, an agency processing time, retrieval time, or a later bulk refresh rather than first public availability.
- A 64-character hash can be well-formed but stale if receipt contents change after the hash is computed.

## Digest integrity

For every schema version, `validate_receipt` now recomputes the canonical fingerprint over the complete receipt after removing only `receipt_fingerprint`. A mismatch fails closed. Raw and normalized fingerprints, optional revision-parent fingerprints, and the receipt fingerprint are also required to be 64-character SHA-256 hex strings.

The existing v1 shape and fingerprint construction remain unchanged. Existing receipts are not bulk-rewritten or retroactively augmented. Validation retains the field-specific checks before the digest check so callers still receive useful errors such as source URL drift or a future availability timestamp.

## V2 fields and rules

V2 adds four explicit fields:

| Field | Meaning |
|---|---|
| `availability_basis` | One of `SOURCE_TIMESTAMP`, `OFFICIAL_RELEASE_TIMESTAMP`, `VERSIONED_SNAPSHOT_FIRST_OBSERVED`, `CONSERVATIVE_NEXT_SESSION`, or `UNKNOWN`. |
| `availability_evidence_url` | HTTPS source/documentation URL supporting a non-null public-availability claim. |
| `vintage_id` | Optional exact release, archive, or source-version identifier. |
| `revision_parent_fingerprint` | Optional SHA-256 fingerprint linking a correction/amendment to the version it supersedes. |

When `available_at` is non-null, v2 rejects `UNKNOWN` and requires an HTTPS `availability_evidence_url`. When `available_at` is null, the basis must explicitly be `UNKNOWN` and the evidence URL must be null. This intentionally does not invent an availability time for source probes, event dates, action dates, retrieval times, current listings, or undocumented historical versions.

V1 callers remain on v1 by default. V2 is opt-in through `build_receipt(schema_version=2, ...)`. Supplying v2-only fields while requesting v1 raises rather than silently discarding provenance.

## Rollout order

1. Keep current source-probe receipts on v1 unless they can supply a defensible historical public-availability basis.
2. Inventory a candidate-specific source's clock contract and revision/vintage semantics before emitting a v2 receipt with non-null `available_at`.
3. Use the source owner/documentation as `availability_evidence_url`; identify an exact version when one exists and parent the record when a correction supersedes it.
4. Preserve `UNKNOWN` as unknown. Do not infer availability from occurrence/action date or from the time this agent downloaded a page.
5. Do not mutate old receipts or silently convert them to v2. A future migration would need its own manifest, hashes, validation and explicit source evidence.

## Validation coverage

The Evidence Bus test suite now covers v1 compatibility, receipt-payload mutation with a stale but correctly shaped digest, valid v2 provenance, rejection of a claimed availability without its evidence URL, and explicit unknown availability. All operational receipts remain `scientific_evidence=False`, `performance_authorization=False`, and `holdout_used=False`.
