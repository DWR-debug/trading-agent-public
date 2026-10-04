# Q182 FERC Self-Hosted Access Probe — current-master refresh

This is a bounded operational/data-QA probe for the Q182 FERC eLibrary access block.

## Purpose
Distinguish a GitHub-hosted HTTP 403 from a broader source-access restriction by running the same fixed official URLs on both verified Windows self-hosted research lanes.

A PASS is only operational reachability evidence. It does not establish historical completeness, PIT validity, entity mapping, revision lineage, performance or promotion.

## Fixed routes
- https://ferc.gov/what-elibrary
- https://www.ferc.gov/about/what-ferc/frequently-asked-questions-faqs/documents-and-filing/elibrary

## Execution
Two matrix lanes:
- local_reproduction
- data_qa

The workflow is fork-guarded, fail-closed, paper-only and artifact-backed.

## Scientific boundary
No prices, returns, ranking, selection, tuning, holdout use, performance authorization, promotion or live execution.
