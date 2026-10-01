# H06-P2 Sector-Residual Global Rank — Performance Design

Stand: 2026-10-01

## Status

**DESIGN-ONLY / NO PERFORMANCE AUTHORIZATION**

H06-P2 is a corrected successor design to the mathematically degenerate H06-P1 construction. It is not yet a preregistered or authorized performance trial.

## Research object

Trial family: H06-P2  
Parent: H06 sector-neutral residual momentum repair  
Predecessor: H06-P1 (design-blocked for treatment/control identity degeneracy)  
Universe: `validation_2026_09_25_sector_neutral_residual_momentum_repair`

The frozen H06 3,500-session snapshot and independently reconciled PIT contract remain the intended data source. No new data or asset selection is required at design stage.

## Fixed universe

Technology: TXN, ADI, AMAT  
Healthcare: MDT, SYK, BDX  
Industrials: ETN, ITW, GD  
Consumer Staples: CL, KMB, GIS  
Utilities: AEP, XEL, DTE

Total: 15 symbols.

## Fixed signal

Raw momentum:

`raw_i(t) = close_i[t-21] / close_i[t-252] - 1`

Sector-residual momentum:

`residual_i(t) = raw_i(t) - mean(raw_j(t) for j in i's fixed sector)`

### Treatment: H06-P2-RESIDUAL-GLOBAL-T5/B5

At each decision bar:
- rank all 15 symbols by residual score;
- long the 5 highest residual scores;
- short the 5 lowest residual scores;
- assign +0.10 to every long and -0.10 to every short;
- remaining 5 symbols receive 0.00.

### Control: H06-P2-RAW-GLOBAL-T5/B5

At each decision bar:
- rank all 15 symbols by raw momentum;
- long the 5 highest raw scores;
- short the 5 lowest raw scores;
- assign +0.10 to every long and -0.10 to every short;
- remaining 5 symbols receive 0.00.

Ties are resolved deterministically by ascending ticker symbol.

Both arms therefore have:
- 5 long positions;
- 5 short positions;
- gross exposure exactly 1.0;
- net exposure exactly 0.0;
- no leverage.

The portfolio is **not required to be sector-balanced**. Sector residualization is a signal transformation, not a portfolio-allocation constraint. This distinction is deliberate: imposing one long and one short inside every sector would recreate the H06-P1 degeneracy.

## Decision and execution timing

The signal is computed only from information available through decision bar t.

The target generated at t is applied on the next actionable session t+1.

No same-bar execution is allowed.

## Formal evaluation contract

Both arms must be evaluated symmetrically under the existing unchanged 13-gate framework.

Required outputs:
- research and holdout results;
- rolling-window diagnostics;
- cost/slippage stress;
- control-relative checks where applicable;
- deterministic report and immutable fingerprint.

Forbidden during the formal run:
- parameter search;
- threshold search;
- horizon search;
- asset search;
- sector-map search;
- variant search;
- holdout-based selection;
- post-hoc reweighting.

The 5/5 selection and 0.10 per-name weights are fixed ex ante and are not tuning axes.

## Provenance gates before any performance authorization

A future performance authorization must bind all of the following to the exact H06-P2 trial identity:
1. immutable H06 coverage receipt;
2. immutable independently reconciled H06 PIT receipt;
3. frozen input snapshot/bundle fingerprint;
4. H06-P2 preregistration fingerprint;
5. exact performance-runner source fingerprint;
6. active-registry authorization for the exact trial;
7. paper-only safety invariants.

Any mismatch is fail-closed and produces no scientific interpretation.

## Engineering gate

Before authorization, the repository must contain and pass:
- deterministic H06-P2 signal implementation;
- structural unit tests;
- mutation/PIT regression tests;
- deterministic ranking/tie handling tests;
- source/provenance readiness checks.

Only after these checks pass may a separate performance preregistration and one-shot authorization be created.

## Scientific rationale

The H06 mechanism-only evidence shows that sector residualization materially changed **global** cross-sectional geometry while preserving the ordering inside each sector. H06-P2 is constructed to test exactly that observable mechanism rather than an algebraically invariant proxy.

This design change is made before any holdout observation and therefore does not use performance outcomes to repair the candidate.
