# Kostenoptimierte Research-Architektur

## Ziel

Das Projekt nutzt möglichst viel lokale Rechenleistung und möglichst wenig
kostenpflichtige API-Intelligenz.

### Lokal / ohne API

- Datenimport und UTC-Normalisierung
- Datenqualität
- Backtests
- Parameter-Sweeps
- Optimierung
- Walk-Forward und Rolling Walk-Forward
- Robustheits- und Overfit-Tests
- Metriken
- Caching
- Ergebnisaggregation
- Checkpoints und Reports
- pytest / CI

### API / Codex nur gezielt

- Forschungsfrage aus bereits berechneten Ergebnissen ableiten
- Ergebnisse interpretieren
- Codeänderungen planen oder reviewen
- nächste Forschungsrunde bestimmen
- ungewöhnliche Ergebnisse untersuchen

Die API erhält bevorzugt kompakte Ergebnis-Summaries statt Rohdaten,
Trade-Listen oder vollständiger Backtest-Ausgaben.

## Kosten-Governor

Die erste freigegebene API-Reserve beträgt **1,00 USD**.

Standardgrenzen:

- maximal 0,25 USD geschätzte API-Kosten pro Forschungsrunde
- maximal 4 kostenpflichtige Forschungsrunden innerhalb der Reserve
- keine automatische Nutzung des restlichen 9-USD-Guthabens

Der Governor ist ein Sicherheits-/Planungsgate und kein Ersatz für die
Abrechnung des API-Anbieters. Tatsächliche Kosten werden ausschließlich
über die OpenAI-Abrechnung verifiziert.

Der Governor zählt genehmigte Forschungsrunden zustandsbehaftet. Nach vier
genehmigten Runden werden weitere Runden abgelehnt, auch wenn ein Aufrufer
versehentlich einen zu niedrigen bisherigen Kostenstand übergibt. Ablehnungen
verbrauchen keine Runde. Nicht-endliche oder negative Kostenwerte werden
abgelehnt.

## Hardware

Ein lokaler Research-Worker soll bevorzugt auf einem verfügbaren PC laufen.
Ein Android/Termux-Gerät kann für kleinere Jobs, Tests, Datenaufbereitung
und als Kontroll-/Git-Client genutzt werden.

Die lokale Maschine soll keine API-Schlüssel für deterministische
Backtests benötigen.

## Sicherheitsregeln

- PAPER_ONLY bleibt True.
- LIVE_TRADING_ENABLED bleibt False.
- Keine echten Trades.
- Keine API-Schlüssel in Repository-Dateien.
- Keine Forschungsergebnisse gelten als Profitabilitätsbeweis.
- Kostenlimits dürfen nicht automatisch erhöht werden.


## Kostenfreie Agentenressourcen — Hypothesen zuerst (2026-09-25)

Die gemeinsame Arbeitsabsprache wird dauerhaft als Research-Regel geführt:

**Kostenfreie Agentencredits werden primär für Hypothesenbildung, Gegenhypothesen, Mechanismensynthese und Forschungsdesign verwendet.** Deterministische Berechnung bleibt lokal. Bezahlte Agenten-/API-Nutzung bleibt deaktiviert.

Die bevorzugte Nutzung ist ein gebündelter Agentenlauf mit mehreren unabhängigen Denk-Linsen und kompakten, eingefrorenen Evidence-Summaries. Agentenoutput ist Ideenmaterial und wird erst nach Präregistrierung, Coverage-Preflight und deterministischer Evidenztestung wissenschaftlich relevant.
