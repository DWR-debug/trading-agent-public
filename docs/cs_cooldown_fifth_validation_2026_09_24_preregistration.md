# Präregistrierung: Ein-Sitzungs-CS-Cooldown auf fünftem Validierungssatz

## Forschungsfrage

Kann ein fixer Ein-Sitzungs-Cooldown des CS-Sleeves nach einem bereits
vollständig beobachteten Winner-Reversal die bisherigen Risiko-Probleme
reduzieren, ohne die Rendite-/Profitabilitätsmerkmale des unveränderten
50/50-Kandidaten zu verschlechtern?

## Vorab festgelegte Regel

Wenn das feste Cross-Sectional-Winner-Reversal über eine vollständige
Open-to-Open-Periode beobachtet wurde, wird ausschließlich für die **nächste**
Return-Periode das gesamte 50%-CS-Sleevegewicht auf 0 gesetzt und in Cash gehalten.
Das Trend-Sleeve bleibt unverändert bei 50%.

Es gibt genau eine Cooldown-Periode: 1 Session. Die zugrunde liegende Rebalance-Struktur bleibt 21-Session.
Längen, Schwellenwerten, Gewichten oder Varianten.

Wichtig: Die Reversal-Periode selbst wird nicht verändert. Das verhindert
Lookahead: Die Regel verwendet ausschließlich das Vorperioden-Flag.

## Neue Validierungsbasis

Ein fünfter vollständig symbol-disjunkter Satz wird vor Datenabruf festgelegt:

Trend:
EPP, FEZ, GSG, DBA, FXA, VIG, BIV, VOO

Cross-Sectional:
IYC, IYE, IYF, IYK, IYM

Alle Assets werden auf 3.500 gemeinsame Candles ausgerichtet; danach werden
2798 Research- und 700 Holdout-Return-Perioden ausgewertet.

Der Satz muss gegenüber den vier bisherigen Validierungssätzen vollständig
symbol-disjunkt bleiben.

## Auswertung

Es werden unverändert Base-, 1,5x- und 2x-Kosten sowie die bestehende 10%-Volatilitäts-
Budgetierung ausgewertet.

Research-Hypothese gilt nur dann als PASS, wenn der Cooldown gegenüber dem
unveränderten Baseline-Kandidaten gleichzeitig folgende feste Richtungen erfüllt:

- Research-Maximum-Drawdown nicht schlechter;
- Rolling-Profit-Factor nicht schlechter;
- Rolling-Durchschnittsdrawdown nicht schlechter;
- kumulierte Research-Rolling-Rendite nicht schlechter.

Holdout wird ausschließlich als Bestätigung verwendet, nicht zur Auswahl. Bestätigung
erfordert gleichzeitig: Holdout-Rendite nicht schlechter, Holdout-Drawdown nicht
schlechter und Holdout-Profit-Factor nicht schlechter.

Zusätzlich müssen die bestehenden Research-Gates des Cooldown-Kandidaten bestehen.

## Unverändert

- Trend-Regel und 50%-Trend-Sleeve;
- CS-Signalgenerierung;
- 252/21/21/Top-2-Regel;
- Point-in-Time-Semantik;
- Kosten-/Turnover-Modell;
- bestehende Gate-Definitionen;
- keine Optimierung;
- keine Parameter-/Schwellenwertsuche;
- keine Asset-Auswahl nach Ergebnis;
- Holdout nicht für Selection;
- keine Orders.

PAPER_ONLY=True; LIVE_TRADING_ENABLED=False.

## Erwartete Verwendung

Nur ein vollständiger PASS über diesen neuen disjunkten Validierungssatz darf
eine spätere unabhängige Replikation rechtfertigen. Ein FAIL beendet diesen
Forschungspfad; dann wird keine weitere Optimierung derselben Hypothese auf
demselben Satz durchgeführt.
