# Q090 — Q089 Failure-Mechanism Diagnosis

Status: COMPLETED_DIAGNOSTIC_ONLY

Immutable-result reconstruction only; no new market data, candidate selection, parameter search, new performance trial or promotion.

## Executive summary

| Arm | Q089 gates | Research DD | Holdout return | Holdout DD | Rolling positive windows | Rolling avg DD | Mean HHI | Mean top-2 share | Turnover sum |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C7_LOW_MAX_21 | 4/13 | 28.94% | -6.83% | 18.32% | 80% | 21.38% | 0.4970 | 0.9940 | 591.00 |
| C8_LOW_IDIO_VOL_273 | 8/13 | 29.08% | 23.75% | 19.23% | 100% | 18.51% | 0.4610 | 0.9220 | 58.00 |
| C9_LONG_TERM_REVERSAL_756 | 4/13 | 26.23% | -6.13% | 33.27% | 60% | 17.87% | 0.3919 | 0.7839 | 196.00 |
| C10_TREND_EFFICIENCY_63 | 3/13 | 50.37% | -31.79% | 45.19% | 80% | 25.34% | 0.4910 | 0.9820 | 975.00 |
| C11_VOLUME_CONFIRMED_TREND_126 | 9/13 | 56.20% | 36.06% | 15.81% | 80% | 27.94% | 0.4791 | 0.9583 | 519.00 |


## Interpretation boundary

Findings are descriptive decompositions, not causal proof or arm selection.
- Exact aggregate reconstruction: True
- Parent report fingerprint: 0eee84e44a12b9f4a606aebb63afe50990dfa0f6e6009afcf926f525e3c8e8d1
- Snapshot fingerprint: bb82aeaed86411a8675be7f8ecb1c99e9c144f017466a836b8cafeb9d3b55e1d

## C7_LOW_MAX_21

- Worst drawdown: 2015-01-26 14:30:00+00:00 to 2016-10-28 13:30:00+00:00 (446 days), 28.94%.
- Mean/max HHI: 0.4970/0.5000.
- Mean top-1/top-2 share: 0.4970/0.9940.
- Turnover sum / simple base-cost drag: 591.00/0.886500

## C8_LOW_IDIO_VOL_273

- Worst drawdown: 2020-02-19 14:30:00+00:00 to 2020-03-24 13:30:00+00:00 (25 days), 29.08%.
- Mean/max HHI: 0.4610/0.5000.
- Mean top-1/top-2 share: 0.4610/0.9220.
- Turnover sum / simple base-cost drag: 58.00/0.087000

## C9_LONG_TERM_REVERSAL_756

- Worst drawdown: 2024-10-01 13:30:00+00:00 to 2025-04-09 13:30:00+00:00 (131 days), 33.27%.
- Mean/max HHI: 0.3919/0.5000.
- Mean top-1/top-2 share: 0.3919/0.7839.
- Turnover sum / simple base-cost drag: 196.00/0.294000

## C10_TREND_EFFICIENCY_63

- Worst drawdown: 2015-07-15 13:30:00+00:00 to 2020-03-19 13:30:00+00:00 (1179 days), 50.37%.
- Mean/max HHI: 0.4910/0.5000.
- Mean top-1/top-2 share: 0.4910/0.9820.
- Turnover sum / simple base-cost drag: 975.00/1.462500

## C11_VOLUME_CONFIRMED_TREND_126

- Worst drawdown: 2019-03-28 13:30:00+00:00 to 2020-05-04 13:30:00+00:00 (278 days), 56.20%.
- Mean/max HHI: 0.4791/0.5000.
- Mean top-1/top-2 share: 0.4791/0.9583.
- Turnover sum / simple base-cost drag: 519.00/0.778500

## Governance

Diagnostic only. No selection, tuning, new performance trial or promotion.
Safety remains paper-only.
