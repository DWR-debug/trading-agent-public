# Orthogonal Cross-Domain Research Frontier Audit
**Date:** 2026-10-09  
**Scope:** low-cost discovery and falsification beyond price-only and document-only features. This is a design note, not a trial, result, authorization, ranking or promotion record.

## Executive decision

The strongest new orthogonal idea for a *cheap feasibility test* is **satellite-measured port activity versus AIS-broadcast activity, mapped through a frozen port-to-industry-to-issuer exposure graph**. The novel question is not whether satellites can estimate port activity—the 2026 literature already studies that—but whether a physical-versus-broadcast discrepancy, combined with a verifiable issuer exposure edge and correct first-public timestamp, contributes information not already present in AIS, official trade records and news.

The second-best cheap test is **CISA confirmed-exploitation events × exact affected software versions (NVD CPE) × documented issuer/product/contract exposure**. Official event and product identifiers are an advantage; false positives in mapping vulnerable components to listed companies are the main weakness.

Do **not** start a new runner job for these concepts yet. Keep active execution restricted to Q104:I19 and Q218. These ideas are discovery notes only and must not alter a frozen candidate or consume resources needed to finish the I19 census.

## 1. I19 continuity and time estimate

Live run: [Q104 I19 Historical 13F Identity Census #37931811984](https://github.com/DWR-debug/trading-agent-public/actions/runs/37931811984), frozen SHA 4b65a279b1763aa7415d595967d06e1d10cbc64f.

At the latest check, five of six shards were still in progress; the 2023 shard had failed its strict acceptance-time completeness gate. Its uploaded artifact [q104-i19-census-2023-37931811984](https://github.com/DWR-debug/trading-agent-public/actions/runs/37931811984/artifacts/11625929045) contains the full four-archive scan for that shard. It records 14,502 target accessions, 14,234 successfully checked acceptance headers, 268 failures (1.848%) and zero identity conflicts.

The 268 failures break down into **251 SEC HTTP 503s** and **17 request timeouts**. This is a source-availability problem, not evidence that the filings do not exist. The workflow has a six-hour per-job timeout. From the run's 12:42 UTC start, the nominal limit is about 18:42 UTC; treat this as a ceiling, not a completion forecast. The live logs did not contain sufficiently fresh progress markers to provide a better ETA.

**Recovery principle:** don't restart the entire census to repair these 268 headers. After the remaining shards reach terminal states and artifact/commit lineage is reconciled, retry only the failed accession headers using bounded retries and the same SEC user-agent/rate budget. Emit a separate immutable retry receipt; verify that its accession set exactly matches the frozen failures and that the union covers the frozen target set without inferred timestamps. Do not relax the completeness gate or fill missing clocks. This note does not start, cancel or retry a run.

## 2. Frontier A — port shadow-flow divergence (recommended next design)

A 2026 paper combines public synthetic-aperture radar (SAR), nighttime lights and port characteristics to estimate monthly port-level maritime trade. It reports that percentage changes transfer better across regions than absolute levels, and that satellite observations complement AIS where broadcasts can be strategically suppressed. This supports the *measurement approach*, not an issuer-level trading edge.

**Hypothesis:** a frozen discrepancy between satellite-implied physical port activity and AIS-implied activity may reveal changes in port/commodity flow that are not yet reflected in official records or conventional news. Only a fixed, evidence-backed port/commodity-to-issuer mapping can pass a shock to an issuer.

NASA's Black Marble suite includes near-real-time VIIRS nighttime-light products. NASA distinguishes NRT hourly/daily variants from standard-quality products, which can be available 1–2 days after acquisition. The tradable clock must be the first observed public data version, not the satellite capture timestamp.

**Cheapest falsification:**
1. Pick a small, preregistered set of ports with independently documented disruptions. Confirm useful sensor coverage, exact publication-time evidence and stable site boundaries.
2. Freeze one physical-vs-broadcast divergence metric, baseline, weather/seasonality adjustments and sensor quality exclusions before examining outcomes.
3. Test measurement validity against independently recorded port activity changes and in periods where AIS coverage is limited. If the satellite metric cannot identify known disruptions, stop.
4. Require a source-backed issuer-to-port/commodity exposure edge; no industry-level guessing. Compare against AIS-only, official trade/port indicators, weather and news. Kill the idea if the signal adds no information or the release clock is too slow.

**Risks:** satellite port activity is not an issuer revenue forecast; firms can route through multiple ports; absolute-level estimates may not transfer; sensor sampling, cloud/moon/weather effects and release latency can dominate.

## 3. Frontier B — CISA KEV × CPE × issuer/product/contract graph

CISA's Known Exploited Vulnerabilities (KEV) catalog provides explicit date-added and remediation-deadline fields and machine-readable formats. NVD provides public Common Platform Enumeration (CPE) product records and affected-version match ranges.

**Hypothesis:** a newly confirmed exploited vulnerability matters to an issuer only when an exact affected product/version is demonstrably present in the issuer's product portfolio or operational exposure. A documented federal-contract exposure can measure materiality, but must remain a fixed covariate: the Q221 family already studies government R&D-to-procurement transitions, so this is not an invitation to create a duplicate award signal.

**Cheapest falsification:**
1. Freeze a small sample of KEV entries and preserve source versions, date-added fields and fingerprints.
2. Blindly adjudicate exact CVE → CPE/version → product/vendor → issuer links. Unknown means unknown.
3. Test precision against a keyword-only placebo and independent product advisories/incident/patch notices.
4. Stop if mapping precision requires manual story-fitting, or if the KEV date is not the first public disclosure and cannot be reconstructed.

**Risks:** complicated version ranges; downstream dependency confusion; “vendor affected” does not imply “listed issuer affected”; remediation cost can be immaterial; KEV date is not always the first public CVE disclosure.

## 4. Frontier C — facility-level operating anomalies from nighttime lights

Map issuer facilities to fixed coordinates and use NASA Black Marble NRT observations to measure within-site changes against local, seasonal and weather-conditioned baselines. Restrict to large, light-emitting facilities with independently checked coordinates and operating patterns. An event requires a light anomaly plus independent corroboration such as a utility outage, severe weather, port closure or issuer notice.

**Kill conditions:** missing/unstable facility geocoding, poor temporal coverage, pixel mixing at 500 m scale, anomalies that disappear after quality/weather controls, or no first-public timestamp. Nighttime light is an illumination/activity proxy, not a direct measure of production or revenue. Keep this separate from Frontier A; do not combine sensor features in an unconstrained score.

## 5. Frontier D — FDA AEMS as a state machine, not a report-count signal

FDA launched the unified Adverse Event Monitoring System public dashboard on 11 March 2026. Its FAQ says dashboard data are updated daily/near-real-time. FDA explicitly warns that reports can be duplicated, incomplete and unverified; a report does not establish causation, and report counts cannot establish incidence.

The only defensible hypothesis here is a **reporting/signal change followed by an official state transition** (safety communication, label change, recall or formal regulatory action), joined to a frozen product-to-issuer exposure. Do not treat raw adverse-event acceleration as safety truth or event date as public-information time. Because the public interface is relatively new and a current query is not an immutable historical snapshot, historical PIT coverage and first-observed clocks are hard gates. Prospective append-only capture may be needed. This is below A/B until versioning and historical availability are proven.

## 6. Negative finding — EDGAR exhibit access is not a prospective new candidate

Cheng, Li and Lin's 2026 Review of Accounting Studies paper “Attention to detail: how do information users process exhibits in Form 10-K?” reports that EDGAR logs separately record main-file and exhibit access. Crucially, the article states that detailed EDGAR internet-access logs for its study were available only from March 2003 through June 2017. This is useful prior art for information-processing/friction hypotheses, but not a fresh prospective source based on that sample, and it overlaps conceptually with Q218's disclosure-gap theme. Do not allocate active compute to a similar feature unless a distinct, independently available PIT source is demonstrated.

## 7. Relative priority for cheap falsification (not expected-return ranking)

| Rank | Idea | Why test at low cost | First stop condition |
|---|---|---|---|
| 1 | Port satellite-vs-AIS divergence | Physical channel; 2026 measurement paper; plausible reporting gap | No first-public clock or no precise issuer exposure graph |
| 2 | KEV × CPE × issuer/product exposure | Official event timestamps and product IDs; source test is cheap | Blinded product-to-issuer precision fails |
| 3 | Facility nighttime-light anomaly | Orthogonal physical-operations signal with NRT source | Weak coverage, bad facility mapping or noisy residuals |
| 4 | FDA AEMS × official state transitions | New daily data interface; strong caveats | PIT timestamps or product/label lineage cannot be reproduced |
| Reject as new candidate | EDGAR exhibit-access counts | Log sample ends 2017 and mechanism overlaps Q218 | Unless a distinct prospective source is found |

These priorities optimize the value of cheap research gates, not expected returns. The active candidate execution lock remains Q104:I19 and Q218.

## Sources

- Jung (2026), “Watching Trade from Space: Nowcasting and Spatial Extrapolation of Port-Level Maritime Trade Using Satellite Imagery,” arXiv:2604.15444: https://arxiv.org/abs/2604.15444
- NASA Earthdata, Black Marble: https://www.earthdata.nasa.gov/data/projects/black-marble
- NASA note on NRT vs standard-quality product availability: https://gis.earthdata.nasa.gov/portal/home/item.html?id=12b97384e1aa435eb2c0853df257b2fe
- CISA Known Exploited Vulnerabilities catalog: https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- NVD CPE/Product APIs: https://nvd.nist.gov/developers/products
- FDA AEMS public dashboard and limitations: https://www.fda.gov/drugs/fda-adverse-event-monitoring-system-aems/fda-adverse-event-monitoring-system-aems-public-dashboard
- FDA AEMS FAQ, daily/near-real-time update note: https://fis.fda.gov/extensions/FPD-FAQ/FPD-FAQ.html
- Cheng, Li & Lin (2026), “Attention to detail: how do information users process exhibits in Form 10-K?”, DOI 10.1007/s11142-026-09970-3: https://doi.org/10.1007/s11142-026-09970-3
- I19 census run and artifacts: https://github.com/DWR-debug/trading-agent-public/actions/runs/37931811984
- Q218 frozen one-shot performance record: https://github.com/DWR-debug/trading-agent-public/blob/master/research/evidence/q218_deterministic_performance_result_latest.json

## Safety boundary

This note changes no frozen contract, preregistration, trial, evidence receipt, authorization, ranking, tuning or promotion. Maintain PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, ORDERS_ENABLED=False, AUTOMATIC_PROMOTION=False. Do not dispatch new jobs from this note alone.
