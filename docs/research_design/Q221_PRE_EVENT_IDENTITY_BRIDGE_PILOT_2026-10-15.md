# Q221 — pre-event identity bridge pilot

**Registered:** 2026-10-15T12:58:00Z  
**Mode:** bounded source/identity feasibility only  
**Candidate state:** blocked; no issuer mapping or public-clock claim is authorized

## Why this test exists

The frozen Q221 sample contains 348 contract transaction keys. The current public-boundary receipt establishes neither first-public-observation time nor recipient-to-issuer mapping. A prior USAspending profile capture is complete for 247 distinct recipient identities, but it is current-state metadata and cannot be projected backward to the sampled action date.

This pilot takes exactly three already-frozen keys and captures seven small public HTML sources. It does not requery the 348-row sample, make any USAspending API call, or download bulk archives. Its only question is whether the exact pre-registered corporate/legal-entity terms appear in official documents filed or released before each action date.

## Frozen rows and outcomes

| Frozen row | Pre-event source | Pre-registered interpretation |
|---|---|---|
| CACI, Inc. – Federal, action date 2019-01-03 | SEC 2018-08-20 Form 10-K exhibit 21.1 lists “CACI, Inc. – Federal” as a Delaware corporation among CACI International’s significant subsidiaries | Exact pre-event subsidiary evidence found; continuity to 2019-01-03 remains unproven |
| Aurora Flight Sciences Corporation, action date 2024-01-02 | SEC-filed agreement dated 2022-07-04 describes Aurora as a wholly owned subsidiary of The Boeing Company | Exact pre-event parent relationship evidence found; continuity to 2024-01-02 remains unproven |
| ATK Launch Systems LLC, action date 2019-01-03 | Orbital ATK’s 2017 exhibit lists “ATK Launch Systems Inc.”; Northrop Grumman’s 2018 release documents the Orbital ATK acquisition | Legal-entity-form mismatch remains unresolved; do not assume Inc. and LLC are the same legal entity |

Sources: [CACI 2018 filing index](https://www.sec.gov/Archives/edgar/data/16058/000156459018022021/0001564590-18-022021-index.htm), [CACI exhibit 21.1](https://www.sec.gov/Archives/edgar/data/16058/000156459018022021/caci-ex211_14.htm), [Aurora agreement filing index](https://www.sec.gov/Archives/edgar/data/1706946/000170694622000124/0001706946-22-000124-index.htm), [Aurora master agreement](https://www.sec.gov/Archives/edgar/data/1706946/000170694622000124/a101auroramasteragreement.htm), [Orbital ATK filing index](https://www.sec.gov/Archives/edgar/data/866121/000086612117000027/0000866121-17-000027-index.htm), [Orbital ATK exhibit 21](https://www.sec.gov/Archives/edgar/data/866121/000086612117000027/oa-ex21x20161231.htm), [Northrop Grumman acquisition release](https://investor.northropgrumman.com/news-releases/news-release-details/northrop-grumman-completes-orbital-atk-acquisition-blake-larson).

## Method and hard limits

1. Validate the exact Q221 manifest Git blob/fingerprint and all three transaction keys.
2. Validate the existing 247-row identity-map artifact from run [#38305074104](https://github.com/DWR-debug/trading-agent-public/actions/runs/38305074104), its raw JSON SHA-256, receipt fingerprint, and the selected current-profile rows.
3. Capture one response from each of the seven pre-registered HTTPS URLs only. Each response is capped at 300,000 bytes; aggregate response bytes are capped at 900,000; timeout is 30 seconds with a one-second gap. There are no retries.
4. Retain the captured public HTML only as a temporary, immutable workflow artifact. Validate fixed required text tokens and source hosts, then independently re-parse the exact capture on Ubuntu ARM64 with zero network requests.
5. Publish a receipt only if the offline reproduction matches the x64 analysis fingerprint exactly.

No source body hash, manifest key, recipient identity, legal entity, or mapping field can be rewritten to make this pilot pass. A missing/changed source results in a failed-closed receipt.

## Decision boundary

A positive source-token check means only that a bounded official page contains the pre-registered wording. The filing date of a document is not the first-public timestamp of a USAspending transaction. A pre-event ownership statement does not establish uninterrupted legal continuity through the transaction's action date, and a current parent profile does not prove historical parent lineage.

The 348-row Q221 public-clock gate remains closed. All three issuer symbols remain null; recipient-to-issuer mapping remains unfrozen. No performance, holdout selection, ranking, tuning, promotion, orders, or live execution is authorized.

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`; paid API budget remains USD 0.
