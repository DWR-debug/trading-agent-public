# Evidence-Critic Lab

Purpose: evaluate typed-decision models as an isolated evidence-interpretation shadow layer.

First wave:
- GestaltLabs/Jeff-1
- convaiinnovations/laya-typed-decisions / Laya
- jaredpalmer/kev-0.8b

The frozen pilot corpus contains 36 balanced cases: 12 SUPPORTED, 12 REFUTED and 12 INSUFFICIENT. Cases are derived only from verified Q116/Q117 contracts and controlled semantic mutations.

Measured:
- accuracy;
- multiclass Brier score;
- ten-bin ECE;
- malformed/no-decision rate;
- median and p95 latency;
- option-order sensitivity.

The lab cannot authorize performance, ranking, holdout selection, promotion or live execution. Model output is operational research metadata only.

External model evidence is contextual, not project evidence. Jeff reports 0.8183 accuracy and 0.0807 ECE on its published fact-checking comparison; its own documentation also notes weaker insufficient-evidence handling and that it does not retrieve or independently verify sources. Laya reports 0.766 accuracy on its typed-decisions benchmark for the fine-tuned typed-decisions checkpoint and explicitly describes the base checkpoints as near-chance zero-shot on that suite. Kev publishes new-source accuracy and Brier results for its 0.8B/4B/9B family.

Project validity is determined only by the frozen corpus, reproducible receipts, and disagreement/error analysis on this repository.
