# Q221 — Monthly archive catalogue inventory result

**Observed:** 2026-10-13  
**Inventory run:** [GitHub Actions #38436121951](https://github.com/DWR-debug/trading-agent-public/actions/runs/38436121951)  
**Immutable artifact:** [q221-monthly-archive-inventory-38436121951-1](https://github.com/DWR-debug/trading-agent-public/actions/runs/38436121951/artifacts/11832887066)  
**Receipt fingerprint:** `41ac19f87d6c0374f06f5d4375222b0498faeb6c11ca34a4fe439d3d809fd727`  
**Status:** `ARCHIVE_LISTING_OK_NO_VERSION_SERIES_FOUND`

## Frozen population and method

The read-only inventory validates the exact Q221 public-boundary manifest:
- Manifest Git blob SHA-1: `b78cf6f7b48af3f914ee7c6d06a38f6485b0438f`
- Manifest receipt fingerprint: `9e738733d369bf4a954e74cd999c4ba462cf0f9a4fa44aa65c74c637cf3b11f4`
- Population: 348 unique frozen transaction keys across FY2019–FY2025, preserving the registered per-year counts (49, 50, 50, 50, 50, 49, 50).

Exactly seven metadata-only requests were made to the official USAspending monthly archive catalogue; each fiscal-year response parsed successfully. The responses yielded 14 per-year listing entries: one full archive dated 2026-09-06 for each FY and the same all-FY delta archive dated 2026-09-24. No fiscal year exposed a multi-date archive series. **No archive ZIP payload was downloaded.**

## Interpretation and next gate

This falsifies the registered hypothesis that the current catalogue exposes a multi-date full- or delta-archive series for any target FY. It does **not** establish transaction presence/absence at a historical time and does not prove the event-level public-observation boundary.

Stop this catalogue route. Do not download broad archive payloads or infer a public clock from archive names, Action Date, Issued Date, or Last Modified Date. The next source search must identify a different transaction-level timestamped-version source or a separately bounded archive whose row-presence records can be validated. Any verified archive presence would at most bound known availability; absence is not proof of historical non-publication.

The 348-key sample, agency exception checks, recipient-to-issuer mapping, historical first-public-observation gate, and all scientific/performance gates remain unchanged and closed.
