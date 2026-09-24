# Ergebnis: sechste Validierung – CS-Dispersion-Risikobudget (2026-09-24)

## Status

Trial T-2026-09-24-010 ist abgeschlossen und wird verworfen.

Die präregistrierte Hypothese wurde auf einem sechsten vollständig
symbol-disjunkten Validierungssatz mit exakt 3.500 gemeinsamen Candles und
3.498 Portfolio-Return-Perioden getestet. Es gab keine Parameter-, Varianten-
oder Schwellenwertsuche. Der Holdout wurde ausschließlich als Bestätigung
verwendet.

Validation Artifact: 10799293827

Report-Fingerprint:
ce7db03ddee10928ded0b859a6748c077198bcbe7974d514ccdb77ac6a80f64a

## Präregistrierte Regel

Die fixe Top-2-CS-Auswahl und das 50/50-Grundportfolio blieben unverändert.
Nur das CS-Sleeve wurde abwärts skaliert, wenn die aktuelle 21-Session-
Cross-Sectional-Dispersion über dem Median der vorherigen 63 beobachteten
21-Session-Dispersionen lag.

Die Skalierung konnte die ursprünglichen 50% CS-Sleevegewicht niemals erhöhen.

## Ergebnis im Base-Szenario mit bestehendem 10%-Volatilitätsbudget

| Kennzahl | Baseline | CS-Dispersion-Budget |
|---|---:|---:|
| Research Return | +53.45% | +40.93% |
| Research Max Drawdown | 20.77% | 22.15% |
| Rolling Profit Factor | 1.0805 | 1.0676 |
| Rolling Ø Drawdown | 15.59% | 15.73% |
| Profitable Rolling-Fenster | 4/5 | 4/5 |
| Holdout Return | +38.53% | +33.33% |
| Holdout Max Drawdown | 10.39% | 9.87% |
| Holdout Profit Factor | 1.2147 | 1.1902 |

Die vier vorab festgelegten Research-Kriterien waren damit sämtlich nicht
erfüllt:

- Research-Maximum-Drawdown: nicht besser;
- Rolling-Profit-Factor: nicht besser;
- Rolling-Durchschnittsdrawdown: nicht besser;
- kumulierter Research-Return: nicht besser.

Die Holdout-Bestätigung war ebenfalls nicht erfüllt. Der Drawdown wurde zwar
leicht reduziert, aber Holdout-Rendite und Holdout-Profit-Factor waren
schlechter.

## Robustheitsbild

Die Richtung bleibt auch unter höheren Kosten negativ. Im 1,5x-Kosten-Szenario
lag die Candidate-Research-Rendite bei +31.80% gegenüber +48.62% der Baseline;
im 2x-Kosten-Szenario bei +23.25% gegenüber +43.95%.

Die bestehenden Robustheitsgates des Candidates blieben nicht bestanden.

## Was wir daraus lernen

Der Test spricht gegen diese konkrete Form eines kontinuierlichen
Dispersion-basierten CS-Risikobudgets.

Die Aussagen bleiben sauber getrennt:

1. Die zuvor replizierte CS-Reversal-Struktur bleibt ein valider
   Diagnosebefund.
2. Der bereits getestete harte Ein-Sitzungs-Cooldown war ungeeignet.
3. Auch die hier getestete weiche, kontinuierliche Dispersion-Skalierung
   liefert auf einem neuen disjunkten Datensatz keine robuste Verbesserung.
4. Es gibt derzeit keinen Nachweis, dass ein einfacher externer Risk-Overlay
   auf die identifizierte CS-Reversal-Problematik die Gesamtstrategie verbessert.

## Wissenschaftliche Entscheidung

Der Hypothesenpfad wird entsprechend der Präregistrierung beendet:

- kein Tuning dieser Regel auf dem sechsten Datensatz;
- keine alternative 21-/63-Variante auf demselben Satz;
- keine nachträgliche Gewichtsanpassung;
- keine Änderung der bestehenden Research-Gates;
- keine Produktionsintegration;
- keine Orders.

Die statistische Selection-Evidenz bleibt im Trial-Ledger als nicht-ready
markiert. DSR/PBO werden für dieses Einzel-Experiment nicht künstlich erzeugt.

## Sicherheitsstatus

PAPER_ONLY=True

LIVE_TRADING_ENABLED=False

orders_enabled=False

Die bestehende Produktions-/Research-Blockierung bleibt unverändert.
