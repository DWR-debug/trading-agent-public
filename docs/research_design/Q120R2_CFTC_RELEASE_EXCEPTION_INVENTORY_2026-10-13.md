# Q120-R2 — Official CFTC release-exception inventory

**Scope:** official source/PIT metadata only  
**Upstream feasibility receipt:** [Run #38456880720](https://github.com/DWR-debug/trading-agent-public/actions/runs/38456880720)  
**Upstream fingerprint:** `9e79abc9fac1b9d1599b35e111e82e19f8b365d99e06a447638d0c0135321445`

This bounded follow-up reads only the CFTC release schedule and historical special-announcements pages. It records report date, original publication date, new publication date, and the date heading of the announcement section containing each table. Repeated report dates in different dated announcements are retained as distinct schedule versions. Conflicting values for the same report date inside the same announcement section still fail closed.

The first live attempt after fixing the UTC import produced a receipt but remained incomplete because the current official page includes multiple dated versions: the December 9, 2025 announcement lists report date 2025-11-10 with intended new publication date December 10, while the November 18, 2025 announcement lists the same report date with intended new publication date December 12. The parser must preserve those two source versions rather than collapse them to one row.

A table row establishes only what CFTC stated in that dated announcement. It does **not** establish the exact first public timestamp, prove the page captures every exception, or authorize a guessed Friday release date for unlisted reports. CFTC describes the listed dates as intended publication dates. The UTC receipt timestamp is observation metadata, not the public availability time of the underlying COT report. No date policy is auto-applied.

**Bound:** two official requests; 350 KB per response and 700 KB total. No response bodies are persisted; receipt records response hashes, size, HTTP status and explicit extracted rows.

Sources: [CFTC release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm); [CFTC historical special announcements](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm).
