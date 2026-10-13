# Q127-R2 — FINRA archived-listing / raw-file capture metadata

**Status:** source/PIT feasibility only; no performance authorization.  
**Frozen R1:** [Run #38455702686](https://github.com/DWR-debug/trading-agent-public/actions/runs/38455702686), receipt `2cbe22c49d885f527ac523ed74ab1e13a843c23999916c674282de6977e9c33c`.

## Question

R1 fetched and parsed the four fixed FINRA Consolidated NMS files successfully, but the historical original-versus-updated file lineage was not established. FINRA says files are posted by 18:00 ET on the same trade date and rare subsequent-day updates can occur. R2 tests whether Wayback exposes bounded metadata for those exact original URLs or the official listing without downloading the underlying short-sale data again.

## Fixed scope and caps

Four URLs are fixed by the R1 sample: 2024-02-05, 2024-07-01, 2025-01-02, 2025-09-24. The probe makes one CDX metadata query per URL, one CDX query for the official listing index, and fetches only two preselected small historical listing captures (2024-07-22 and 2025-01-20). Maximum 7 requests, 350 KB per response, 1.5 MB total; no retries and no FINRA data-file payload downloads.

A listing capture can establish that a filename was visible by the capture time. It cannot establish the exact first-publication time or original payload bytes. A CDX no-hit is not proof that a URL was never public.

## Gate outcome

The result persists the exact CDX capture metadata, listing snapshot hashes and target-filename visibility. Regardless of whether captures are found, `exact_first_publication_time_proven=false`, `original_vs_updated_file_lineage_proven=false`, and `same_day_formal_use_allowed=false`. A positive archival hit would motivate a separately bounded content comparison; it does not clear the PIT gate.
