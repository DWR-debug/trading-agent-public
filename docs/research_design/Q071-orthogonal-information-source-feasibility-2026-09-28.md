# Q071 — Orthogonal Information Source Feasibility — 2026-09-28

## Status
**DESIGN_ONLY.**

Q071 expands candidate discovery beyond another round of OHLCV parameter variants. It freezes six mechanism families for source/PIT feasibility work only. No candidate is ranked and no performance result is used for inclusion.

## Candidate families

| ID | Family | Source | First gate | PIT posture |
|---|---|---|---|---|
| I1 | FINRA Reg SHO short-sale flow shock | FINRA | source + public-availability PIT | next session |
| I2 | SEC Form 4 insider flow | SEC EDGAR | source + filing-header PIT | next session |
| I3 | ALFRED macro vintage surprise/state | ALFRED | source/vintage PIT | next session |
| I4 | CFTC COT crowding/de-crowding | CFTC | source + actual-publication PIT | next session |
| I5 | Wikimedia firm attention shock | Wikimedia | source + entity-map contract | next session |
| I6 | GDELT media tone/attention shock | GDELT | source + entity/version contract | next session |

## Why these are worth testing

The existing research already contains multiple price-only families and a repeated drawdown bottleneck. Q071 therefore targets information channels that are not simple transformations of OHLCV.

### I1 — FINRA Reg SHO
FINRA provides daily security-level short-sale volume data and API access. The signal would be treated as short-sale activity, not as short-interest position data. The source contract must explicitly preserve its off-exchange/reporting-facility scope and public-availability timing.

### I2 — SEC Form 4
SEC EDGAR exposes acceptance timestamps in filing headers, which gives a much sharper historical PIT anchor than merely using the filing date. The public quarterly insider datasets are useful for bulk discovery, but the raw filing/header remains the authority for metadata needed for PIT.

### I3 — ALFRED
ALFRED's vintage-date model is unusually suitable for historical PIT research because it explicitly retrieves values as they existed on a past date. This is a cleaner route than trying to reconstruct an intraday macro-release clock. A future candidate must still freeze the exact series and composite rule before any outcome is observed.

### I4 — CFTC
CFTC COT history is extensive, and the normal release schedule is explicit. The key feasibility problem is that historical report dates and actual public-release dates can diverge, notably during the 2025 publication interruption. Any formal use therefore needs an actual-publication ledger.

### I5 — Wikimedia
Wikimedia pageview data provide a public, timestamped attention proxy. This is deliberately experimental: the entity-to-article mapping and bot filtering can create hidden selection or leakage unless frozen.

### I6 — GDELT
GDELT publishes archived event/news files that make an unusual media-information layer technically possible without a paid news feed. Entity resolution, source-set stability and version/fingerprint control are the dominant risks; these are feasibility gates, not reasons to assume alpha.

## Formal sequence

1. Source-access and schema feasibility.
2. Point-in-time/public-availability contract.
3. Frozen entity/universe mapping.
4. Fresh disjoint coverage.
5. Mutation PIT test.
6. Only then, separately authorized performance evaluation.

No holdout selection, candidate ranking, parameter tuning or promotion is permitted in Q071.

## Current evidence boundaries

Q071 does not modify Q068, Q069 or Q070. The active Q068 and Q070 pipelines remain on their frozen definitions.

Related project evidence:
- Q040 official-event feasibility separated source accessibility from historical publication-time PIT.
- Q042 established PIT-safe code for the 52-week-high and overnight/daytime mechanisms, but no performance evidence.
- Q019 validated the Treasury auction data contract; Treasury is not counted as a new Q071 family.

## External source notes

- FINRA Reg SHO Daily Short Sale Volume: official API/catalog.
- SEC EDGAR filing headers and insider transaction datasets.
- ALFRED vintage-date archival data.
- CFTC COT release schedule and historical archives.
- Wikimedia public pageview data.
- GDELT archived event files.

This document is discovery/feasibility infrastructure only.
