# Q221 — Historical public-clock archive inventory

**Audit date:** 2026-10-11  
**Repository baseline:** \`DWR-debug/trading-agent-public\` master \`d20a8211e8c7a52a675481af7989b686f5968bce\`  
**Upstream source revision inspected:** \`fedspendingtransparency/usaspending-api\` commit \`03b9e2554837998c4c261c65e2947dc79f23855a\`  
**Classification:** Source feasibility / PIT infrastructure only. Not scientific evidence or performance authorization.

## Research question

Can public USAspending source artifacts supply historical transaction-level observations for the fixed Q221 contract-transaction sample? The existing Q221 receipt correctly keeps \`historical_first_public_observation_proven=false\`. The earlier archive gate establishes only that several versions of the *About the Data* PDF can be reconstructed; a policy PDF does not establish when any named contract transaction first became public.

## Sources inspected and what they establish

1. The official transaction-history contract for \`POST /api/v2/transactions/\` lists transaction attributes including \`action_date\`, \`action_type\`, \`modification_number\`, and description; it does not document a per-transaction first-publication timestamp.  
   Source: [transactions endpoint contract](https://github.com/fedspendingtransparency/usaspending-api/blob/03b9e2554837998c4c261c65e2947dc79f23855a/usaspending_api/api_contracts/contracts/v2/transactions.md).

2. The official reporting submission-history contract returns \`publication_date\` and \`certification_date\` histories keyed by top-tier agency, fiscal year, and fiscal period. The implementation reads \`SubmissionAttributes\` history and describes the route as agency-account submission history. These dates are not keyed by a contract transaction and do not, by themselves, prove the visibility time of a contract modification.  
   Sources: [submission-history contract](https://github.com/fedspendingtransparency/usaspending-api/blob/03b9e2554837998c4c261c65e2947dc79f23855a/usaspending_api/api_contracts/contracts/v2/reporting/agencies/toptier_code/fiscal_year/fiscal_period/submission_history.md), [submission-history implementation](https://github.com/fedspendingtransparency/usaspending-api/blob/03b9e2554837998c4c261c65e2947dc79f23855a/usaspending_api/reporting/v2/views/submission_history.py).

3. The official monthly archive catalog is \`POST /api/v2/bulk_download/list_monthly_files/\`. Its contract returns \`file_name\`, \`updated_date\`, and \`url\` values. Its current implementation scans object names under agency/type prefixes, filters file names matching the dated \`*_Full_*.zip\` and \`*_Delta_*.zip\` patterns, and returns the matching names it found. It does not explicitly reduce those lists to one newest key in the listing code. This makes date-coded archive history a plausible *candidate source path*, not an established result: the runtime response, retention, archive row schema, and exact transaction presence must still be checked.  
   Sources: [monthly-files contract](https://github.com/fedspendingtransparency/usaspending-api/blob/03b9e2554837998c4c261c65e2947dc79f23855a/usaspending_api/api_contracts/contracts/v2/bulk_download/list_monthly_files.md), [monthly-files implementation](https://github.com/fedspendingtransparency/usaspending-api/blob/03b9e2554837998c4c261c65e2947dc79f23855a/usaspending_api/download/v2/list_monthly_downloads.py).

4. The API implementation that lists full database downloads explicitly selects the latest full and subset database file. That endpoint alone is not a historical version index.  
   Source: [database-download listing implementation](https://github.com/fedspendingtransparency/usaspending-api/blob/03b9e2554837998c4c261c65e2947dc79f23855a/usaspending_api/download/v2/list_database_downloads.py).

## New bounded probe in this PR

\`automation/q221_monthly_archive_inventory_probe.py\` reads only the fixed transaction keys already recorded in \`research/evidence/q221_historical_public_boundary_latest.json\`. It maps each key's action date to a federal fiscal-year archive partition (October starts the next fiscal year); that mapping is solely for locating files and explicitly is **not** a public-time estimate.

For each unique target fiscal year (maximum 10), the probe makes one read-only metadata POST to list contract archives for all agencies. Each request has a 30-second timeout and a 5 MB response ceiling. It validates dated file names and their \`updated_date\`, fingerprints raw catalog responses and target-key manifests, and writes a JSON receipt on success or failure. It does not download ZIP archives, read transaction payloads, place any orders, or alter repository evidence automatically.

The probe distinguishes:
- \`DATED_ARCHIVE_SERIES_FOUND\`: the catalog lists at least two different dated full archives for a target year or at least two different dated delta archives. This is only permission to investigate those files in a later bounded row-presence experiment.
- \`ARCHIVE_LISTING_OK_NO_VERSION_SERIES_FOUND\`: catalog calls worked, but no multi-date family was seen.
- \`ARCHIVE_LISTING_EMPTY\`, \`ARCHIVE_LISTING_INCOMPLETE\`, and invalid-manifest states: all fail closed.

A date-coded file name does not prove when that file first became publicly downloadable. Presence in a dated archive would at most anchor a *conservative known-available-by-snapshot* observation after file availability itself is verified; absence from a prior archive does not prove absence from the live API/UI. The event-level first-publication gate must remain negative through this inventory step.

## Execution / evidence state

The probe and its mock-based tests are added through this branch and PR. This session could inspect the upstream contract and implementation, but could not directly reach \`api.usaspending.gov\` from its local network environment (DNS lookup failed). Therefore, no live catalog response, archive retention claim, target-row presence result, or publication-time claim is made here. The included manual GitHub Actions workflow is read-only and uploads the receipt even on a fail-closed result, so the dynamic inventory can be collected on an authorized GitHub-hosted runner after review.

The latest capacity-dispatch receipt inspected for this task had \`active_research_job_count=7\` and \`planned_executable_count=0\`; no competing research run was started. Existing Q220 Run \`38155914188\` remains pending and is not retriggered.

## Unchanged research and safety gates

\`historical_first_public_observation_proven=false\`, \`event_level_public_boundary_proven=false\`, \`recipient_to_issuer_mapping_frozen=false\`, \`scientific_evidence=false\`, \`performance_authorization=false\`, \`holdout_selection=false\`, \`ranking=false\`, \`tuning=false\`, \`promotion=false\`, and \`live_execution=false\`. Q218 stays excluded from active dispatch; Q221 remains in the active focus set. No trading flags or research gates are changed.

## Next decision rule

Only if the live inventory exposes a genuinely versioned archive series should a second, separately reviewed bounded probe choose a small set of frozen transaction keys, download the minimum eligible dated archives, verify archive schema and hashes, and test row presence across versions. It must distinguish the archive's update date from its verified public availability, retain missing/ambiguous identities, and leave PIT and performance gates closed absent a defensible public-boundary contract.
