# Kostenoptimierte Research-Architektur

## Ziel

Das Projekt nutzt möglichst viel lokale Rechenleistung und möglichst wenig kostenpflichtige API-Intelligenz.

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

### Kostenfreie Agentenressourcen / gezielt

Kostenfreie Agentenressourcen werden bewusst **für Hypothesenbildung und Forschungsdesign** reserviert, nicht für deterministische Berechnung.

Geeignete Aufgaben:
- neue, orthogonale Hypothesen aus eingefrorener Evidenz ableiten;
- Gegenhypothesen und Falsifikationsbedingungen formulieren;
- Mechanismen und Literatur-/Domänenwissen synthetisieren;
- ungewöhnliche Ergebnisse interpretieren;
- Forschungsdesign und Präregistrierung kritisch reviewen.

Die bevorzugte Arbeitsweise ist: kompakte Evidence-Summaries an Agenten geben, mehrere unabhängige Hypothesen in einem gebündelten Lauf erzeugen und die gesamte numerische Prüfung anschließend lokal deterministisch ausführen.

### Bezahlte API

Projektseitig bleibt bezahlte Agenten-/API-Nutzung deaktiviert.

- paid_api_budget_usd = 0
- keine automatische bezahlte API-Nutzung
- kein automatisches Nachladen von Credits

Agentennutzung soll nur auf tatsächlich kostenfrei verfügbarem Kontingent erfolgen.

## Kosten-Governor

Kostenfreie Agentenläufe sind konzeptionell vom bezahlten Kosten-Governor getrennt. Ein kostenfreier Lauf darf nicht dazu führen, dass später automatisch kostenpflichtige Nutzung aktiviert wird.

Der bestehende bezahlte Governor bleibt unverändert und ist kein Ersatz für die Abrechnung des API-Anbieters.

## Effizienzprinzip

Nicht jede Forschungsaufgabe benötigt einen Agenten. Deterministische Rechenarbeit bleibt lokal.

Agenten werden dort eingesetzt, wo zusätzliche unabhängige Synthese, Gegenprüfung und Hypothesengenerierung einen Informationsgewinn erzeugt. Wiederholte Agentenaufrufe ohne neue Evidenz werden vermieden.

## Sicherheitsregeln
- PAPER_ONLY bleibt True.
- LIVE_TRADING_ENABLED bleibt False.
- Keine echten Trades.
- Keine API-Schlüssel in Repository-Dateien.
- Keine Forschungsergebnisse gelten als Profitabilitätsbeweis.
- Kostenlimits dürfen nicht automatisch erhöht werden.
- Agentenantworten sind Ideenmaterial und werden erst durch Präregistrierung und deterministische Evidenztestung wissenschaftlich relevant.
