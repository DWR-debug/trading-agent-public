# Ergebnis: Trial T-2026-09-24-029 — DATA_INVALID

## Status

**DATA_INVALID / NO_SCIENTIFIC_OUTCOME**

Trial 029 wurde nicht als Performance-Experiment gewertet, weil der
präregistrierte Datenvertrag vor dem Researchlauf nicht erfüllt werden konnte.

## Technischer Nachweis

- Workflow: `36039285580`
- Artifact: `10826146206`
- Artifact-SHA256: `sha256:652627afbe7ab0cb39d374d986a32d265c779d9f96b27f233d3b8108477fc036`
- angefordert: 3.500 Candles je Symbol
- 12 Symbole: jeweils 3.520 Candles
- IEFA: 3.496 Candles
- gemeinsamer Kalender: 3.496 statt 3.500
- Research und Holdout wurden **nicht** ausgeführt
- keine Rendite-/Drawdown-/PF-Evidenz aus diesem Trial

Der historische Unterschied ist im gespeicherten Artifact direkt sichtbar:
die zwölf übrigen Datensätze beginnen am 20.09.2012; IEFA beginnt am
24.10.2012 und hat dadurch vier fehlende Zielperioden.

## Governance-Entscheidung

- Target Count nicht gelockert;
- keine nachträgliche Symbolersetzung;
- kein Trimmen auf 3.496;
- kein Holdout verwendet;
- keine wissenschaftliche Performanceaussage;
- keine Promotion;
- keine Orders.

Trial 029 wird ausschließlich als Datenqualitätsfehler archiviert.

## Sicherheitsstatus

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
orders_enabled=False
