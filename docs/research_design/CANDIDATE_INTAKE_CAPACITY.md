# Candidate intake and capacity disposition

## Purpose

Use one file to propose a new research hypothesis: `research/candidates/candidate_intake_queue.json`. The dashboard's deterministic planner validates each entry, flags duplicate IDs, checks the early robustness contract, and displays a content-fingerprinted disposition. No candidate-specific workflow or runner reservation is needed to propose an idea.

## Required entry fields

Every candidate needs:
- `id`: unique, stable project identifier;
- `name` and `hypothesis`: mechanism, with no assumed outcome direction;
- `construction`: fixed feature construction and a public-observation/PIT boundary;
- `sources`: source URLs or immutable source references;
- `next_gate`: the next cheap non-performance gate;
- `cheap_falsifiers`: concrete tests that could reject the mechanism;
- `gates`: source coverage, identity, revision, clock and independent PIT checks.

A candidate's source URLs are leads, not project evidence. The existing research-hypothesis compiler rejects forbidden outcome/selection fields and applies the universal pre-formal robustness gate.

## Automatic disposition

Queue order is FIFO; this tool does not rank by expected return. Invalid records, IDs that collide with project inventories, and duplicate queue IDs are blocked. A structurally valid proposal receives `VALIDATED_QUARANTINED_WAITING_FOR_FOCUS_RELEASE`, a full-contract fingerprint, and no resource assignment.

**Passing intake does not dispatch research.** The execution focus remains exactly Q104:I19, Q220 and Q221. A new idea needs a deliberate focus decision and a bounded, independent, receipt-defined task before the existing dispatcher can allocate capacity. Intake cannot authorize performance, holdout use, tuning, promotion, orders or live trading.

## No-waste rule

An empty queue costs zero compute. Invalid or duplicate candidates do not reach runners. Validating a proposal consumes no runner capacity. Once a proposal is explicitly admitted later, use the existing planned-capacity dispatcher and completion chaining; do not create artificial tasks, duplicate active work, or rerun successful work merely to fill a slot.

## Workflow

1. Add one candidate object to the queue file, in FIFO order.
2. The master-branch push triggers the dashboard refresh; the scheduled refresh is a recovery path.
3. Review status, reasons, input inventory fingerprints and plan fingerprint on the dashboard.
4. Only after an explicit focus decision should a candidate-specific, bounded workpack be defined and dispatched.
