# Q221 — current parent identity lead map

**Source run:** [#38305074104](https://github.com/DWR-debug/trading-agent-public/actions/runs/38305074104)  
**Immutable artifact:** [q221-current-parent-identity-map-38305074104-1](https://github.com/DWR-debug/trading-agent-public/actions/runs/38305074104/artifacts/11772786096)  
**Source artifact receipt fingerprint:** `ae3a3263d5e7d2545dbdaed7ba7ff1cfe3d4cd00e0403352096dcce4d4797602`  
**Summary receipt fingerprint:** `444179ed66cb0560ca792d2b831144c89165f46f19095a15456e21db7b18623a`  
**Persisted summary:** `research/evidence/q221_current_parent_identity_map_summary_2026_10_12.json`

## Verified result

The bounded USAspending recipient endpoint run completed 247/247 frozen recipient profiles from 247/247 requests. It transferred 342,214 response bytes under the 25,000,000-byte budget. The source artifact's own receipt fingerprint was independently recomputed; the compact summary has a separate canonical fingerprint.

| Classification | Count | Meaning |
|---|---:|---|
| `CURRENT_PARENT_ENTITY_LEAD` | 71 | Current profile reports a distinct parent entity, a lead for further evidence collection |
| `CURRENT_PROFILE_SELF_OR_NO_SEPARATE_PARENT` | 176 | Current profile has no separate parent under this classifier |

The lead map is current-state metadata only. It does **not** establish historical parent lineage, prove a transaction-level first-public timestamp, identify a public issuer, or freeze recipient-to-issuer mapping. The source receipt and its 348 frozen transaction keys are unchanged.

## Next gate

For the 71 parent leads, require independent evidence that predates the relevant transaction and verifies the entity relationship as of that date. No name-similarity mapping, current-parent inference, or retroactive historical claim is allowed. If an authoritative pre-event identity bridge cannot be found, retain the unresolved mapping state.

No new USAspending calls were made for this repository summary. This is persistence of the existing immutable artifact, not a rerun.

Safety remains `PAPER_ONLY=true`, `LIVE_TRADING_ENABLED=false`, `ORDERS_ENABLED=false`, `AUTOMATIC_PROMOTION=false`; no performance or promotion authority is added.
