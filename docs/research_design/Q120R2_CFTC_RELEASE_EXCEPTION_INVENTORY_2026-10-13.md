# Q120-R2 — Official CFTC release-exception inventory

**Scope:** official source/PIT metadata only  
**Upstream feasibility receipt:** [Run #38456880720](https://github.com/DWR-debug/trading-agent-public/actions/runs/38456880720)  
**Upstream fingerprint:** `9e79abc9fac1b9d1599b35e111e82e19f8b365d99e06a447638d0c0135321445`

This bounded follow-up parses only the CFTC Release Schedule and Historical Special Announcements pages. It records report date, original publish date and new publish date only when all three are explicitly listed by CFTC. The normal 3:30 p.m. ET schedule is context, not an invented historical publication date.

A historical exception row can establish the dates stated by the agency for that listed event. It does **not** establish the exact first public timestamp, prove that the page lists every exception, or make unlisted dates safe for same-day use. In particular, no default Friday date is assigned to an unlisted report date. Payload HTML is hashed for provenance but not persisted.

**Success meaning:** the fixed sources and table contract were parsed successfully. It is not a PIT clearance or performance result.

Sources: [CFTC release schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm); [CFTC historical special announcements](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm).
