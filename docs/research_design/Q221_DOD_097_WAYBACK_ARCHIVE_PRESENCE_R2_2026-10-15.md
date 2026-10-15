# Q221 DoD 097 Wayback archive row-presence probe — recovery R2

**State:** separately preregistered recovery proposal. It is not an archive result, a PIT/publication-clock result, or gate clearance.

## Why a new attempt is needed

The first run [#38791554425](https://github.com/DWR-debug/trading-agent-public/actions/runs/38791554425) validated its frozen inputs and completed its offline checks, but failed during receipt serialization with `NameError: _fingerprint is not defined`. Its end receipt and artifact were absent. The persisted audit therefore labels both the exact source-request count and archive outcome **unknown**. Neither row presence nor row absence can be inferred from that attempt.

The writer fix and canonical fingerprint regression test are on current `master` in commit `eef749f120e99cd568915bca02d8df89b7743cc0`. This R2 is a distinct preregistration, marker, workflow and attempt number. It does not re-use or rewrite the consumed R1 marker.

## Frozen scope — unchanged

- Source manifest Git blob SHA-1: `b78cf6f7b48af3f914ee7c6d06a38f6485b0438f`; receipt fingerprint: `9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4`.
- Exact archive: `FY2025_097_Contracts_Full_20250106.zip`; Wayback capture `20250128184322` (2025-01-28 18:43:22 UTC).
- Expected archive identity: CDX SHA-1/Base32 `IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB`, length `13,605,284` bytes.
- Fixed 28 FY2025 DoD exception-candidate transaction keys derived at runtime from the frozen 348-key manifest. No additions, removals, ranking, census restart or live USAspending API calls.
- Same hard bounds: at most two GET requests, both to `web.archive.org`; 5 MB CDX response, 20 MB archive response, 25 MB combined response, 250 MB expanded ZIP, 512 ZIP members, 128 CSVs and 2,000,000 rows. No redirects; archive bytes stay in memory; only a JSON receipt is uploaded. The dedicated R2 receipt-sync workflow validates the canonical fingerprint and safety boundary, then persists both an immutable run-specific receipt and a latest pointer.

## Interpretation and hard gates

A unique key match establishes only presence in this exact snapshot as captured at the pinned timestamp, not the transaction's first-public time. A no-match applies only to this archive snapshot, not historical absence from every public channel. A transport, schema, digest, cap or receipt failure remains unknown/blocked and is not recoded as absence.

This is source feasibility only. Historical first-public observation, event-level PIT, transaction-class applicability, pre-event recipient-to-issuer mapping, scientific evidence, performance authorization, holdout selection, ranking, tuning, promotion and live execution remain false. R2 is one-shot; any further acquisition after an R2 failure requires another independently reviewed preregistration and a new marker.
