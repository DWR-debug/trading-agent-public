# Trading Agent — Code Review Policy

Code review is required for changes that can affect research validity, provenance, safety, resource governance, or workflow behavior.

## Review levels

| Change | Minimum review |
|---|---|
| Safety, performance authorization, holdout/PIT, evidence ledger | independent technical review + deterministic CI; never merge on AI output alone |
| Research compiler / source parser / workflow | focused code review + targeted tests + full relevant CI |
| Orchestration / resource routing / AI scheduler | focused review + contract tests + project-integrity checks |
| Mechanical documentation-only change | CI/integrity checks; review as needed |

## Required reviewer checks

Reviewers verify scope, deterministic behavior, error handling, provenance/fingerprints, mutation/future-data resistance, resource bounds, secrets/permissions, and that no gate or safety invariant is weakened.

AI review is useful as an adversarial second reader, but AI output is not approval, scientific evidence, or authorization.

## Merge rule

A PR may merge only when its applicable CI and governance checks pass and no unresolved blocking review finding remains. When an external reviewer is unavailable, the orchestrator performs the technical review and records concrete findings; high-risk scientific/safety changes remain fail-closed rather than being treated as approved merely because CI is green.