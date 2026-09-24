## Neue Forschungsphase 2026-09-24

Schwerpunkt ist jetzt ein modularer Forschungsstack:
Research Lifecycle -> orthogonale Alpha-Familien -> Event/Macro Context ->
Portfolio Allocation -> Risk Overlay -> Execution Simulation -> Paper Monitoring.

Pflichtbausteine dieser Phase:
- reproduzierbare Research-Queue und Graveyard
- adversarial robustness
- Champion/Challenger
- Korrelation und Drawdown-Kopplung
- realistische Kosten-/Latenztests
- point-in-time Event Intelligence
- erst danach experimentelle Long/Short- und Leverage-Exposure

# Trading Agent – Ziele und Maßnahmen

## Hauptziel

Ein dauerhaft reproduzierbarer Forschungs- und Entwicklungsprozess für
einen Trading-Agenten, der ausschließlich simuliert arbeitet und nur dann
als Kandidat für weitere Prüfung gilt, wenn er über mehrere unabhängige
Tests hinweg robust erscheint.

Das Ziel ist nicht, kurzfristig einen einzelnen guten Backtest zu finden,
sondern belastbare, reproduzierbare und möglichst robuste Strategien zu
identifizieren und schlechte oder überangepasste Hypothesen systematisch
auszusortieren.

## Qualitätsprinzipien

Jede Forschungsbehauptung muss auf reproduzierbaren Experimenten beruhen.

Zu prüfen sind insbesondere:

- Out-of-sample-Ergebnisse
- Walk-Forward / Rolling Walk-Forward
- verschiedene Marktphasen
- Parameterstabilität
- Sensitivität gegenüber Gebühren und Slippage
- ausreichende Trade-Anzahl
- Drawdown und Verlustrisiken
- Robustheit gegenüber kleinen Parameteränderungen
- Trennung von Entwicklungs- und Evaluierungsdaten
- Overfit-/Data-Snooping-Risiken

Ein positives Ergebnis in einem einzelnen Backtest reicht nicht als
Freigabekriterium.

## Forschungsprozess

1. Datenqualität sicherstellen.
2. Hypothese definieren.
3. Baseline messen.
4. Parameterraum kontrolliert untersuchen.
5. Out-of-sample validieren.
6. Walk-Forward prüfen.
7. Robustheit untersuchen.
8. Ergebnisse dokumentieren.
9. Hypothese akzeptieren, verwerfen oder neu formulieren.
10. Nächsten Forschungsschritt aus den Ergebnissen ableiten.

## Kontrollierte Autonomie

Der Agent darf die Reihenfolge und Tiefe der Forschungszweige selbst
optimieren, solange die Sicherheits- und Qualitätsregeln unverändert
bleiben.

Ein Forschungspfad darf automatisch beendet werden, wenn er z. B.
instabil, stark überangepasst oder nicht reproduzierbar erscheint.

## Entwicklungs-Gates

Gate A – Infrastruktur:
GitHub, CI und Codex-Ausführung funktionieren.

Gate B – Testqualität:
Vollständige Testsuite grün.

Gate C – Sicherheitsprüfung:
PAPER_ONLY=True und LIVE_TRADING_ENABLED=False.

Gate D – reproduzierbare Forschung:
Experimente erzeugen nachvollziehbare Ergebnisse und Checkpoints.

Gate E – robuste Kandidaten:
Mehrere unabhängige Validierungen bestehen.

Kein Gate erlaubt den Übergang zu Live-Trading.

## Artefakte

Wichtige Projektinformationen sollen im Repository gespeichert werden:

- Code
- Tests
- Agent-Aufträge
- CI-Workflows
- Forschungsaufträge
- Ergebnisberichte
- Checkpoints
- Logs
- Wiederherstellungsinformationen

## Aktueller Blocker

Der Codex-Smoke-Test erreichte Codex erfolgreich, wurde aber vor der
eigentlichen Analyse wegen fehlender API-Credits beendet.

Nach Wiederherstellung des Guthabens wird der Smoke-Test erneut gestartet.


## Kosten- und Rechenstrategie

1. Deterministische Berechnungen lokal ausführen.
2. API nur für Forschungsplanung, Analyse und gezielte Codearbeit einsetzen.
3. Ergebnisse vor einer API-Analyse kompakt aggregieren.
4. Wiederholte Experimente über Version/Parameter/Data-ID vermeiden.
5. API-Reserve zunächst auf 1,00 USD begrenzen; pro Forschungsrunde maximal 0,25 USD geschätzt.
6. PC als self-hosted Research Worker verwenden, sobald der Runner eingerichtet ist.
7. Keine automatische Budgeterhöhung.
