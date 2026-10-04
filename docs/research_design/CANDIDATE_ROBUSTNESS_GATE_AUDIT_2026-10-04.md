# Candidate Robustness Gate Audit — 2026-10-04

## Finding

Issue #1001 identified a schema mismatch: the universal robustness gate requires `id`, `name`, `hypothesis`, `construction`, `sources`, and `next_gate`, while Q133–Q170 inventories omitted `hypothesis` and `construction`, and Q171–Q178 used `core_hypothesis` instead of `hypothesis`.

## Remediation

The gate implementation is not weakened. The missing fields are restored from already committed candidate design documents and mechanistic definitions. No return metric, ranking, parameter choice, holdout result or promotion outcome is used to construct these fields.

Q179–Q184 already satisfy the required pre-formal schema and are included in the same non-authorizing pre-formal gate. Inclusion in this gate does not authorize any formal phase.

The executable audit is `tests/test_candidate_inventory_schema.py`, supplemented by the existing gate tests.

## Required invariants

- all governed frontier candidates have the exact required pre-formal fields;
- no legacy `core_hypothesis` alias remains;
- no authorizing/performance fields are admitted;
- the gate remains non-performance and non-authorizing;
- Q179–Q184 remain source/PIT discovery-only.
