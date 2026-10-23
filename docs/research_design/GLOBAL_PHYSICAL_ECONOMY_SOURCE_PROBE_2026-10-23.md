# Global Physical Economy Graph — bounded source/PIT probe

**State:** discovery quarantine; no candidate dispatch; not performance-authorizing.  
**Related decision:** https://github.com/DWR-debug/trading-agent-public/issues/1514

## Question

Can a fixed, small sample from IMF PortWatch and Copernicus Sentinel-2 be captured reproducibly with source provenance, while keeping historical first-public availability and pre-event ownership mapping as separate unproven gates?

## Scope

The module automation/global_physical_economy_source_probe.py performs only bounded JSON requests:

1. PortWatch ArcGIS layer metadata.
2. Copernicus Sentinel-2 L2A STAC collection metadata.
3. At most three deterministically ordered rows from PortWatch, only if its metadata exposes a stable object-ID field.
4. At most two STAC item metadata records for each of three fixed geographic windows (Rotterdam, Singapore, Ningbo), over the frozen 2025-10-01 through 2025-10-15 window.

The response-body ceiling is 1,000,000 bytes per request, timeout is 20 seconds, and imagery assets are never downloaded. Raw response bytes are SHA-256 pinned and Base64-encoded in the receipt only if the complete body fits under the ceiling. Over-limit bodies are not represented as complete captures.

## Why this is worth testing

The proposed mechanism links physical maritime activity to specific assets and pre-event ownership, then asks whether the physical state becomes publicly reconstructible before later official statistics and issuer disclosures. This may be orthogonal to filing text and price-only features. It is only a hypothesis.

- PortWatch layer metadata: https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/Daily_Chokepoints_Data/FeatureServer/0?f=pjson
- PortWatch: https://portwatch.imf.org/
- Copernicus STAC collection: https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a
- Copernicus STAC API: https://documentation.dataspace.copernicus.eu/APIs/STAC.html
- Global Energy Ownership Tracker: https://globalenergymonitor.org/projects/global-energy-ownership-tracker/
- UN Comtrade data-version policy: https://uncomtrade.org/docs/data-availability/

## Mandatory interpretation

A successful HTTP request is not evidence that an historical data vintage is reproducible. A satellite acquisition timestamp is not by itself the product's first-public time. An asset's location is not evidence of a supplier/customer relationship. Current parent ownership must not be back-projected into historical rows without independently frozen evidence.

The receipt therefore hard-codes:

- historical_pit_gate.status = NOT_PROVEN
- historical_pit_gate.gate_pass = false
- scientific_boundary.performance = false
- safety.PAPER_ONLY = true
- safety.LIVE_TRADING_ENABLED = false
- safety.ORDERS_ENABLED = false
- safety.AUTOMATIC_PROMOTION = false

There is no price data, return calculation, candidate ranking, tuning, holdout selection, or performance authorization.

## Run

    python -m automation.global_physical_economy_source_probe --output research/runs/global_physical_economy_source_probe/manual.json

Use --fail-on-fetch-error in an environment where unavailable sources should fail the workflow after the receipt is written. The receipt must be retained even when a request fails.

A run that captures current responses remains source-feasibility evidence only. Before a historical retrospective test can be considered, a separately reviewed contract must establish (a) supported version/history semantics or a bounded historical archive, (b) first-public availability of the exact source version, and (c) contemporaneous pre-event asset-to-issuer exposure. If that cannot be proven, close the retrospective branch as DATA_INSUFFICIENT; consider prospective-only collection as a separate decision.

## Tests

Offline tests mock the HTTP transport. They check exact-body hashing, the byte ceiling, stable row ordering, all fixed sample windows, and the invariant that successful current responses cannot set historical PIT authorization to true. They do not claim that live providers were reached.
