# Vierfach-Regime-/Sleeve-Interaktionsdiagnose — Pre-Registration 2026-09-23

## Forschungsfrage

Über alle vier unabhängigen Validierungsfamilien und deren fünf festen
Research-Rolling-Fenster soll deskriptiv geprüft werden, ob negative
Portfolio-Fenster überwiegend auf gemeinsame Schwäche beider Sleeves oder
auf eine einzelne Sleeve zurückgehen und wie stark die bestehende
63-Session-/10%-Risk-Layer dabei skaliert.

## Vorab definierte Einheiten

- 4 vollständig symbol-disjunkte Validierungsfamilien
- 5 feste Research-Fenster je Familie
- insgesamt 20 Research-Fenster
- nur 2.798 Research-Returns je Familie
- Portfolio-Negativfenster: Research-Rolling-Return < 0
- gemeinsame Schwäche: Trend-Return < 0 und CS-Return < 0
- einseitige Schwäche: genau eine der beiden Sleeve-Renditen < 0

## Gemessene Größen

- Portfolio-, Trend- und Cross-Sectional-Return
- Portfolio-Drawdown und PF
- Sleeve-Drawdown und PF
- De-Risking-Anteil, mittlere und minimale Scale
- Sleeve-Renditekorrelation
- Anzahl und Anteil negativer Portfolio-Fenster nach Failure-Klasse

## Interpretation

Die Untersuchung ist rein deskriptiv. Es wird keine universelle Schwelle zur
Auswahl einer Intervention aus den Ergebnisdaten geschätzt.
Die Auswertung dient ausschließlich dazu, den nächsten Forschungsmechanismus
zu bestimmen oder festzustellen, dass kein hinreichend klarer Kontrast vorliegt.

## Auswertungsgrenze

Der Holdout wird weder ausgegeben noch für die Interpretation oder
Entscheidung verwendet.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Parameteroptimierung
- keine Asset-Auswahl
- keine Gate-Änderung
- keine Produktionsmutation
- keine Orders