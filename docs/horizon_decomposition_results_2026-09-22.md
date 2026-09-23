# Horizon-Dekomposition — Trainingshistorie vs. Holdout

Stand: 2026-09-22

## Kontrollziel

Der 2.500-vs.-5.000-Candle-Horizon-Control zeigte eine deutliche Veränderung
mehrerer OOS-Gates. Dieser neue Kontrolllauf trennt zwei gleichzeitig
veränderte Größen:

| Dimension | Stufe A | Stufe B |
| --- | --- | --- |
| Research-Historie | 2.250 Candles [2250:4500] | 4.500 Candles [0:4500] |
| Holdout | 250 Candles [4500:4750] | 500 Candles [4500:5000] |

Beide Research-Bedingungen enden am identischen Zeitpunkt 2024-09-20.
Beide Holdout-Bedingungen beginnen am 2024-09-23. Die 500er Holdout-Bedingung
ist gegenüber der 250er deshalb ein längerer Beobachtungshorizont und enthält
deren Zeitraum.

Dies ist ausdrücklich kein Replay des historischen 2.500-Candle-Reports.

## Laufidentität

- Universum: `benchmark` — SPY, QQQ, IWM
- Selection-Profile: `score_max`, `boundary_averse`, `risk_averse`, `trade_rich`
- Parameterraum: 1.280 Kandidaten
- Research-Läufe: 24
- 2x2-Zellen: 48
- GitHub Actions Run: `35745158096`
- Artifact-ID: `10702573686`
- Code-Version: `dde541d0d3f98bb88936b6e6adf3ca6a2bb0bd3f`
- Diagnostic-Fingerprint: `031cc1f8a927bf83b94052dfc5fe98ad39d616986775bb391eb32ca70557bef2`
- Datenbasis: jeweils 5.000 Candles, Bereich 2006-11-02 bis 2026-09-21
- Paper-Only: `True`
- Live-Trading: `False`
- Orders: deaktiviert

## 2x2-Gate-Ergebnis

| Gate | 2.250 / H250 | 2.250 / H500 | 4.500 / H250 | 4.500 / H500 | Trainingseffekt | Holdouteffekt |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `data_quality` | 12/12 | 12/12 | 12/12 | 12/12 | 0,0 pp | 0,0 pp |
| `backtest` | 4/12 | 4/12 | 0/12 | 0/12 | -33,3 pp | 0,0 pp |
| `walk_forward` | 2/12 | 2/12 | 5/12 | 5/12 | +25,0 pp | 0,0 pp |
| `rolling_walk_forward` | 3/12 | 3/12 | 2/12 | 2/12 | -8,3 pp | 0,0 pp |
| `robustness` | 3/12 | 3/12 | 5/12 | 5/12 | +16,7 pp | 0,0 pp |
| `overfit` | 1/12 | 1/12 | 4/12 | 4/12 | +25,0 pp | 0,0 pp |
| `holdout` | 1/12 | 3/12 | 0/12 | 6/12 | +8,3 pp | +33,3 pp |

Die Trainingseffekte sind deskriptive Haupteffekte des kontrollierten
2x2-Designs. Wegen diskreter Gate-Passraten und kleiner Asset/Profile-Zahl
sind sie kein statistischer Kausalitätsbeweis.

## Trainingshistorie

Unter identischem Research-Endpunkt verbessert zusätzliche Historie:

- WFO: 2/12 -> 5/12
- Robustness: 3/12 -> 5/12
- Overfit: 1/12 -> 4/12

Gleichzeitig verschärft sie:

- Baseline-Backtest: 4/12 -> 0/12
- Rolling-WF: 3/12 -> 2/12

Damit lässt sich die ursprüngliche Verbesserung von WFO, Robustness und
Overfit wesentlich enger der Trainingshistorie zuordnen als im ursprünglichen
2.500-vs.-5.000-Vergleich.

## Holdout-Horizont

