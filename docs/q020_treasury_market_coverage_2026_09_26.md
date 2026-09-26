# Q020 — Treasury Market Coverage Gate — 2026-09-26

**Status: PREREGISTERED_COVERAGE_ONLY**

Q020 prüft ausschließlich, ob das bereits fixierte Q018-Universum genügend kanonische OHLCV-Coverage für einen späteren formalen Performance-Test besitzt.

## Fixed contract

- Universe: `UNH, UPS, FDX, DIS, ADP, BKNG, ORLY, AZO, TJX, RSG, WM, EOG`
- Study window: 2011-01-01 bis 2025-09-24
- requested candles: 3520
- required common calendar: 3500

## Decision rule

Der kanonische Datenlayer muss mindestens 3500 gemeinsame Candles liefern. Bei Nichterfüllung wird `DATA_INSUFFICIENT` dokumentiert. Assets, Signalregel oder Sample-Geometrie werden nicht verändert.

Q020 berechnet weder Renditen noch P&L, verwendet keinen Holdout und autorisiert kein Performance-Trial.
