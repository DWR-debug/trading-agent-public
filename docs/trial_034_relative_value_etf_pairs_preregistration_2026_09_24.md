# Präregistrierung: Trial T-2026-09-24-034 — Fixed ETF Relative-Value Pairs

## Forschungsfrage

Kann eine kleine, ex ante festgelegte, market-neutrale ETF-Pairs-Trading-Regel
nach realistischen Projektkosten einen eigenständigen positiven Return-Stream
mit kontrolliertem Drawdown liefern?

## Evidenzbasierte Motivation

Die peer-reviewte Arbeit von Chen & Alexiou (Journal of Asset Management, 2025)
untersucht ETF-Pairs-Trading über 2000–2024 und beschreibt einen monatlich
aktualisierten Cointegration-/ADF-Gate, Preisverhältnis-Z-Score und feste
Mean-Reversion-Regeln. In der dort beschriebenen dynamischen Variante werden
Paare mit ADF-p < 0,05 zugelassen, der Z-Score über ein 200-Tage-Fenster
gebildet, Einträge bei |Z| > 1,65 eröffnet und bei Rückkehr innerhalb |Z| < 0,75
geschlossen. Die Autoren betonen zugleich die Abhängigkeit von der Stabilität
der Cointegration und die Sensitivität gegenüber Handelskosten. citeturn508293view0turn622934view1

Eine frühere ETF-Pairs-Arbeit (Tokat & Hayrullahoğlu, 2022) zeigt ebenfalls,
dass Cointegration als alternative Pair-Auswahlmethode für ETFs untersucht
werden kann und dass Transaktionskosten wesentlich sind. citeturn816417search2

Die fremden Resultate werden ausschließlich als Methodensource verwendet.
Sie sind keine Evidenz unseres Systems.

## Einzige Intervention

Es gibt fünf feste, ex ante festgelegte ökonomische ETF-Paare:

1. VTWO / IJR — US Small Cap
2. QQEW / ONEQ — Nasdaq-orientierte Aktien
3. EEMV / SCHE — Emerging Markets
4. IGIB / SPIB — US Investment-Grade Corporates
5. SCHP / STIP — US TIPS

Diese zehn Symbole sind gegenüber den bisherigen Projektuniversen
vollständig symbol-disjunkt.

Für jedes Paar:

- monatlicher Refresh alle 21 Handelssitzungen;
- Cointegration-/Stationaritätsgate: ADF auf dem Preisverhältnis der letzten
  200 abgeschlossenen Sitzungen;
- Zulassung nur bei p < 0,05;
- täglicher Z-Score des Preisverhältnisses über dieselben 200 Sitzungen;
- Long-Spread bei Z < -1,65;
- Short-Spread bei Z > +1,65;
- Exit bei |Z| < 0,75;
- wird ein Pair ungültig, wird es flach gestellt;
- pro aktivem Pair gleiche Kapitalhälften Long/Short;
- aktives Pair erhält denselben Anteil am gesamten maximalen Gross-Budget;
- maximales Gesamt-Gross-Exposure = 1,0;
- Netto-Exposure = 0,0;
- keine Shorts außerhalb der Pair-Hedge-Struktur;
- kein Hebel > 1;
- keine Pair-Suche, keine Parameter-Suche, kein Threshold-Tuning.

Die Regel ist ausschließlich auf Close(t)-Information aufgebaut. Die Zielposition
wird für die nächste Open-zu-folgende-Open-Periode angewendet.

## Datenvertrag

Coverage-Preflight:

- Workflow: 36044264502
- Artifact: 10827702970
- 10/10 Symbole mit je 3.520 Candles
- gemeinsamer Kalender: 3.520
- Coverage-Fingerprint:
  b4102c8e01e442ca5657426b96f0dc97ec919783299408946975f49b05c445a4
- keine Performanceauswahl im Coverage-Preflight

Research-Run:

- 3.500 Candles je Symbol;
- 3.498 PIT-Returnperioden;
- 2.798 Research;
- 700 blinder Holdout.

## Kosten- und Modellvertrag

Projektstandard:

- Fee: 10 bps je Richtung;
- Slippage: 5 bps je Richtung;
- Kostenstress 1,5x und 2,0x.

Die Kosten werden auf jede absolute Positionsänderung angewendet.

Wichtige Einschränkungen:

- Short-Borrow-/Finanzierungskosten sind in diesem reinen Research-Control noch
  nicht verfügbar und werden deshalb **nicht** modelliert.
- ETF-Dividenden-Cashflows sind im bestehenden OHLC-Modell nicht enthalten.
- Daher kann ein bestandener Research-Control **nicht** direkt als Paper-Ready
  oder Live-Ready interpretiert werden. Bei einem positiven Ergebnis folgt
  zunächst ein separater Execution-/Borrow-/Liquidity-Audit.

## Präregistrierter Entscheidungsvertrag

Ein Research-Pass erfordert gleichzeitig:

1. positive Research-Rendite;
2. Research-Drawdown <= 10 %;
3. Research-Profit-Factor >= 1,10;
4. mindestens 30 abgeschlossene Research-Pair-Trades;
5. positives Ergebnis über fünf Research-Rolling-Fenster;
6. Rolling-PF >= 1,10;
7. mindestens 50 % profitable Rolling-Fenster;
8. höchstens 25 % Null-Trade-Rolling-Fenster;
9. durchschnittlicher Rolling-Drawdown <= 10 %;
10. OOS/IS-Return-Verhältnis >= 0,25;
11. positiver Holdout;
12. Holdout-PF >= 1,10;
13. Holdout-Drawdown <= 10 %;
14. mindestens 10 abgeschlossene Holdout-Pair-Trades;
15. Holdout bei 1,5x Kosten nichtnegativ;
16. Holdout bei 2,0x Kosten nichtnegativ.

Bei einem Fehler eines einzigen Vertragskriteriums lautet der Status
NO_SUPPORT / BLOCKED.

Es gibt bewusst **keinen** Nicht-Verschlechterungsvergleich gegen den bestehenden
50/50-Long-only-Kandidaten, weil Trial 034 eine eigenständige market-neutrale
Ertragsquelle und keine Ersatzallokation prüft.

## Auswahlvertrag

- kein Auswahlwettbewerb unter Paaren;
- alle fünf vorab festgelegten Paare werden berichtet;
- Holdout wird erst nach Abschluss der gesamten festen Regel betrachtet;
- kein Pair wird aufgrund von Holdout-Ergebnissen entfernt;
- keine Regeländerung nach Sichtung der Ergebnisse.

## Sicherheitsvertrag

PAPER_ONLY=True

LIVE_TRADING_ENABLED=False

orders_enabled=False

Keine Live-Orders. Keine automatische Promotion.
