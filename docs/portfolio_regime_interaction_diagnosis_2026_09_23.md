# Portfolio-Regime-/Sleeve-Interaktionsdiagnose — 2026-09-23

## Ziel

Der gemeinsame Failure-Consensus über zwei vollständig disjunkte Vollvalidierungen zeigt denselben vierteiligen Risiko-/Robustheits-Failure. Dieser Control prüft nun, ob die beobachtete Portfolio-Schwäche mit einer wiederkehrenden Interaktion der beiden Sleeves zusammenfällt.

## Datenbasis

- zweite Failure-Diagnose: Artifact 10742595425
- dritte Failure-Diagnose: Artifact 10745788019
- beide Reports und Diagnose-Fingerprints werden vor der Analyse erneut verifiziert

## Reine Beobachtungsmessung

Für jedes der fünf festen Research-Fenster beider Datensätze werden gemeinsam betrachtet:

- Portfolio-Periodenrendite, Drawdown und Profit Factor
- Trend-Sleeve-Rendite, Drawdown und Profit Factor
- Cross-Sectional-Sleeve-Rendite, Drawdown und Profit Factor
- Sleeve-Rendite-Korrelation
- Median- und Minimum-Scale des realen Vol-Budgets
- gleichzeitige negative Periodenrendite beider Sleeves
- Fälle, in denen die Cross-Sectional-Sleeve den größeren Sleeve-Drawdown aufweist

Zusätzlich werden die negativen Portfolio-Fenster separat den positiven Portfolio-Fenstern gegenübergestellt. Es werden keine Schwellenwerte optimiert oder aus den Daten ausgewählt.

## Forschungsfrage

Die Diagnose soll zwischen drei deskriptiven Situationen unterscheiden:

1. überwiegend Cross-Sectional-getriebene Failure-Fenster
2. gleichzeitige Schwäche beider Sleeves
3. geringe Portfolio-Scale reicht trotz De-Risking nicht aus, um die negative Sleeve-Interaktion auszugleichen

Das Ergebnis ist ausdrücklich kein Kausalitätsnachweis. Es ist ein Replikations-/Mechanismusbefund, der entscheidet, ob eine spätere Intervention als Portfolio-Regime-Hypothese sinnvoll präregistriert werden kann.

## Sicherheitsregeln

- keine Parameteränderung
- keine Signaländerung
- keine Asset-Ersetzung
- keine Sleeve-Gewichtsänderung
- keine Gate-Änderung
- Holdout wird nicht zur Auswahl einer Intervention verwendet
- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False