Die Holdout-Größe verändert ausschließlich das Holdout-Gate:

- kurzer Trainingsarm: 1/12 -> 3/12
- langer Trainingsarm: 0/12 -> 6/12

Die Auswahl bleibt innerhalb desselben Trainingsarms identisch. Der Holdout
beginnt in beiden Fällen am gleichen Datum. Der Unterschied misst daher einen
zusätzlichen Folgezeitraum von 250 Daily-Candles, nicht nur eine größere
Stichprobengröße.

## Rolling-WF

Rolling-WF ist der wichtigste Sonderfall:

- kurze Trainingshistorie: 3/12
- lange Trainingshistorie: 2/12
- Holdout-Größe: kein Effekt

Die Verbesserung 0/12 -> 2/12 aus dem historischen 2.500-vs.-5.000-Control
wird damit nicht durch zusätzliche Trainingshistorie allein erklärt. Der
Befund ist vereinbar mit einem kombinierten Einfluss aus verändertem
Untersuchungszeitraum und veränderter Rolling-WF-Fenstergeometrie.

## Kandidaten-Dynamik

10 von 12 Asset/Profile-Kombinationen ändern den WFO-selected candidate zwischen
2.250 und 4.500 Research-Candles.

| Parameter | Änderungen |
| --- | ---: |
| `mean_reversion.window` | 7/12 |
| `mean_reversion.threshold` | 6/12 |
| `momentum.lookback` | 5/12 |
| `risk_per_trade` | 2/12 |
| `leverage` | 0/12 |

| Asset | Kandidatenwechsel |
| --- | ---: |
| SPY | 3/4 |
| QQQ | 4/4 |
| IWM | 3/4 |

Die Holdout-Größe verändert den Kandidaten innerhalb derselben Trainingsbedingung
nicht.

## Wiederkehrende Failure-Kriterien

| Gate | Kurzer Trainingsarm | Langer Trainingsarm |
| --- | ---: | ---: |
| Rolling-WF: PF unter Minimum | 9/12 | 10/12 |
| Rolling-WF: Gesamtprofit nicht positiv | 8/12 | 8/12 |
| Rolling-WF: profitable Fensterquote unter Minimum | 6/12 | 8/12 |
| WFO: PF unter Minimum | 9/12 | 7/12 |
| WFO: OOS-Profit nicht positiv | 9/12 | 7/12 |
| Robustness: profitable Variantenquote unter Minimum | 6/12 | 7/12 |
| Robustness: Stresskosten-Failure | 9/12 | 7/12 |
| Overfit: OOS-/IS-Ratio unter Minimum | 11/12 | 8/12 |

Im ursprünglichen 2.500-vs.-5.000-Control blieben insbesondere folgende
Failure-Arten über beide Horizonte bestehen:

- Rolling-WF: `profit_factor` 10/12 in beiden Horizonten
- Overfit: `oos_to_is_ratio` 11/12 -> 8/12
- WFO: `profit_factor` 10/12 -> 7/12
- Robustness: Stresskosten-Failure 10/12 -> 7/12

Die Kriterien sind nicht exklusiv; eine Auswertung kann mehrere Failure-Arten
gleichzeitig enthalten.

## Schlussfolgerung

1. Zusätzliche Trainingshistorie erklärt einen wesentlichen Teil der
   Verbesserung bei WFO, Robustness und Overfit.
2. Der Holdout-Horizont hat einen eigenständigen und deutlichen Effekt auf
   das Holdout-Gate.
3. Rolling-WF wird weder durch den Holdout-Horizont beeinflusst noch durch
   zusätzliche Trainingshistorie verbessert.
4. Der verbleibende Rolling-WF-Unterschied aus dem historischen Horizon-Control
   braucht deshalb eine eigene zeit-/fensterbezogene Analyse.

Bis dahin bleiben Strategie, Parameterraum, Selection-Profile und Gates
unverändert.