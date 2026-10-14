# Q127-R4 — Official FINRA year-filtered listing metadata

**Scope:** official source metadata only; no target file bodies are downloaded.  
**Upstream frozen sample:** [Q127-R1 Run #38455702686](https://github.com/DWR-debug/trading-agent-public/actions/runs/38455702686)  
**Upstream fingerprint:** `2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c`

The previous Q127-R2 Wayback route found no target-file captures, and Q127-R3's Common Crawl exact-URL queries all returned HTTP 504. This follow-up uses a distinct route: the official FINRA daily-file catalogue's year filter for 2024 and 2025.

A manual live metadata inspection on 2026-10-14 returned HTTP 200 for both selected year views and showed each of the four fixed Consolidated NMS links exactly once:
- 2024-02-05 (`CNMSshvol20240205.txt`): 321 KB
- 2024-07-01 (`CNMSshvol20240701.txt`): 323 KB
- 2025-01-02 (`CNMSshvol20250102.txt`): 342 KB
- 2025-09-24 (`CNMSshvol20250924.txt`): 358 KB

No visible `Updated` label was adjacent to these links in the current listing. FINRA's own page states that daily files are posted no later than 6:00 p.m. ET on the trade date, but also that a subsequent-day update is possible and updated files are labelled. These statements provide an official publication policy/nominal upper bound; they do not prove the historical first-public timestamp or which bytes were available then.

The automated probe must preserve the exact selected-year filter, response hashes/byte counts, exact target URL counts and adjacent visible labels. It will not persist raw HTML or download the four FINRA files. Regardless of result, same-day PIT clearance and historical revision lineage remain false unless separate immutable vintage evidence is established.

Sources: [FINRA Daily Short Sale Volume Files](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files); [FINRA Short Sale Volume Data catalogue](https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data).
