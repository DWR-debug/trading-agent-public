# Q066 — Alpha Failure-Mechanism Diagnosis

Status: **COMPLETED_DIAGNOSTIC_ONLY**

This report reconstructs the fixed Q041/T060 and Q045/T065 return/exposure paths from immutable Actions artifacts. It does not perform parameter search, asset selection, new market-data acquisition, a new performance trial, or promotion.

## Executive summary

### Q041

- CONTROL: mean gross exposure=0.8623; mean HHI=0.2612; turnover sum=45.7226; base cost drag(simple)=0.068584.
- A1_TSM_CONSENSUS: mean gross exposure=0.8528; mean HHI=0.1980; turnover sum=674.7833; base cost drag(simple)=1.012175.
- A2_CS_MOMENTUM_TOP2: mean gross exposure=0.9220; mean HHI=0.4610; turnover sum=314.0000; base cost drag(simple)=0.471000.
- A3_RESIDUAL_MOMENTUM_TOP2: mean gross exposure=0.9160; mean HHI=0.4580; turnover sum=304.0000; base cost drag(simple)=0.456000.
- A5_LOW_BETA_TOP2: mean gross exposure=0.9160; mean HHI=0.4580; turnover sum=53.0000; base cost drag(simple)=0.079500.
- CONTROL underwater fraction=0.8756; worst 5% negative-loss share=0.2375.

### Q045

- CONTROL: mean gross exposure=0.8832; mean HHI=0.2705; turnover sum=50.1441; base cost drag(simple)=0.075216.
- A1_TSM_CONSENSUS: mean gross exposure=0.9145; mean HHI=0.2376; turnover sum=720.8667; base cost drag(simple)=1.081300.
- A2_CS_MOMENTUM_TOP2: mean gross exposure=0.9220; mean HHI=0.4610; turnover sum=256.0000; base cost drag(simple)=0.384000.
- A3_RESIDUAL_MOMENTUM_TOP2: mean gross exposure=0.9160; mean HHI=0.4580; turnover sum=285.0000; base cost drag(simple)=0.427500.
- A5_LOW_BETA_TOP2: mean gross exposure=0.9160; mean HHI=0.4580; turnover sum=46.0000; base cost drag(simple)=0.069000.
- A1B_52W_HIGH_TOP2: mean gross exposure=0.9220; mean HHI=0.4610; turnover sum=770.0000; base cost drag(simple)=1.155000.
- A6_OVERNIGHT_TUGWAR_TOP2: mean gross exposure=0.9940; mean HHI=0.4970; turnover sum=1092.0000; base cost drag(simple)=1.638000.
- ENSEMBLE_ALL6: mean gross exposure=0.9307; mean HHI=0.2407; turnover sum=481.4246; base cost drag(simple)=0.722137.
- CONTROL underwater fraction=0.8831; worst 5% negative-loss share=0.2188.

## Interpretation boundary

The diagnosis is descriptive. Shared exposure, overlap, correlation or turnover patterns are evidence about co-movement and transmission of risk, not proof of a causal driver.

## Reconstruction

- Q041 exact aggregate reconstruction: True
- Q045 exact aggregate reconstruction: True

## Governance

- New performance evaluation: false
- Selection/ranking: false
- Holdout used for selection: false
- Promotion: false
- Safety: paper-only; live trading disabled; orders disabled.
