# Präregistrierung: Turn-of-Month Calendar Alpha 2026-09-24

## Trial

Trial-ID: `T-2026-09-24-017`

## Forschungsfrage

Erzeugt die feste, international diversifizierte Vier-Tage-Turn-of-Month-Exposition
auf einem neuen ETF-Universum einen robusten Mehrertrag gegenüber denselben Assets
außerhalb des Turn-of-Month-Fensters?

## Einzige Hypothese

Das Signal ist vollständig kalenderbasiert und nutzt keinerlei Rendite-, Volatilitäts-
oder Parameterinformation:

- am letzten Handelstag jedes Monats,
- sowie am ersten, zweiten und dritten Handelstag des Folgemonats,

wird eine gleichgewichtete Long-Exposition von exakt 1,0x auf acht vorher festgelegten
globalen Country-Equity-ETFs gehalten. Außerhalb dieses Fensters ist die Exposition 0x.

Universum:

EWS, EWM, EZA, ECH, EPU, EIDO, THD, EPHE

Es gibt keine Asset-Auswahl, keine Gewichtsoptimierung und keine Varianten-Suche.

## Daten und Aufteilung

Pro Asset werden exakt 3.500 Tages-Candles aus Yahoo Chart akquiriert und über den
identischen Timestamp-Kalender ausgerichtet.

Die Auswertung verwendet 3.498 aufeinanderfolgende Close-to-Close-Returns. Der erste
Return der 3.499 möglichen Returns wird bewusst nicht verwendet:

- Research: erste 2.798 Returns
- Holdout: letzte 700 Returns

Holdout wird ausschließlich nach Abschluss des Research-Controls ausgewiesen und nicht
zur Regel- oder Asset-Entscheidung verwendet.

## Kosten

Basis: 0,10% Gebühr + 0,05% Slippage je Turnover-Einheit.

Zusätzlich: 1,5x und 2,0x der Basis-Kosten.

Dividenden werden in diesem ersten Kalender-Control bewusst nicht als zusätzliche
Information oder Total-Return-Korrektur verwendet; die Kernprüfung betrifft
preisbasierte Tagesrenditen.

## Vorab definierte Entscheidung

Die Hypothese erhält nur dann Unterstützung, wenn alle folgenden festen Bedingungen
erfüllt sind:

1. Research-TOM-Mittelrendite > Research-Nicht-TOM-Mittelrendite.
2. Holdout-TOM-Mittelrendite > Holdout-Nicht-TOM-Mittelrendite.
3. Research-Drawdown des TOM-Portfolios <= 10%.
4. Research-Profit-Factor >= 1,10.
5. Mindestens 50% der fünf festen Research-Rolling-Fenster sind profitabel.
6. OOS/Research-Renditeverhältnis >= 0,25.
7. Holdout-Return > 0 und Holdout-PF >= 1,10.
8. Holdout-Drawdown <= 10%.
9. Holdout-Return unter 1,5x und 2x Kostenstress >= 0.
10. Kein positiver Entscheidungsstatus bei fehlender Datenintegrität.

Diese Bedingungen ändern sich nach Sichtung des Holdouts nicht.

## Literatur

Kayacetin, N. V. (2026), “Infrequent rebalancing, risk deferral, and equity returns
at the turn of the month”, Journal of International Financial Markets, Institutions
and Money, 109, 102309, DOI: 10.1016/j.intfin.2026.102309.

Die Arbeit untersucht 30 Länder über 1994-2023 und berichtet einen Turn-of-Month-Effekt,
ordnet ihn aber einem Rebalancing-/Risk-Deferral-Mechanismus zu. Eine Studie von 2025
berichtet dagegen, dass der US-Turn-of-Month-Effekt nach 2001 weitgehend verschwindet.
Die vorliegende Untersuchung prüft daher eine feste internationale ETF-Konstruktion
direkt und behauptet keine allgemeine Gültigkeit.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
Keine Orders.
