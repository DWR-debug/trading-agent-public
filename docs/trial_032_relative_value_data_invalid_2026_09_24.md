# Trial 032 — DATA_INVALID — Relative-Value ETF Pairs

## Status

**DATA_INVALID — keine Performanceauswertung**

Der Coverage-Preflight für den vorgesehenen Relative-Value-Trial wurde vor
jeder Research-/Holdout-Auswertung beendet.

## Nachweis

- Coverage-Workflow: `36043628557`
- Ziel je Symbol: 3.520 Daily-Candles
- QQQM: nur 1.493 Candles
- Performanceauswertung: **nicht durchgeführt**
- Holdout-Auswertung: **nicht durchgeführt**
- keine Parameter-/Threshold-/Pair-Auswahl auf Basis von Performance
- Paper-only

## Konsequenz

Der Datenvertrag wird nicht gelockert und QQQM wird nicht künstlich aufgefüllt.
Trial 032 wird als DATA_INVALID archiviert.

Für den nächsten Preflight wird ausschließlich der historische Abdeckungsfehler
bereinigt: QQQM wird durch QQEW ersetzt, ein länger historisches Nasdaq-ETF.
Alle übrigen vorgesehenen Paare bleiben unverändert.

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`
