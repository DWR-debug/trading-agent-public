# F2 Quality Acceleration — 2026-09-28

Status: DESIGN / SOURCE-PIT FEASIBILITY ONLY

F2 extends gross profitability into a second-difference signal:

quality level = (Revenue - COGS) / Assets

quality growth = level_t - level_t-1

quality acceleration = growth_t - growth_t-1

Every observation is bound to the exact SEC accession, report date, and EDGAR acceptance chronology. The implementation does not rank assets for performance and does not access holdout outcomes.

The idea is motivated by published evidence that a quality-acceleration measure can contain incremental information beyond quality level and quality growth. That literature is an external motivation only; it is not project evidence.

Required gates before any future performance study:
- source accessibility;
- deterministic filing identity;
- exact accession/report-date fact matching;
- at least three sequential complete annual observations;
- future-filing mutation invariance;
- fresh symbol-disjoint coverage for performance;
- immutable provenance;
- preregistration;
- separate one-shot authorization.

No parameter, asset, threshold, horizon, variant, or holdout selection is introduced in this stage.
