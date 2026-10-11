# Candidate intake and capacity disposition

## Purpose

This is the single, low-friction intake point for a new hypothesis. Add one candidate object to research/candidates/candidate_intake_queue.json; do not create a separate workflow, runner assignment, or ad-hoc candidate inventory for each idea.

The deterministic planner reuses the existing research-hypothesis compiler and universal pre-formal robustness gate. It checks schema, source list, a fixed/deterministic PIT boundary, cheap falsifiers and formalization gates, and detects duplicate candidate IDs against the maintained project inventories. It publishes the result on the Research Control Board.

## Candidate entry contract

Every entry must provide:
- id: unique project identifier;
- name and hypothesis: the mechanism and what it predicts, without assuming direction;
- construction: the deterministic feature and point-in-time/public-observation boundary;
- sources: source URLs or immutable project source references;
- next_gate: a cheap non-performance gate;
- cheap_falsifiers: at least one concrete falsifier;
- gates: the provenance, identity, revision and PIT checks needed before formal work.

Construction should explicitly state the relevant fixed/frozen/PIT/publication boundary. Existing forbidden outcome and selection fields are rejected by the research-hypothesis compiler.

## Automatic disposition

The planner creates a content-fingerprinted receipt and records each item in file order (FIFO; not by expected return). Invalid entries and duplicate IDs receive a blocked disposition. An entry that passes validation is marked VALIDATED_QUARANTINED_WAITING_FOR_FOCUS_RELEASE and is visible for triage, but still has dispatchable=false and no resource assignment.

This hard boundary is intentional: the active execution focus stays Q104:I19, Q220 and Q221. The intake tool cannot add a candidate to that allowlist, start a job, authorize performance/holdout use, tune or promote anything. An explicit later focus decision and a separate receipt-backed cheap-falsifier workpack are required.

## Useful-compute rule

An empty queue costs zero compute and is a valid state. An invalid or duplicate candidate is not sent to runners. Passing intake consumes no runner capacity. Only after a deliberate focus decision can the existing planned-capacity dispatcher consider a defined, independent, bounded task. There is no auto-repeat, padding, or outcome-based candidate ranking.

## Local validation

Run the candidate-intake unit tests and the existing CI/full-suite checks before merging any changes. The dashboard snapshot computes the intake plan from the queue and current inventories; the scheduled Resource Dashboard Update republishes the latest view.
