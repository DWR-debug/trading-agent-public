# Q221 — DoD agency 097 Wayback archive schema and row-presence probe

**Status:** one-shot preregistered source feasibility only. This is not an award-publication clock, historical PIT proof, issuer mapping, scientific result, or performance authorization.

## Discovery and selection

The frozen Q221 receipt contains 348 transaction keys across FY2019–FY2025. Its FY2025 partition includes 28 Department of Defense transactions marked as DoD 90-day-exception candidates. The exact keys are derived from the pinned manifest at runtime, not manually selected after archive inspection.

The prior monthly-catalogue inventory did not expose a dated historical series. A separate Wayback CDX prefix inspection returned 20 URL entries matching 097 contract archives: 19 fiscal-year full archives and one all-FY delta archive. The observed filenames used stamp 20250106 and the captures were dated 2025-01-28. That discovery query collapsed by URL key, so it is URL-coverage metadata, not a complete capture timeline. The FY2025 full archive is 13,605,284 bytes in CDX metadata; larger full-file captures were excluded.

The live USAspending archive directory had a newer 20261006 filename stamp when checked on 2026-10-15. That live listing is current-state metadata, not a historical version of the FY2025 file. This probe replays only the exact 2025-01-28 Wayback capture of the 2025-01-06-named FY2025 DoD full archive.

## Frozen source pins

- Manifest Git blob SHA-1: b78cf6f7b48af3f914ee7c6d06a38f6485b0438f
- Manifest receipt fingerprint: 9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4
- Original archive URL: https://files.usaspending.gov/award_data_archive/FY2025_097_Contracts_Full_20250106.zip
- Pinned Wayback capture: 20250128184322 (2025-01-28 18:43:22 UTC)
- CDX SHA-1/Base32: IYPLEC2VXYNMEA2CUHSSPVKPEJRKBJQB
- CDX archive length: 13,605,284 bytes

## Procedure and hard caps

The one-shot master-only workflow checks Actions run history to prevent re-use of the source request. It validates the frozen manifest and preregistration before network access, then makes at most two GET requests, both to web.archive.org: one bounded CDX inventory and one exact replay. Redirects are not followed. The CDX result is capped at 100 records and 5 MB; replay at 20 MB; total received bytes at 25 MB. ZIP limits are 512 members, 250 MB expanded content, 128 CSVs and two million rows. A cap breach fails closed.

The archive is inspected in memory only. The workflow uploads a JSON receipt, never the archive bytes. Matching uses the frozen PIID, modification, action date and recipient UEI composite. The composite must be unique in the frozen target set, and where an awarding-agency-code column exists, a matched row must show code 097.

## Interpretation rules

A unique match means only that the frozen composite is present in this exact file as observed at the pinned Wayback capture timestamp: a known-available-by-snapshot bound, not the first-public time. A no-match means only that the row was not found in this exact snapshot, not historical absence from USAspending.gov, the live API, or another channel. The filename date is not first-public time.

The file was selected by pinned archive identity/size and overlap with the pre-existing frozen FY2025 sample, before row inspection. No shared delta, larger yearly ZIP, live API, SAM.gov API, or extra transaction keys are queried.

## Gates and safety

This cannot clear Q221 historical first-public-observation or event-level PIT gates, freeze recipient-to-issuer identities, prove transaction-class applicability, or establish scientific evidence. Performance authorization, holdout selection, ranking, tuning, promotion, orders and live execution stay disabled. No census restart or change to the frozen population is permitted.
