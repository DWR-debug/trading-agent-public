# Q221 — FPDS public identity-bridge feasibility

**Registered:** 2026-10-15 09:18 UTC  
**Mode:** bounded public-source feasibility, four fixed contract records  
**Candidate status:** blocked; this request does not authorize historical parent lineage, first-public clock, issuer mapping, or performance.

## Why this probe

The prior source audit found the exact child legal name in four pre-event SEC subsidiary-list exhibits, but it did not connect that legal name to the UEI / recipient UUID in the frozen USAspending transaction. The fixed four record keys are carried forward without sampling changes.

The official FPDS SP9 implementation note states that UEI data was to be affixed to existing Contract Action Reports and that the feed included both DUNS and UEI elements; the planned bulk crosswalk was delivered through a CCB-member-restricted JIRA ticket. The public Atom feed is therefore a possible record-level bridge, but its current route may be retired: SAM.gov's current contracting page says FPDS ezSearch is retired and the FPDS Atom feed would be retired later in FY 2026. The replacement SAM.gov Contract Awards API documentation requires a public API key, which this workpack does not assume or use. See [FPDS SP9 implementation notes](https://www.fpds.gov/wiki/index.php/V1.5_SP_9.0), [legacy public Atom usage](https://www.fpds.gov/wiki/index.php?oldid=3270&title=Public_Atom_Feed_Usage), [SAM.gov contracting status](https://sam.gov/contracting), and [SAM.gov Contract Awards API requirements and schema](https://open.gsa.gov/api/contract-awards/).

## Frozen scope

Exactly four PIID-only public-feed requests are allowed, for these already-frozen keys: CACI / `FA875018C0180-P00003`; Booz Allen / `FA807520F0004-0`; OSI / `70RWMD23C00000001-0`; Northrop / `FA865124FB001-0`. The response parser must find the exact modification and signed/action date and report the raw identifier fields observed. A PIID-only hit is not enough.

Per request: 1 MB; total: 4 MB; no retries; one second between requests; 25-second timeout; at most 250 feed entries. Redirects are captured and blocked rather than followed. No SAM API requests, SEC calls, USAspending calls or archive downloads are allowed. Response bodies are hashed and parsed in memory only, then discarded.

## Interpretation

A unique entry with exact PIID/modification/date, a frozen UEI match and an exact listed legal-name match can create a **row-level identity lead** for this four-record purposeful sample. DUNS/UEI fields and entity-data-source labels are recorded as observed. For actions before 2022-04-04, a later UEI attached to an old FPDS report is not treated as proof that UEI was the authoritative identifier on the action date. No inference is permitted from a missing field, alternate modification, a similar name or a parent profile.

Even a positive result does not prove first-public observation, parent lineage as of the event, map the other 344 transactions, or clear Q221's public-clock/issuer-mapping gate. If the legacy route redirects, is retired or exposes no exact record, stop this route and retain the blocked status.

Safety: `PAPER_ONLY=true`, live trading/orders/automatic promotion/performance/holdout/ranking/tuning/promotion/live execution false; paid data budget USD 0.
