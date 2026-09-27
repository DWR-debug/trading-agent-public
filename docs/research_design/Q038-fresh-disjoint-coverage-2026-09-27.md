# Q038 — Fresh Disjoint Coverage for Alpha Architecture

**Stand:** 2026-09-27  
**Status:** PREREGISTERED / COVERAGE-ONLY  
**Vorgänger:** Q037 — Ex-ante Alpha-Mechanism-Architecture

## Zweck

Q038 erzeugt die Datenvoraussetzung für die nächste Alpha-Forschungsphase. Es wird ausschließlich geprüft, ob ein neu definiertes, vollständig symbol-disjunktes Kandidatenuniversum die eingefrorene Coverage-Geometrie erfüllt.

Q038 ist **keine** Performanceprüfung und keine Auswahl nach Rendite.

## Fester Kandidatenpool

Die Reihenfolge ist Bestandteil des Vertrags:

`IVE → IWL → DLN → DHS → DON → DES → USRT → ITB`

Vor jeder Datenabfrage wird geprüft, dass kein Kandidat bereits in einem registrierten Research-Universum verbraucht wurde.

## Deterministische Coverage-Regel

Für jedes noch nicht verbrauchte Symbol werden unverändert 4.000 Tages-Candles angefordert.

Ein Symbol darf nur übernommen werden, wenn:

1. mindestens 3.500 valide Candles verfügbar sind;
2. die Aufnahme des Symbols in die bisher akzeptierte Menge einen gemeinsamen Kalender von mindestens 3.500 Sessions erhält.

Die Kandidaten werden genau einmal in der festen Quellreihenfolge verarbeitet. Performance-, Return-, Drawdown-, Profit-Factor-, Holdout- oder sonstige Strategiekennzahlen dürfen die Auswahl nicht beeinflussen.

Bei acht akzeptierten Symbolen und mindestens 3.500 gemeinsamen Sessions lautet der Status `COVERAGE_VALIDATED`. Andernfalls `DATA_INSUFFICIENT`.

## Nächste wissenschaftliche Schranke

Erst nach einem erfolgreichen Q038-Coverage-Receipt darf eine getrennte PIT-Prüfung für das neue Universum vorbereitet werden. Erst nach bestandener PIT-Prüfung kommt eine separat präregistrierte Fixed-Rule-Performanceausführung in Betracht.

Der unveränderte 13-Gate-Evidence-Vertrag bleibt bestehen:

- 2.798 Research-Perioden
- 700 Holdout-Perioden
- Rolling-Stabilität
- OOS/IS-Verhältnis
- Kostenstress
- Holdout bis zur finalen Auswertung blind
- keine ergebnisgetriebene Auswahl

## Sicherheitszustand

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`ORDERS_ENABLED=False`  
`AUTOMATIC_PROMOTION=False`

Die Coverage-Ausgabe ist ein Daten-/Provenienzbeleg und keine Handelsentscheidung.
