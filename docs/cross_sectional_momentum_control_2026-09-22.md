# Cross-Sectional-Momentum-Control — 2026-09-22

## Motivation

Die bisherige neue Evidenz zeigt mittel-/langfristige Trendstabilität auf
Einzelasset- und Portfolioebene. Cross-Sectional Momentum ist eine davon
getrennte, klassisch untersuchte Mechanik: relative Gewinner und Verlierer
werden aus den vergangenen Renditen der Aktien untereinander gebildet.

Jegadeesh und Titman dokumentieren positive Momentum-Erträge bei Portfolios, die
Aktien mit hohen vergangenen Renditen kaufen und Aktien mit niedrigen
vergangenen Renditen verkaufen; die untersuchten Bildungshorizonte liegen
zwischen 3 und 12 Monaten. citeturn484066search0turn484066search2

Spätere internationale Evidenz verwendet typischerweise eine 12-Monats-
Formation mit Ausschluss des letzten Monats. citeturn484066search1turn484066search3

## Kontrollhypothesen

Es werden ohne Optimierung vier aktive Varianten geprüft:

- 6-1, Long-only, Top 2
- 12-1, Long-only, Top 2
- 6-1, Long/Short, Top 2 gegen Bottom 2
- 12-1, Long/Short, Top 2 gegen Bottom 2

Als passive Referenz dient ein gleichgewichtetes Buy-and-Hold-Portfolio.

Alle Regeln sind vorab fixiert:
- Skip: 21 Handelssitzungen
- Rebalance: alle 21 Handelssitzungen
- Top-N: 2
- Long/Short: 50 Prozent Long und 50 Prozent Short, jeweils gleichgewichtet
- Close(t) → Open(t+1) → Open(t+2)
- 0,10 Prozent Gebühr + 0,05 Prozent Slippage je Turnover-Einheit

## Daten

Verwendet wird das frische, bereits archivierte
small_cap_high_volatility-Universum aus Workflow Run 35778876546:

SOUN, RKLB, IONQ, ASTS, HIMS.

Jeder Datensatz enthält genau 1.000 tägliche Candles und endet am 21. September
2026. Die Daten und das Manifest werden aus dem unveränderlichen Workflow-
Artifact geladen und per Fingerprint geprüft.

## Stichprobenbegrenzung

Der Control ist bewusst explorativ:

- 800 Research-Candles
- 200 Holdout-Candles
- 5 Rolling-Testfenster innerhalb des Research-Abschnitts

Die Stichprobe ist zu klein, um aus einem positiven Resultat bereits einen
Produktions-Edge abzuleiten. Ein positives Resultat dient ausschließlich als
Begründung für einen größeren, unabhängig archivierten Replikationslauf.

## Vorab definierte Interpretation

Ein positiver Befund wird nur als Forschungs-Signal gewertet, wenn er:

1. auf mehreren Rolling-Fenstern stabil bleibt,
2. im Holdout ebenfalls positiv ist,
3. nach den festgelegten Kosten positiv bleibt,
4. nicht nur durch eine einzelne Aktie getragen wird.

Kein automatischer Befund dieses Controls verändert:
- Produktionsstrategie
- Parameterraum
- Selection-Profile
- Gate-Schwellen
- Live-/Paper-Trading-Konfiguration

## Sicherheit

Paper-Only bleibt aktiv.
Live-Trading bleibt deaktiviert.
Im Research werden keine Orders erzeugt.
