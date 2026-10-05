# Trading Agent Build Track — Start Now, Promote Later

Status: active engineering track, non-authorizing.

## Decision

The Trading Agent should be built now, in parallel with research. The build target is the candidate-neutral runtime and paper/forward integration layer, not a strategy optimizer and not a live execution system.

The current repository already contains the core paper/shadow/forward infrastructure, the paper broker, the risk controller, the execution guard and a bounded agent-control plane. This build track connects those components behind explicit contracts so that a scientifically validated candidate can be evaluated without a second engineering project.

## Boundary

The runtime must never:

- select candidates;
- rank trials;
- search parameters, assets, thresholds or horizons;
- choose or modify holdouts;
- authorize performance;
- promote a strategy;
- submit live orders.

Global safety remains:

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
ORDERS_ENABLED=False  
AUTOMATIC_PROMOTION=False

AI agents remain hypothesis/design/review tools only. They cannot become evidence or authorization.

## Build sequence

### 1. Candidate-neutral decision shell — in progress

`agent/runtime.py` is now the first implementation.

It accepts one explicitly frozen candidate, validates the safety/cost contract and closed-candle observation ordering, calls an injected fixed signal adapter and returns an immutable decision envelope. The runtime intentionally has no live-execution method.

### 2. Deterministic paper execution adapter

Next, expose the existing `PaperBroker`, `PortfolioRiskController` and `ResearchExecutionCostContract` through one candidate-neutral adapter.

The adapter must enforce the existing global limits and the research execution-cost contract before any simulated fill. It must write no research evidence and must not mutate the research registry.

### 3. Replayable agent state

Add a versioned agent state envelope with:

- candidate contract fingerprint;
- observation/input fingerprint;
- decision fingerprint;
- paper account state;
- risk state;
- last accepted closed-candle timestamp;
- deterministic replay metadata.

A replay of identical inputs must reproduce the same state transition and fingerprints.

### 4. Paper-forward integration

Use the existing closed-candle feed and persistent MTM ledger as the operational observation/state path. Research candidates become pluggable only through an explicitly frozen candidate artifact.

No current frontier candidate is promoted into this path merely because source/PIT readiness improves.

### 5. Production boundary — deliberately postponed

A broker interface may eventually exist as an architectural seam, but the current implementation must remain a hard-disabled no-op boundary. Any future live capability requires a separate explicit safety and governance program; it is not part of this build track.

## Research acceleration enabled by the build

Building the runtime now removes future engineering latency from the critical path. At the same time, research should be accelerated by:

1. parallel candidate-specific historical PIT reconstruction whenever the source contract permits;
2. using Runner C for genuinely long deterministic archive/reproduction work;
3. keeping A/B on separate fast readiness/frontier lanes;
4. using hosted x64 workers aggressively for independent source probes and compilers;
5. reusing immutable source snapshots across candidates only when the exact source contract is shared;
6. running cheap falsifiers before expensive reconstruction;
7. immediately scheduling the predeclared independent reproduction after any complete formal pass;
8. keeping AI review asynchronous and non-authorizing.

A later engineering optimization can batch compatible evidence publications into fewer master commits. That is an operational optimization only; it must not merge distinct receipts or alter immutable content.

## Definition of ready

The agent build reaches the next engineering milestone when a frozen candidate can execute this path deterministically:

`frozen candidate -> closed observations -> fixed signal adapter -> risk checks -> paper execution -> persistent MTM state -> replay/receipt validation`

without any candidate selection or research-gate mutation.

The research program remains the scientific authority. The Agent is the execution/observability shell.

