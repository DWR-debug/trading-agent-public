# Q220 — historical hash timeline reconciliation

**Registered:** 2026-10-15  
**Scope:** deterministic offline reconciliation of already committed historical and current receipts.  
**Status:** historical hash agreement is attested; current source lineage and authoritative vintage remain unresolved.

## Correct distinction

The current four-hash diagnostic asks whether the frozen expected SHA-256 occurs in the four *current whole-document observations*. It does not summarize all prior history. A separately committed historical receipt proves that a successful compiler run on 2026-10-11 reported all 55 frozen hashes matched, and an independent reproduction also reported success. Those historic runs did **not** retain the raw whole-document bytes, so they attest to the successful hash comparisons at the time but cannot now be independently re-hashed from preserved bodies.

That means the accurate conclusion is not “the expected hash was never reproduced.” The accurate conclusion is:

- **Historically attested:** 55/55 frozen hashes matched in compiler run [38182963418](https://github.com/DWR-debug/trading-agent-public/actions/runs/38182963418), receipt fingerprint `1b34b3ac2f3a6fc3ff90fa42cd8ea1c7b73297b5cbd71414a0877bb25d9b203c`, generated at `2026-10-11T23:06:37.379425Z`.
- **Independently attested then:** run [38183038217](https://github.com/DWR-debug/trading-agent-public/actions/runs/38183038217) reported `Q220_INDEPENDENT_PIT_REPRODUCED`, 55 rows and zero hash failures.
- **First stored blocked state:** run [38210402239](https://github.com/DWR-debug/trading-agent-public/actions/runs/38210402239), at `2026-10-12T06:00:28.208402Z`, reported 55 hash failures and zero verified primary documents.
- The last positive and first negative compiler receipts used the same compiler source blob `c4587f75551297c1ceae9ed151196681eddfbdb8` and code SHA-256 `6a8fb9496181fb2a46393d4d9dc348660b068d50255d807401bb8eff0da686ed`. The observation window is approximately 6 hours, 53 minutes; these timestamps bound observations, not the exact server-side change time.
- A separate same-code collector comparison from 2026-10-10 17:19 UTC to 2026-10-11 08:24 UTC found all 55 hashes changed and all 55 primary response lengths decreased by five bytes. The filing-header response hashes also changed for all 55 records while directory-index hashes stayed unchanged. This still does not prove an origin/intermediary cause.

## Current observation set

The later pinned source-hash lineage run reconciles four distinct complete-document hashes for the SPGI 2019 filing under the same URL and `Last-Modified` value:

| Current whole-document observation | Bytes | SHA-256 |
|---|---:|---|
| Original forensics observation | 4,774,458 | `08039132d6d6d1692d1f7552193c70a04cad4c1dcadad1cfa3ca2b8b4efe3fdb` |
| Five identical HTTP sensitivity responses | 4,774,457 | `fc7dfedd605cdbc9e497bb0c0bc306c74e3f90493a68fb6025d762540ef600f3` |
| Current compiler response | 4,774,465 | `ccd9060d023c3ca8e5fc5d3fd43a67c394dfd97ef1e42a72f71c4ca630cd2f63` |
| Later single-feed boundary response | 4,774,465 | `2693819652172f0c218394ef036eb3f4af95c2a7077f624f6efcd990df370172` |

The frozen expected SHA-256 is `27177e35cf02e7b66c24aee89bfc97a00f12f7022c6e584e3b48dc70d56abc83` at 4,774,458 bytes. It is **absent from those four later body observations**, but its historical successful hash comparison remains attested by the 2026-10-11 receipts above. The raw historical response bodies are unavailable, so the earlier match cannot be re-hashed offline.

## Interpretation and boundary

The evidence is consistent with time-varying complete-document response representations after the frozen set was established, but it does not identify which server/intermediary layer changed the bytes or independently establish the authoritative source vintage. The current source population still has 55 failures and zero currently verified primary documents. **Q220 remains BLOCKED.** The current lineage receipt is not superseded as a run artifact; this reconciliation corrects how its current-only field `frozen_expected_hash_reproduced=false` should be read in the context of historical receipts.

This workflow uses only the two already committed JSON receipts pinned by their Git blob SHA-1 values. It makes no source requests, downloads no body, and changes no frozen hash, population, compiler receipt or gate. The output has independent deterministic x64 and ARM64 fingerprints.

Next gate: locate an authoritative pinned source-vintage record or preserve the blocked state. No further Feed or primary-document downloads, hash rewrites, census restart, performance work, holdout selection, ranking, tuning, promotion, orders or live execution are authorized.

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`.
