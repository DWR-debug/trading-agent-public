# Q127-R1 — FINRA Reg-SHO Historical Source / PIT Feasibility

## Status

SOURCE / PIT FEASIBILITY ONLY. No performance authorization.

## Objective

Move Q127 beyond static source-page markers by reproducing a fixed historical sample of the FINRA Consolidated NMS Daily Short Sale Volume file and preserving raw source provenance.

FINRA states that these files are posted no later than 18:00 ET on the same trade date and that rare subsequent updates may occur; updated files are identified separately on the FINRA page.

## Fixed universe

Q107 frozen symbols:
SPGI, NDAQ, AMP, RJF, WMB, VLO, DVN, EMN.

## Fixed historical sample

- 2024-02-05
- 2024-07-01
- 2025-01-02
- 2025-09-24

## Source contract

For each date use the observed public Consolidated NMS naming pattern:

https://cdn.finra.org/equity/regsho/daily/CNMSshvolYYYYMMDD.txt

Preserve:

- exact URL;
- raw SHA-256;
- response headers relevant to provenance;
- file header/schema;
- exact rows for the fixed symbols;
- symbols absent from a file.

A successful probe must not silently substitute a different venue file.

## Revision / PIT boundary

The FINRA page's 18:00 ET statement is a publication upper bound for the daily file, not an exact historical first-publication timestamp. FINRA also states that rare later updates may occur.

Therefore:

- revision_lineage_established = false unless immutable original/updated version history is recovered;
- same_day_pit_safe = false for formal use at this stage;
- no performance inference may be made from the probe;
- ticker/symbol identity alone is not a sufficient permanent-security identity for a formal historical study.

## Required next gate

Establish deterministic historical security identity mapping and immutable original-vs-updated file lineage before any candidate-specific PIT compiler can be treated as formal evidence.

## Scientific boundary

No returns, holdout use, ranking, selection, tuning, performance authorization, promotion or live execution.
## File-schema contract

The FINRA format guide requires a header and a final numeric trailer containing the number of produced records. The `Market` field identifies the reporting facility, so the same symbol may legitimately occur on multiple market rows. The parser therefore keys uniqueness by `(Symbol, Market)`, preserves all fixed-symbol rows, and verifies the trailer count against parsed data rows. This is a source-schema correction only; it creates no performance evidence.
