# Failure-/Risk-Diagnose 2026-09-23

## Zweck

Dieser Control diagnostiziert ausschließlich die bereits abgeschlossene zweite
unabhängige Validierung. Er verwendet das unveränderte Validation-Artifact
10740188093 einschließlich der darin archivierten 13 ETF-Datensätze.

Es werden keine neuen Assets ausgewählt, keine Parameter verändert, keine
Sleeve-Gewichte verändert und keine Gates angepasst.

## Diagnoseachsen

1. Zerlegung der fünf festen Research-Rolling-Fenster in:
   - Gesamtportfolio
   - Trend-Sleeve
   - Cross-Sectional-Momentum-Sleeve
2. tägliche und kumulierte Asset-Beiträge innerhalb der festen Sleeves
3. Vol-Budget-Skalierung je Fenster
4. gepaarte Sleeve-Korrelation
5. exakte Max-Drawdown-Phase mit Start/Ende
6. reproduzierbarer Abgleich gegen den Fingerprint und die Research-Gesamtrendite
   des abgeschlossenen Validation-Reports

## Datenintegrität

Der Workflow lädt den bereits abgeschlossenen Artifact-Blob anhand seiner
GitHub-Artifact-ID und verifiziert den bekannten SHA-256-Digest, bevor die
Diagnose startet. Damit wird für die Diagnose kein neuer Yahoo-Datenabruf
benötigt.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- keine Parameter-/Signal-/Sleeve-/Gate-Änderung

Das Ergebnis ist ein Ursachenbefund, keine Optimierung.
