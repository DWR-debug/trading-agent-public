# Q018 — Orthogonal Official Event-Source Design Round — 2026-09-26

## Status
**DESIGN_ONLY.** This round follows the Q017-G3 source-feasibility failure. It does not create performance evidence and does not authorize a performance trial.

## Purpose
Q017-G3 was DATA_INSUFFICIENT because its fixed ALFRED PIT retrieval was unreliable, historical CFTC publication timestamps were not fully certifiable, and the fixed Yahoo universe did not contain the required common history. Q018 therefore starts a fresh source-first design round rather than changing failed candidates opportunistically.

## Candidates

### A — SEC insider-flow event
Source: SEC EDGAR Form 4. Fixed signal: issuer-day Table I transaction-count imbalance, P=+1 and S=-1. PIT anchor: EDGAR ACCEPTANCE-DATETIME; action no earlier than the next eligible trading bar.

### B — FOMC policy-decision event
Source: official Federal Reserve FOMC statements/calendars. Fixed signal: +1 / -1 / 0 from the change in the target federal-funds-rate range midpoint. PIT anchor: official release date; action no earlier than the next eligible trading bar.

### C — Treasury 10-year auction-demand event
Source: official TreasuryDirect auction results. Fixed signal: sign of the change in bid-to-cover ratio versus the immediately preceding 10-year note auction. PIT anchor: official publication date; action no earlier than the next eligible trading bar.

## Fixed validation universe
UNH, UPS, FDX, DIS, ADP, BKNG, ORLY, AZO, TJX, RSG, WM, EOG.

## Governance
No candidate ranking. No holdout selection. No parameter, asset, feature, threshold, or horizon search. Coverage and PIT verification precede any performance preregistration. Coverage success does not imply a positive trading result.

## Next step
Run a deterministic source-feasibility preflight for A/B/C. Candidates that fail the source contract are recorded as DATA_INSUFFICIENT and closed without rescue tuning.
