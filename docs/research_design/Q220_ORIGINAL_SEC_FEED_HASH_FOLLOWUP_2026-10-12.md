# Q220 — Original SEC Feed primary-hash follow-up

**Workpack:** `Q220-ORIGINAL-FEED-FOLLOWUP-2026-10-12`  
**Registered:** 2026-10-12 UTC  
**Stage:** bounded primary-source vintage feasibility only; no PIT gate opening or performance authority.

## Why this is a new request

The prior run [#38239078713](https://github.com/DWR-debug/trading-agent-public/actions/runs/38239078713) failed closed. Its 2019-02-20 DVN complete submission exceeded the immutable 30 MB per-member limit. Repeating that exact request would predictably stop again after a costly Feed download.

This follow-up leaves the original request, source receipt, source-population fingerprint, and expected hashes untouched. It replaces only the over-limit sample with WMB filing `0000107263-19-000007`, already present in the same frozen 55-failure population. The WMB primary document is 4,613,193 bytes in the frozen receipt, but this does **not** prove that the full historical `.nc` member is below 30 MB. The runtime cap remains authoritative and the run must fail closed if the full member exceeds it.

## Fixed sample

1. SPGI — `0000064040-19-000059`, 2019-02-13, `spgi-20181231x10k.htm`.
2. WMB — `0000107263-19-000007`, 2019-02-21, `wmb_20181231x10k.htm`.
3. SPGI — `0000064040-25-000052`, 2025-02-11, `spgi-20241231.htm`.

All keys and expected hashes are read from the unchanged Q220 source receipt. Selection uses technical/source feasibility only; no market outcomes are accessed.

## Hard limits

The limits are identical to the original preregistration: 1.5 GB per daily Feed archive; 15 MB per current primary document; 30 MB per original submission member; 12 GB cumulative TAR scan; 4.6 GB total downloaded bytes; 600-second request timeout; one-second inter-request gap. A known Content-Length mismatch is incomplete data, not a successful fetch.

## Decision and safety

A completed receipt can clarify whether frozen hashes match contemporaneous accepted-submission bytes. It cannot change the 55-row source population, rewrite hashes, mark Q220 PIT-ready, authorize performance, select a holdout, rank/tune candidates, promote a strategy, or enable live execution. This workpack remains paper-only.

Official method references: [SEC — Accessing EDGAR Data](https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data) and [SEC EDGAR README](https://www.sec.gov/Archives/edgar/README.txt).
