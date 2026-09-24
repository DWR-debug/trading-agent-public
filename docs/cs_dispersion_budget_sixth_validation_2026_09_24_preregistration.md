# Präregistrierung: CS-Dispersion-Risikobudget auf sechstem Validierungssatz

## Forschungsfrage

Kann das bestehende 50/50-Portfolio robuster werden, wenn das fixe Top-2 CS-Sleeve
bei ungewöhnlich hoher Cross-Sectional-Dispersion kontinuierlich und
ausschließlich abwärts skaliert wird?

## Exakte Regel

Für jeden aktuellen Return-Startpunkt werden ausschließlich bereits
abgeschlossene CS-Daten verwendet:

1. 21-Session-Close-to-Close-Rendite je CS-Asset;
2. Population-Standardabweichung dieser fünf Renditen als aktuelle Dispersion;
3. Median der vorherigen 63 beobachteten 21-Session-Dispersionen als Referenz;
4. Originale Top-2-CS-Gewichte werden mit min(1, Referenz / aktuelle Dispersion) multipliziert;
5. die CS-Sleeve bleibt dadurch immer höchstens 50% des Gesamtportfolios;
6. der Trend-Sleeve bleibt unverändert 50%.

Es gibt keine zusätzlichen Schwellenwerte, Gewichtsvarianten oder Parameter-
Suchen. Die 21/63 Horizonte sind vorab festgelegt.

## Sechster disjunkter Validierungssatz

Trend: IVV, EWC, EWW, EWY, EWT, EIS, EDV, MUB

CS: XSD, XAR, XHE, XPH, XNTK

Alle Symbole sind gegenüber allen bisher registrierten Universen symbol-disjunkt.
Pro Asset werden exakt 3.500 gemeinsame Candles ausgerichtet; die Portfolio-
Zeitreihe muss 3.498 Return-Perioden liefern.

Research/Holdout: 2798 / 700.

## Vorab definierte Erfolgskriterien

Gegenüber der unveränderten Baseline müssen im Research gleichzeitig gelten:

- Research-Maximum-Drawdown nicht schlechter;
- Rolling-Profit-Factor nicht schlechter;
- Rolling-Durchschnittsdrawdown nicht schlechter;
- kumulierter Research-Return nicht schlechter.

Zusätzlich müssen die bestehenden Research-Gates bestehen.

Im Holdout müssen als reine Bestätigung Rendite, Drawdown und Profit Factor
gegenüber der Baseline nicht schlechter sein.

Die einzelne Hypothese wird nicht auf diesem Datensatz variiert.

## Selection-/PBO-/DSR-Governance

Trial-ID: T-2026-09-24-010.

Da nur eine vorab definierte Architekturhypothese geprüft wird, wird keine
künstliche DSR-/PBO-Zahl erzeugt. Das Ledger dokumentiert die statistische
Selection-Evidenz als nicht-ready.

## Sicherheit

Keine Orders, keine Live-Ausführung und keine Änderung bestehender Gates oder
Produktionskonfiguration. PAPER_ONLY=True; LIVE_TRADING_ENABLED=False.
