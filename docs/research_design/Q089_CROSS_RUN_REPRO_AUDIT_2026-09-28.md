# Q089 Cross-Runner Reproducibility Audit — 2026-09-28

Status: DESIGN / AUDIT-ONLY

The project now performs coverage on independent PC and cloud runners for the same fixed Q089 universe definition.

The audit intentionally separates three properties:

1. Selection agreement: identical fixed symbol batch.
2. Geometry agreement: identical common-calendar count and fixed study geometry.
3. Snapshot fingerprint agreement: byte-level equality of the downloaded source snapshot.

Selection and geometry agreement can be true while snapshot fingerprints differ. Such a difference is treated as source-snapshot variance, not silently normalized away.

No performance output, return label, holdout result, optimizer state or promotion decision is consumed.

The audit exists to make cross-run data differences explicit before any downstream PIT or performance evidence is accepted.
