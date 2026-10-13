# Q130-R2 — Historical Pageviews API archive metadata

**Status:** source/PIT feasibility only; no performance authorization.  
**Frozen R1:** [Run #38455993358](https://github.com/DWR-debug/trading-agent-public/actions/runs/38455993358), receipt `4334be29ff2387813ea9586ba12c6899979e0e43125aeaf0585b073063876568`.

## Question

R1 confirmed public daily values for the eight fixed issuer page titles during 2025-09-20 through 2025-09-24. It did not establish when a value first became public or whether later corrections can be reconstructed. R2 searches Internet Archive CDX metadata for each exact pinned API URL, without re-requesting current pageview counts or downloading archived response bodies.

## Fixed scope and caps

Eight exact article URLs, one CDX query each. Maximum 8 requests, 200 KB per response, 1.6 MB total, no retries. The original article names and R1 response/coverage pins are validated first. Results contain capture timestamps, digests and archived length only.

## Gate outcome

Archive metadata, if found, identifies a possible timestamped response to evaluate in a separately preregistered content comparison. It does not itself prove first-publication time, daily completeness or revision lineage. If no exact captures are found, that is a negative result for this archive route only, not evidence that the pageview values were never publicly available. Exact historical publication time, revision lineage and same-day formal PIT remain unproven in every outcome.
