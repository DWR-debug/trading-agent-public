# Trading Agent — Research Architecture 2026-09-24

## Pipeline

Data -> Alpha Sleeves -> Event/Macro Context -> Evidence/Confidence ->
Portfolio Allocation -> Risk Overlay -> Execution Simulation -> Paper Portfolio ->
Monitoring -> Research Feedback.

## Controls

- Fail-closed strategy lifecycle and Research Graveyard.
- Adversarial diagnostics for latency, costs, outliers and sign permutations.
- Champion/Challenger evidence contract without autonomous promotion.
- Portfolio overlay for realized volatility, correlation, concentration, drawdown
  and joint-loss periods.
- Point-in-time GDELT Event parser and Trial 017 baseline.
- Existing Trial Ledger, immutable manifests, disjoint validation and safety gates
  remain authoritative.

Leverage and short exposure remain downstream exposure variants. They cannot
repair a missing or unstable alpha source.
