# Trading Agent — Code Review Policy

Code review is required for changes that can affect research validity, provenance, safety, resource governance, or workflow behavior.

| Change | Minimum review |
|---|---|
| Safety, performance authorization, holdout/PIT, evidence ledger | focused technical review + deterministic CI; high-risk changes stay fail-closed without independent approval |
| Research compiler / source parser / workflow | focused code review + targeted tests + relevant CI |
| Orchestration / resource routing / AI scheduler | focused review + contract tests + project-integrity checks |
| Documentation-only | normal CI/integrity checks |

AI review is an adversarial second reader, not scientific evidence, authorization, or sole approval.

A PR must not merge while an unresolved blocking technical finding remains.