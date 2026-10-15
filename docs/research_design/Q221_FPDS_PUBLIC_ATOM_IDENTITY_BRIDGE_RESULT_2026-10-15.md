# Q221 — FPDS public Atom identity-bridge result

**Result date:** 2026-10-15  
**Source run:** [#38712516839](https://github.com/DWR-debug/trading-agent-public/actions/runs/38712516839)  
**Immutable final artifact:** [q221-fpds-public-atom-final-38712516839-1](https://github.com/DWR-debug/trading-agent-public/actions/runs/38712516839/artifacts/11960828222)  
**Canonical evidence:** `research/evidence/q221_fpds_public_atom_identity_bridge_latest.json`  
**Receipt fingerprint:** `f041edf725388a47aeb1ec96076bfbffcdc8946acc87fb4c8cb515f8c3c03817`  
**Analysis fingerprint:** `732a23385f9a5346e7a0806e342647658e6a4f88ea3d1ee233b956ead4277309`

## Observed result

The bounded, preregistered probe made exactly four public FPDS Atom requests, one for each frozen PIID in the four-record Q221 child-entity bridge sample. All four returned HTTP 302. The no-redirect policy blocked all four responses. No redirect target was followed, no response body was persisted, total body bytes were 0, and no exact PIID/modification/action-date/UEI/name tuple was returned.

| Frozen row | HTTP status | Result |
|---|---:|---|
| CACI — `FA875018C0180 / P00003 / 2019-01-03` | 302 | `REDIRECT_BLOCKED` |
| Booz Allen — `FA807520F0004 / 0 / 2020-01-02` | 302 | `REDIRECT_BLOCKED` |
| OSI / American Science & Engineering — `70RWMD23C00000001 / 0 / 2023-01-03` | 302 | `REDIRECT_BLOCKED` |
| Northrop Grumman — `FA865124FB001 / 0 / 2024-01-02` | 302 | `REDIRECT_BLOCKED` |

The x64 capture stage and the ARM64 offline validation stage both succeeded. ARM64 made zero network requests and validated the frozen capture receipt with the same analysis fingerprint. This is deterministic validation of the captured negative outcome, not an independent replay of the source feed.

## Interpretation

This result establishes that the exact preregistered legacy public route was not usable under the no-redirect contract at probe time. It does **not** prove that all FPDS data are unavailable or that a particular redirect destination is authoritative. The route is now closed for this workpack: do not repeat the same calls or follow the redirect speculatively.

No SAM.gov Contract Awards API request was made because this task did not assume an API key was available. Any future use of a replacement API must be a separately reviewed and authorized source contract, with explicit access and historical timestamp semantics; it must not silently widen or rewrite this frozen probe.

## Q221 gate status

Q221 remains blocked:

- The 348-row frozen transaction sample still lacks proof of the first public-observation time for 348/348 rows.
- All 247 frozen recipient identities remain unmapped to public issuers.
- The separate current-parent profile audit captured 247/247 profiles (71 current-parent leads, 176 without a separate parent under its classifier), but those are current-state leads, not historical parent lineage.
- The pre-event SEC subsidiary-list audit found exact child legal names for the four selected rows, but it did not bridge those names to the frozen recipient UUID/UEI.
- For pre-2022 transactions, a UEI attached to a later record is not proof that UEI was authoritative on the original action date.

The next admissible path is a separately reviewed, actually accessible historical record-level source that supplies a defensible event-time identity bridge and publication-time semantics. If no such source is available under authorized access, preserve the negative result and keep Q221 blocked. Do not infer issuer identities from name similarity, current parent metadata, or a redirect.

## Safety and frozen scope

The frozen 348 transaction keys, four-record probe set, upstream receipt fingerprints, expected values, population and research gates are unchanged. No source rows or response bodies were rewritten or persisted. No Feed archive or SEC primary document was downloaded.

`PAPER_ONLY=true`; `LIVE_TRADING_ENABLED=false`; `ORDERS_ENABLED=false`; `AUTOMATIC_PROMOTION=false`. Performance authorization, holdout selection, ranking, tuning, promotion and live execution remain false. Paid data budget remains USD 0.
