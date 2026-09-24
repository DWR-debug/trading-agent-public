# Präregistrierung: Trial T-2026-09-24-041 — Correlation-Aware Minimum-Variance Portfolio Risk Control

## Forschungsfrage

Kann eine einmalig vorab festgelegte, kovarianzbewusste Minimum-Variance-Allokation
zwischen dem unveränderten Trend-Sleeve und dem unveränderten 12-1-Cross-Sectional-Momentum-Sleeve
die Risikoqualität verbessern, ohne die bestehenden Rendite-, Robustheits- und Evidenzbedingungen
gegenüber der fixen 50/50-Kontrolle zu verschlechtern?

## Motivation

Die historische Failure-Synthese zeigt wiederkehrende Risiko-Gate-Verletzungen. T028 liefert
zusätzlich einen kontroll-relativen Hinweis, dass reine Exposure-Steuerung Drawdown reduzieren
kann, ohne damit automatisch Alpha nachzuweisen. Die neue Hypothese prüft deshalb nicht erneut
Inverse-Volatility-Parity, sondern berücksichtigt explizit die Kovarianz der beiden bereits
festgelegten Sleeves.

T028 ist ausschließlich Motivation und keine Auswahlregel.

## Einzige Intervention

Unverändert:

- Trend-Sleeve: SMA-50/200 mit der bereits validierten inversen Volatilitätsgewichtung;
- Cross-Sectional-Sleeve: feste 12-1-Momentum-Definition mit Top-2 Long-only;
- monatliches Rebalancing innerhalb der bestehenden Sleeves;
- Point-in-Time-Ausführung;
- gleicher Kostenvertrag;
- gleicher blinder Holdout;
- gleiche absolute und relative Evidence-Gates.

Einzige neue Portfolio-Allokationsregel:

- am ersten realisierten Handelstag eines neuen Kalendermonats wird die Sleeve-Allokation neu berechnet;
- Beobachtungsfenster: die unmittelbar vorausgehenden 63 realisierten gemeinsamen Sleeve-Renditen;
- Schätzung von Varianz der Trend-Sleeve, Varianz der Cross-Sectional-Sleeve und ihrer Kovarianz;
- Minimum-Variance-Gewicht der Trend-Sleeve:

  w_trend = (var_cs - cov_tc) / (var_trend + var_cs - 2 * cov_tc)

- w_trend wird fest auf [0, 1] begrenzt;
- w_cs = 1 - w_trend;
- vor Vorliegen von 63 Beobachtungen ist die Allokation 50/50;
- keine erwarteten Renditen, kein Optimierer, keine Short-Positionen, kein Leverage;
- Gewichtssprünge werden als echter Portfolio-Turnover kostenwirksam berücksichtigt.

Damit ist die Intervention vollständig deterministisch und verändert keinen Sleeve-Signalpfad.

## Kontrolllauf

Primäre Baseline ist die unveränderte feste 50/50-Aggregation derselben zwei Sleeves.

Der Challenger darf gegenüber dieser Kontrolle nicht schlechter sein bei:

- Research-Return;
- Research-Maximum-Drawdown;
- Research-Profit-Factor;
- minimalem Rolling-PF;
- Anteil profitabler Research-Rolling-Fenster;
- durchschnittlichem Rolling-Drawdown;
- OOS/Research-Return-Ratio;
- Holdout-Return;
- Holdout-Profit-Factor;
- Holdout-Maximum-Drawdown.

## Datenbasis

Trend-Leg:

VONE, VONG, VONV, VOE, VOT, IWB, IUSG, IUSV

Cross-Sectional-Leg:

IWS, IWP, IJS, IJJ, IJK

Alle 13 Symbole sind vorab als neue, vollständig symbol-disjunkte Validierungsbasis reserviert.
Der Datenvertrag verlangt 3.500 Daily-Candles je Symbol und 3.498 gemeinsame Point-in-Time-Returnperioden nach Konstruktion.

Jede Leg-Datei besitzt einen eigenen Coverage-Preflight. Erst wenn beide Coverage-Gates
bestanden sind, darf ein formaler T041-Performance-Lauf stattfinden.

## Formale Gates

Der Challenger muss im Basisfall alle folgenden unveränderten Gates erfüllen:

1. positive Research-Gesamtrendite;
2. Research-Maximum-Drawdown <= 10 %;
3. Research-Profit-Factor >= 1,10;
4. minimaler Rolling-PF >= 1,10;
5. profitable Rolling-Fensterquote >= 50 %;
6. durchschnittlicher Rolling-Drawdown <= 10 %;
7. OOS/Research-Return-Ratio >= 0,25;
8. positiver blinder Holdout;
9. Holdout-PF >= 1,10;
10. Holdout-Maximum-Drawdown <= 10 %;
11. Holdout-Return bei 1,5x-Kostenstress >= 0 %;
12. Holdout-Return bei 2,0x-Kostenstress >= 0 %.

Zusätzlich gilt der vollständige Nicht-Verschlechterungsvertrag gegenüber der fixen 50/50-Kontrolle.

Keine dieser Schwellen darf aus T041-Daten nachträglich verändert werden.

## Kosten

Basis:

- Gebühr: 0,10 % je Seite;
- Slippage: 0,05 % je Seite.

Zusätzliche Stressfälle:

- 1,5x Gesamtkosten;
- 2,0x Gesamtkosten.

Auch Allokationsänderungen zwischen den Sleeves werden als Turnover belastet.

## Blindheit und Governance

- Holdout ist vollständig blind und darf für keinerlei Auswahl verwendet werden.
- Es gibt keine Parameter- oder Asset-Suche.
- Es gibt keine Gewichtssuche.
- Es gibt keinen zweiten T041-Challenger auf demselben Datensatz.
- Kein Re-Backtest nach Sichtung des Holdouts.
- Kein Gate-Relaxieren.
- Keine automatische Promotion.
- Ein positives T041-Ergebnis wäre ausschließlich Research-Evidenz und keine Live-Freigabe.

## Abbruchregeln

Wenn einer der beiden Coverage-Preflights den Datenvertrag verfehlt, wird T041 vor jeder
Performanceauswertung als DATA_INVALID behandelt. Ein Coverage-Nachfolger darf ausschließlich
einen Datenqualitätsfehler reparieren; die Hypothese und alle übrigen Regeln bleiben unverändert.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
