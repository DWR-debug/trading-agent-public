# Candidate next-gate six-runner wave — 2026-10-14

## Scope

This is a bounded, non-authorizing research/engineering wave on the canonical public repository. It routes independent work to the configured three Windows self-hosted slots and the three GitHub-hosted architectures (Ubuntu x64, Ubuntu ARM64, Windows). Actual names and execution status are recorded by each job, not inferred from configuration.

## Six independent slots

| Slot | Workpack | Purpose |
|---|---|---|
| Windows A/B | Q104 R3 DATE-OF-FILING-DATE-CHANGE header capture | Re-read only 18 official EDGAR header routes for the six frozen 2016-Q4 accessions whose R3 receipt did not retain the field |
| Windows A/B | Q221 transaction-probe failure audit | Verify the immutable HTTP 503 receipt failed before preflight count/data download; explicitly prohibit identical retry |
| Windows C | Q220 offline hash-lineage diagnostic | Compare existing frozen reports and two small immutable artifacts; no SEC source calls |
| GitHub Ubuntu x64 | Q104 cross-vintage aggregation | Combine six R3 rows with the previously pinned eight-row R1/R2 date-change probe, without applying a policy |
| GitHub ARM64 | Q220 independent reproduction | Recompute the offline Q220 diagnostic and require the same deterministic analysis fingerprint |
| GitHub Windows | Q104 independent reproduction | Recompute the 14-row Q104 aggregate and require the same deterministic analysis fingerprint |

The two jobs using the common Windows research label are independent. If only one shared-label runner is online, GitHub queues the second job instead of allowing concurrent work on one listener. Runner C uses its dedicated trading-agent-long label.

## Expected information gain

- Q104: establishes whether the six already identified 2016-Q4 bulk/header filing-date mismatches have observable and internally consistent DATE-OF-FILING-DATE-CHANGE metadata. Missing metadata is recorded as missing, not interpreted as proof of absence.
- Q220: preserves and contrasts the frozen expected hash, prior compiler observation, earlier response observation, and later bounded response for one fixed key. Identical URL/Last-Modified metadata with distinct response hashes is recorded as an unresolved provenance conflict, not as proof of why the body changed.
- Q221: documents a terminal, bounded HTTP 503 at the transaction-count preflight. A separate audit-trigger snapshot freezes the exact request timestamp and identity pins used by that failed run; this avoids accidentally validating the old failure against a later active request revision. It does not repeat the endpoint, download transaction data, infer a parent mapping, or claim a historical public clock.

## Safety and audit

Every output is fingerprinted and records its immutable upstream pins. Cross-architecture jobs compare a deterministic analysis_fingerprint, excluding generation time. The wave does not modify frozen inputs, expected hashes, accession identities, source receipts, candidate definitions, threshold values, or any research gate. It has no performance, holdout-selection, ranking, tuning, promotion, orders, or live-execution authority.

## Completion criteria

A job success means only the stated bounded diagnostic/reproduction completed and its input fingerprints matched. It does not imply Q104:I19, Q220, or Q221 is gate-positive or authorized. Runner occupancy is accepted only when the job completes on a named runner; queued jobs are not counted as used capacity.
