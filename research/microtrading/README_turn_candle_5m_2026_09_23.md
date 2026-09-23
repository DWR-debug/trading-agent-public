# Micro-Trading: Turn-of-the-Candle Control auf 5m

Dieser Control ist bewusst der letzte andersartige Micro-Track nach den
15m-Continuation-, Reversal-, Short/Long-, Leverage- und
Holding-Horizon-Kontrollen.

## Forschungsfrage

Ein 2023 veröffentlichter Heliyon-Artikel von Shanaev, Vasenin und Stepanov
berichtet für Bitcoin, dass Renditen an den Minuten 00, 15, 30 und 45 einer
Stunde auffällig konzentriert waren. Die Autoren untersuchten den Effekt mit
Minutendaten und berichten eine Out-of-Sample-Persistenz.

Quelle:
https://doi.org/10.1016/j.heliyon.2023.e14236

Offene Fassung:
https://pmc.ncbi.nlm.nih.gov/articles/PMC10015199/

Dieser Repository-Control übernimmt das Ergebnis nicht als gegeben. Er prüft
lediglich eine klar vorab festgelegte, gröbere Replikation:

- 5m-Candles
- feste UTC-Startminuten 00/15/30/45
- nur Turn-of-the-Candle-Candles werden gehandelt
- Long und Short als feste Gegenrichtungen
- 1x, 2x und 3x Exposure
- 0x, 0,25x, 0,5x, 1x, 2x und 4x des vorhandenen 0,15%-Kostenbasissatzes
- 80% Research / 20% Holdout
- 5 feste Research-Rolling-Fenster
- vier vollständig neue, symbol-disjunkte Assets

## Ausführung

Das Signal ist ausschließlich die UTC-Uhrzeit des Barstarts und benötigt keine
Preisinformation aus dem Bar. Die Position wird am Beginn des Turn-Bars eröffnet
und zum selben Bar-Close geschlossen.

Damit entsteht kein Preis-Lookahead in der Signalspezifikation. Gleichzeitig
ist eine Ausführung exakt am Candle-Open idealisiert und kein Beleg für reale
Mikrostruktur- oder HFT-Ausführung.

## Auswertung

Für Research und Holdout werden parallel erfasst:

- Netto- und Bruttorendite
- Maximaler Drawdown
- Profit Factor
- Turnover und durchschnittliche Brutto-Exposure
- mittlere Rendite der tatsächlich gehandelten Turn-Bars
- einfacher Trade-t-Statistikwert als deskriptiver Signaltest
- 5 feste Rolling-Research-Fenster
- Buy-and-Hold-Proxy auf demselben gemeinsamen Zeitraster

Die Richtung wird nicht nach dem Ergebnis ausgewählt. Die Kosten werden nicht
optimiert, sondern nur entlang des vorab fixierten Stressgitters ausgewiesen.

## Modellgrenzen

Shorting ist nur ein Preisreturn-Proxy. Funding, Borrow, Spread, Liquidation und
Latenz werden nicht modelliert. Leverage wird ausschließlich als feste
Multiplikation der Preisrendite untersucht.

Ein positives Ergebnis wäre deshalb zunächst nur ein Forschungsbefund. Vor
irgendeiner realistischeren Ausführungskontrolle wären eine unabhängige
Replikation und ein explizites Execution-/Kostenmodell erforderlich.

## Sicherheitsgrenzen

- Paper-only
- keine Orders
- keine Produktionsintegration
- keine Parameteroptimierung
- keine Auswahl der Richtung nach dem Ergebnis
- keine Gate- oder Kostenänderung

Dieses Dokument ist Teil des öffentlichen Research-Trackings und nicht der
Produktionsstrategie.
