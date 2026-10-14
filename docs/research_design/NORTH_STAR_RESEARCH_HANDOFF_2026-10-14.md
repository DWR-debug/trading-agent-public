# North Star Research Handoff — 2026-10-14

**Snapshot UTC:** 2026-10-14 07:14:00Z
**Snapshot master SHA:** `fbcdc0c1123a02186b5282b420ed64ab61c5a396`
**Work repository:** `DWR-debug/trading-agent-public`
**Latest engineering merge:** [PR #1427](https://github.com/DWR-debug/trading-agent-public/pull/1427), merge commit `784b4be5c0d227e5fe3db6ee2df1cb96966f59a4`.

## Highest-value progress

### Q104:I22 — independent PIT reproduction now passes

- Run: [#38526675922](https://github.com/DWR-debug/trading-agent-public/actions/runs/38526675922)
- Immutable receipt SHA-256 fingerprint: `923afa1165e9f161caea6be187abb7eceeefc313b49cac5faa42849d701592ff`.
- The immutable reconciliation input is pinned to source compiler run #38274043682 and receipt fingerprint `058bba7fd9aebb9d30cc5294fc71548ebe9bd9f11d5ee38a558936b29ecfb9a0`; the previous `I22_RECONCILIATION_PIN_MISMATCH` was a mutable-`latest` pointer defect, not a negative PIT result.
- Independent reproduction: 2,209 filing events; 2,011 eligible issuer sessions; eight fixed issuers; 24/24 prefix cases pass; x64 and ARM64 semantic outputs agree; independent SEC refetch is semantically equal; input order and future acceptance invariance pass for all eight symbols.
- **Still blocked:** mechanism orthogonality. The frozen comparison contains 121 peers, zero complete comparisons and 121 incomplete comparisons because peer `source_components` and `source_domains` are missing. Tokens alone cannot prove non-overlap.

**Next Q104 gate:** a metadata-only signature-completeness audit across these 121 peers, using only existing candidate/receipt metadata. Unknown source components/domains must stay unknown; no score/rank or performance gate can be substituted.

## Source/PIT candidate status

| Candidate | Latest verified result | Gate still closed |
|---|---|---|
| Q104:I22 | Independent PIT reproduced; immutable receipt saved by run #38526675922. | Mechanism non-overlap review; no performance authority. This does not close the separate Q104:I19 acceptance/census work. |
| Q220 | 55/55 primary-document hash mismatches; exact original document bytes were not retained with the population. Two sampled SEC feed identities matched, hashes did not; the third ~1.11 GB download was incomplete. | As-filed document provenance and PIT. Keep every frozen hash; no repeat of the large download. |
| Q221 | 348/348 historical public-observation timestamps unresolved; 247/247 recipient identities unmapped to issuer. Catalogue has no multi-date archive series; the same parent-UEI API returned HTTP 503 twice before preflight. | Historical public clock, agency/correction semantics and issuer mapping. No third call to the same failed API. |
| Q120-R2 | [Run #38479765335](https://github.com/DWR-debug/trading-agent-public/actions/runs/38479765335): 30 official CFTC exception rows; 28 changed publish dates. | Historical release calendar remains incomplete; exact first-public time not proven. Explicit listed dates only; no default Friday assumption. |
| Q127-R3/R4 | [R3](https://github.com/DWR-debug/trading-agent-public/actions/runs/38519811046) Common Crawl queries returned HTTP 504; [R4](https://github.com/DWR-debug/trading-agent-public/actions/runs/38526554657) verified the official current listing: all four fixed files listed once, no Updated badges. | Historical listing/version and exact first-public times are still unproven. Do not repeat the same 504 routes. |

## Compute and regression checkpoint

- [Windows Candidate Gate Regression Wave #38526554709](https://github.com/DWR-debug/trading-agent-public/actions/runs/38526554709) is in progress at the time of this checkpoint.
- Completed packs: Q221 on `LHT-N133732-3`, Q104 on `LHT-N133732-2`, and Q220 on `LHT-N133732`; all three completed successfully at about 07:13:39Z.
- Running packs as of 07:14Z: Q120 on `LHT-N133732-2`, Q127 on `LHT-N133732-3`, Q130 on `LHT-N133732`. These exact jobs occupy the three physical Windows slots; when the jobs complete, the slots are available again without requiring online telemetry.
- The latest completed Q127-R4 official source run used two metadata requests and 863,158 bytes; fingerprint `b54dadc8b25ed14ecd14aa0abb0719e293634ce9b235573c03c4595620479d29`.
- The fast dispatcher observed all three Windows slots occupied during its 07:10 run and correctly emitted zero dispatches; this was not an idle-runner veto. Three old monitor/router runs queued since 2026-10-07 remain stale queue entries and do not themselves occupy a Windows slot.

## Non-negotiable boundaries

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`; paid API budget USD 0. No performance run, holdout selection, candidate ranking, parameter/threshold/horizon search, promotion or live execution is authorized by any result in this handoff.

## Resume order

1. Finish and verify Windows regression #38526554709, including the Q127-R4 test now included in the Q127 pack.
2. Persist the Q104:I22 success receipt at an immutable run-specific path and preserve its fingerprint.
3. Build a metadata-only audit of why 121 peer signatures lack source component/domain coverage; fill only from explicit existing contracts/receipts and keep unknowns fail-closed.
4. Separately crosswalk the 30 explicit Q120-R2 exception rows against the fixed report-date population only if the original population receipt/pin can be reverified.
5. Keep Q220 and Q221 blocked until a distinct evidence source can address the exact provenance/clock gap. Do not change frozen hashes, populations, mappings, or acceptance criteria.
