# Literaturbasierter Strategieforschungs-Redesign — 2026-09-22

## Ausgangslage

Die bisherigen Research-Layer haben die technische Reproduzierbarkeit bestätigt,
aber auf der aktuellen Preis-only-Strategiearchitektur bislang keinen über mehrere
Universen stabilen positiven Kandidaten hervorgebracht.

Der wichtigste empirische Befund der bisherigen Evidenzfamilie ist das schwache
Verhältnis zwischen In-Sample- und OOS-Performance: 50 von 52
Dataset/Profile-Auswertungen verfehlen das Overfit-Kriterium. Rolling-WF bleibt
ebenfalls ein wiederkehrender Engpass.

## Literaturbefunde

Time-Series-Momentum und Trend Following sind deutlich breiter untersucht als
unser bisheriger 3- bis 21-Tage-Momentumbaustein. Moskowitz, Ooi und Pedersen
dokumentieren Persistenz über ungefähr 1 bis 12 Monate in 58 liquiden
Instrumenten aus mehreren Assetklassen; die Diversifikation über Märkte ist
Teil der untersuchten Konstruktion. citeturn809836search1

Hurst, Ooi und Pedersen finden in einer sehr langen historischen Untersuchung
erneute Evidenz für Trend Following und betonen ebenfalls die
Mehrmarkt-/Mehrasset-Perspektive. citeturn665863search4

Asness, Moskowitz und Pedersen finden Value- und Momentum-Prämien über
mehrere Märkte und Assetklassen. Value ist für unsere aktuelle Preis-only-
Datenbasis noch keine unmittelbar testbare Erweiterung. citeturn665863search1

Mean Reversion und Reversal besitzen ebenfalls historische Evidenz, sind aber
stark horizon- und kostenabhängig. Für kurzfristige Reversal-Systeme können
Transaktionskosten einen erheblichen Teil der Profitabilität absorbieren. citeturn388493search5turn167997search9

Sullivan, Timmermann und White zeigen zugleich, warum eine große Menge
getesteter technischer Regeln ohne strikte Data-Snooping-Kontrolle zu
überschätzten Ergebnissen führen kann. citeturn809836search0

Die aktuelle AQR-Evidenz bestätigt die Existenz mehrerer langfristig
beobachteter Faktorprämien, betont aber deutliche Zeitvariation und die
Gefahr, dass ex-post Timing nach Datenverzögerungen und Transaktionskosten
wenig Zusatznutzen liefert. citeturn665863search0turn665863search3

## Ableitung für den Trading Agent

Der bisherige Ansatz ist nicht als Research-Methode unbrauchbar, aber als
primäre Strategie-Suchmaschine zu eng.

Der aktuelle Produktionspfad besteht im Kern aus:

- Momentum mit sehr kurzen Lookbacks
- Mean Reversion mit kurzen Fenstern
- einem symmetrischen Score-Combiner
- einem fixen 2-Prozent-Stop
- Optimierung von 1.280 Kombinationen auf einem einzelnen Asset

Das unterscheidet sich strukturell von den stärker diversifizierten,
mittel-/langfristigen Trend- und Momentum-Systemen der Literatur.

Deshalb ändern wir die Reihenfolge der Forschung:

1. Strategiefamilie zuerst definieren.
2. Trade-Lifecycle und Exitlogik separat definieren.
3. Ausführung punkt-in-zeit-korrekt modellieren.
4. Positionsrisiko separat über Volatilität steuern.
5. Erst danach Portfolioaggregation und Auswahlmechanismen untersuchen.
6. Parameteroptimierung erst nach einem reproduzierbaren Familiennachweis.

## Point-in-Time-Ausführung

Eine Tageskerze darf erst nach ihrem Schluss als Information verwendet werden.
Die neue Forschungslaborschicht verwendet deshalb:

Entscheidung bei Close(t) → Ausführung bei Open(t+1).

Der bestehende Backtest verwendet dagegen heute Signalbildung am Schluss und
simuliert Entry/Exit grundsätzlich noch auf diesem Schluss. Diese Semantik
bleibt zunächst als Produktionsbestand unverändert, wird aber für den neuen
Research-Laborkontrolllauf bewusst nicht verwendet.

Realistische Ausführungs- und Kostenannahmen sind eine wesentliche
Backtesting-Bedingung. citeturn167997search8turn167997search11

## Neue Referenzfamilien

Der neue Research-Laborlauf verwendet einen kleinen, vorab definierten Satz
ohne Parameteroptimierung:

- Time-Series Momentum, mittlere/lange Horizonte
- Ensemble aus mehreren Momentum-Horizonten
- Donchian-/Breakout-Trend
- Moving-Average-Trend
- Mean Reversion als Kontrollfamilie
- Buy-and-Hold als Referenz

Die ersten vier Familien sind als Referenzmodelle gedacht und nicht als
Behauptung, dass sie auf unserem Datensatz bereits erfolgreich sind.

Die Positionssteuerung wird getrennt von der Signaldefinition über ATR-basierte
Volatilitätsskalierung untersucht.

## Portfolioebene

Die Literatur zu Time-Series-Momentum untersucht breit diversifizierte
Mehrmarkt-Konstruktionen. citeturn809836search1turn665863search4

Unser bisheriger Agent ist dagegen primär ein Single-Asset-System. Das ist eine
wahrscheinliche strukturelle Einschränkung.

Der längerfristige Zielpfad lautet daher:

Mehrere liquide Assets → Signal je Asset → Volatilitätsskalierung →
Positionslimits → gemeinsame Portfolio-Equity-Curve.

## Was wir nicht ändern

Die Research-Gates bleiben unverändert.

Der Produktions-Parameterraum bleibt zunächst unverändert.

Selection-Profile werden nicht zu einer neuen „Bestenregel“ umgebaut.

Paper-Only bleibt aktiv.

Es wird keine Live-Ausführung eingeführt.

## Konkreter nächster Kontrollschritt

Der Literatur-Strategie-Laborkontrolllauf auf dem unveränderten historischen
Benchmark-Archiv beantwortet zunächst nur eine Frage:

Kann eine klar definierte, literaturbasierte Strategiefamilie unter
point-in-time-korrekter Ausführung und separater Risikosteuerung reproduzierbare
Profitabilität über mehrere Assets und mehrere Zeitfenster erzeugen?

Ein positives Ergebnis wäre noch kein Produktionsnachweis. Es wäre lediglich der
Grund, diese Familie in den echten Trading-Agent-Backtest zu integrieren und
anschließend erneut durch WFO, Rolling-WF, Robustness, Overfit und Holdout zu
prüfen.
