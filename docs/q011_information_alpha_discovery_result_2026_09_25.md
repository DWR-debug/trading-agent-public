# Q011 Discovery Result — 2026-09-25

## Formal result

Q-011-ORTHOGONAL-INFORMATION-ALPHA-DISCOVERY completed as a discovery-only run.

- Workflow run: 36121684164
- Authorization commit: 3587fde89ba5a2cc9d4a2c83de3ca84c59c484e8
- Artifact ID: 10857762336
- Artifact digest: sha256:0810dc6f9f9ca0fdd2435c4fccf7845667b0bd2929e45bceecfd923b23dcee1f
- Report fingerprint: 08664ed668b61a2e149067cbe10c281f73d27b0b94ed50372877ab1203e97da8
- Corrected JSON SHA256: e2dbe92f2e16bfb3079eceac42b1180b5fd152a47090043935459950693f76d9
- Full test suite: passed
- Paper-only safety: passed

## Fixed design

- Dates: 2026-08-24 through 2026-09-24
- Assets: SPY, TLT, GLD
- Information source: GDELT 2.0 Event export
- Filter: international event with num_articles >= 3
- Features: event count, attention score, source breadth, article count, negative Goldstein magnitude, mean tone
- Point-in-time rule: previous market day < event day < target market day
- Same-day return usage: false
- Parameter / threshold / asset / holdout selection: false

## Data coverage

- 22 common market-day observations
- 4 event windows
- 18 no-event windows
- 3,208,523 GDELT event rows seen
- 24 rows skipped by the parser

## Descriptive findings

1-day Pearson correlations:

| Feature | SPY | TLT | GLD |
| --- | ---: | ---: | ---: |
| Event count | -0.039 | +0.163 | -0.250 |
| Attention score | -0.034 | +0.165 | -0.249 |
| Source breadth | -0.051 | +0.166 | -0.258 |
| Article count | -0.059 | +0.156 | -0.251 |
| Negative Goldstein | -0.029 | +0.168 | -0.248 |
| Mean tone | -0.006 | -0.143 | +0.196 |

5-day Pearson correlations:

| Feature | SPY | TLT | GLD |
| --- | ---: | ---: | ---: |
| Event count | -0.013 | +0.074 | +0.150 |
| Attention score | -0.010 | +0.078 | +0.151 |
| Source breadth | +0.017 | +0.093 | +0.171 |
| Article count | +0.003 | +0.090 | +0.157 |
| Negative Goldstein | +0.001 | +0.089 | +0.156 |
| Mean tone | +0.024 | -0.113 | -0.103 |

Event-window versus no-event next-day mean return:

| Asset | Event window | No event window |
| --- | ---: | ---: |
| SPY | +0.064% | +0.029% |
| TLT | +0.076% | -0.208% |
| GLD | -1.008% | -0.239% |

These are descriptive relationships only. With 22 observations and only four event windows, the result does not establish a stable cross-asset information effect and does not select a trading feature.

## Interpretation

The signal picture is asset- and horizon-dependent. SPY is near zero; TLT shows modest positive association for event-intensity features over one day; GLD changes sign between the one-day and five-day horizons. No pre-registered cross-asset selection criterion exists, so no feature is promoted from this result.

The appropriate next step is to test temporal stability of the information source over a materially longer fixed historical window, using the same feature definitions and no post-hoc feature selection. Only a stable discovery should be considered for a separately preregistered performance trial.

## Serialization note

The run artifact contained a literal escaped newline after the JSON object. This was a transport/serialization defect only. The JSON object, embedded fingerprint and all scientific fields were intact. The defect was repaired losslessly by removing the trailing two-character literal sequence; the embedded report fingerprint remained exactly 08664ed668b61a2e149067cbe10c281f73d27b0b94ed50372877ab1203e97da8.

The production serializer was corrected in commit d2351beb0e6edc22afc709055cc8beae0cf2923d and protected by a JSON reload regression test.

## Non-actions

No parameter search, threshold search, asset selection, holdout selection, performance rerun, promotion, or live execution was performed.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
orders_enabled=False  
automatic_promotion=False
