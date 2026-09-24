# Präregistrierung: Open/Close Gap-Reversal Alpha 2026-09-24

## Trial

Trial-ID: `T-2026-09-24-020`

## Forschungsfrage

Erzeugt eine feste, parameterfreie Gegenposition zum Overnight-Gap eines
vollständig neuen ETF-Universums eine robuste positive Same-Day-Intraday-Rendite?

## Einzige Hypothese

Für jeden Handelstag wird je Asset nur das bereits beobachtbare Overnight-Gap
vom vorherigen Schlusskurs zum aktuellen Open verwendet:

- positives Overnight-Gap -> Short vom Open bis zum Close,
- negatives Overnight-Gap -> Long vom Open bis zum Close,
- exakt null -> Flat.

Alle acht vorher festgelegten Assets erhalten unabhängig voneinander ein
gleiches Gewicht von 1/8, sodass die maximale Brutto-Exposure exakt 1,0x bleibt.
Es gibt keinen Schwellenwert, keine Lookback-Periode, keine Optimierung und
keine Asset-Auswahl.

Universum:

SPYG, SPYV, SPTM, SPMD, SDY, RWR, XNTK, XPH

Die verwendeten Preise werden aus Yahoo-OHLC und Adjusted Close so rekonstruiert,
dass Open und Close konsistent split-/dividendenbereinigt werden. Das Signal
wird ausschließlich mit Informationen bis zum jeweiligen Open gebildet.

## Daten und Aufteilung

Pro Asset werden exakt 3.500 Tages-Candles über die bestehende Yahoo-Research-Pipeline
akquiriert und auf den gemeinsamen Timestamp-Kalender ausgerichtet.

Die Auswertung verwendet 3.498 Point-in-Time-Returns:

- Research: erste 2.798 Returns
- Holdout: letzte 700 Returns

Der erste potenziell verfügbare Return wird aus Konsistenzgründen mit den bestehenden
PIT-Controls bewusst nicht ausgewertet. Holdout bleibt bis zum Abschluss des
Research-Controls unangetastet und wird nicht zur Regel- oder Asset-Entscheidung
verwendet.

## Kosten

Verwendet wird der bestehende Projekt-Kostenstandard je Turnover-Einheit:

- Gebühr: 0,10%
- Slippage: 0,05%
- Basiskosten: 0,15% je Turnover-Einheit

Da jede aktive Position am selben Tag eröffnet und wieder geschlossen wird,
werden Entry und Exit als getrennte Turnover-Einheiten erfasst.

Zusätzlich werden feste Kostenstress-Szenarien mit 1,5x und 2,0x des Basissatzes
gerechnet.

## Vorab definierte Entscheidung

Unterstützung der Hypothese liegt nur vor, wenn alle folgenden festen Checks
erfüllt sind:

1. Research-Netto-Return > 0.
2. Research-Drawdown <= 10%.
3. Research-Profit-Factor >= 1,10.
4. Mindestens 50% der fünf festen Research-Rolling-Fenster sind profitabel.
5. OOS/Research-Renditeverhältnis >= 0,25.
6. Holdout-Netto-Return > 0.
7. Holdout-Profit-Factor >= 1,10.
8. Holdout-Drawdown <= 10%.
9. Holdout-Rendite bleibt unter 1,5x Kostenstress >= 0.
10. Holdout-Rendite bleibt unter 2,0x Kostenstress >= 0.
11. Die mittlere Gap-Reversal-Richtung ist in Research und Holdout positiv:
    Das Signal-Portfolio muss im Mittel eine positive Beziehung zur
    negativen Overnight-Gap-Richtung zeigen.

Diese Bedingungen ändern sich nach Sichtung des Holdouts nicht.

## Literatur-/Inspirationsbasis

Die Hypothese ist ausschließlich als Research-Frage vorregistriert.

Eine 2026 veröffentlichte Untersuchung zu 24 globalen Aktienindizes untersucht
Opening Gaps und zeitrespecting Cross-Index-Abhängigkeiten
(doi:10.1016/j.bir.2026.100871).

Eine 2026 veröffentlichte U.S.-Aktienuntersuchung berichtet eine
Overnight-to-Intraday-Reversal-Beziehung, bei der starke Overnight-Gaps
teilweise intraday zurückgegeben werden.

Ein separates 2026-Update der Federal Reserve Bank of New York berichtet,
dass ein früher dokumentierter enger Overnight-Drift in U.S.-Equity-Futures
seit 2021 deutlich abgeflacht ist. Diese Evidenz betrifft ein anderes Zeitfenster
und eine andere Instrumentengruppe und wird deshalb nicht als direkte Bestätigung
der vorliegenden Hypothese verwendet.

Externe Open-Source-Inspiration für die Robustheits-/Kostenbetrachtung:
NafizNoor1/overnight-anomaly (MIT-Hinweis auf konsistente Adjustierung von
Open/Close und explizite Kostenanalyse). Keine Ergebnisse dieses Projekts werden
als Evidenz unseres Controls übernommen.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
Keine Orders.
