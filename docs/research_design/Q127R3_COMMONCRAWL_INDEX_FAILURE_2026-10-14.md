# Q127-R3 — Common Crawl exact-file metadata path timed out

**Observed:** 2026-10-14 06:02:24 UTC  
**Run:** [Q127-R3 diagnostic #38519811046](https://github.com/DWR-debug/trading-agent-public/actions/runs/38519811046)  
**Receipt fingerprint:** `5667314ff526288cb695e3dc6c911c6f274669518a9f7b60008f451a606326ea`

The official Common Crawl collection index succeeded with HTTP 200 (35,226 bytes). All four exact-URL CDX metadata lookups returned HTTP 504 with a 167-byte error response:

| Frozen FINRA daily file date | Collection selected | Result |
|---|---|---|
| 2024-02-05 | `CC-MAIN-2024-10` | HTTP 504 |
| 2024-07-01 | `CC-MAIN-2024-30` | HTTP 504 |
| 2025-01-02 | `CC-MAIN-2025-05` | HTTP 504 |
| 2025-09-24 | `CC-MAIN-2025-43` | HTTP 504 |

Total: five requests, 35,894 bytes. No FINRA target file or WARC record was downloaded. The workflow succeeded at producing a bounded, immutable, fail-closed diagnostic receipt, but the data probe remains incomplete.

**Interpretation:** this establishes that the Common Crawl exact-URL index route was unavailable during this run. It does not prove that these files were absent from crawls or never published by FINRA. Do not blindly retry the same four queries. The next attempt needs an independently validated access route (for example, an alternate official URL-index/columnar method or another archive service), with the same frozen dates and metadata-only contract.

All source keys, budgets and Paper-Only gates remain unchanged.
