# Strategiearchitektur und Literatur-Checkpoint — 2026-09-22

## Ausgangslage

Die bisherige Strategiearchitektur kombiniert kurzes Momentum mit Mean Reversion
und optimiert 1.280 Kandidaten. In der bisherigen Cross-Universe-Evidenz waren
50 von 52 Dataset/Profile-Auswertungen beim OOS-/IS-Renditeverhältnis negativ
und Rolling-WF blieb häufig unter der geforderten Profitabilität.

Das ist kein Beweis, dass systematisches Trading auf unserer Datenbasis
unmöglich ist. Es ist aber ein starkes Signal, dass weitere Mikrooptimierung
derselben Konstruktion nicht der informationsreichste nächste Schritt ist.

## Architektur-Control

Der diagnostische Control verglich den aktuellen Combiner mit Momentum-only und
Mean-Reversion-only. Risiko wurde auf 0,25 Prozent und Hebel auf 1,0 fixiert,
damit die Signalarchitektur isoliert wird.

Ergebnis über SPY, QQQ und IWM:
- Combiner Rolling-OOS-Gesamtprofit: -6,19 EUR
- Momentum-only: -43,55 EUR
- Mean-Reversion-only: -50,16 EUR
- Combiner profitable Rolling-Fensterquote: 53,3 Prozent
- Momentum-only: 33,3 Prozent
- Mean-Reversion-only: 26,7 Prozent
- Combiner Holdout-Gesamtprofit: +31,29 EUR
- Momentum-only: -39,82 EUR
- Mean-Reversion-only: +37,57 EUR

Assetweise:
- SPY Combiner: Rolling-OOS -8,34 EUR, Holdout +22,69 EUR
- QQQ Combiner: Rolling-OOS +11,55 EUR, Holdout +17,68 EUR
- IWM Combiner: Rolling-OOS -9,39 EUR, Holdout -9,07 EUR

Der Combiner ist damit nicht als alleinige Hauptursache belegt. Die IWM-Schwäche
bleibt auch bei niedriger Exposition bestehen.

## Warum die Forschungsrichtung geändert wird

Die externe Literatur untersucht Time-Series Momentum und Trend Following über
wesentlich längere Horizonte und deutlich mehr Märkte als unsere bisherigen
3- bis 21-Tage-Momentumregeln. Moskowitz, Ooi und Pedersen dokumentieren
Time-Series Momentum in 58 liquiden Instrumenten mit Persistenz über etwa
1 bis 12 Monate. citeturn689588search5

Hurst, Ooi und Pedersen finden Trend-Following-Evidenz über ein Jahrhundert und
67 Märkte; die Mehrmarkt-Diversifikation ist ein wesentlicher Bestandteil der
Konstruktion. citeturn689588search7turn890699search33

Szakmary, Shen und Sharma finden bei Moving-Average- und Channel-Regeln in
28 Rohstoffmärkten positive mittlere Excess Returns nach Transaktionskosten
über viele der untersuchten festen Parametrisierungen. citeturn890699search6

Gleichzeitig zeigen Sullivan, Timmermann und White, warum eine große Zahl
getesteter technischer Regeln zu Data-Snooping und überschätzten Ergebnissen
führen kann. citeturn689588search0turn689588search4

Damit ist die methodische Ableitung für uns:
Strategiefamilien zuerst sauber definieren, erst danach begrenzt optimieren.

## Literatur-Strategie-Labor

Auf dem unveränderten 5.000-Candle-Archiv von SPY, QQQ und IWM wurden sechs
feste Referenzfamilien getestet:
- Buy-and-Hold als Referenz
- Time-Series Momentum 126 Tage
- TSM-Ensemble 63/126/252 Tage
- Donchian 55/20
- SMA 50/200 Long/Flat
- Mean Reversion 20/2

Methodik:
- keine Parameteroptimierung
- keine Selection-Profile
- Entscheidung nach Close(t)
- Ausführung nach Open(t+1)
- feste Kosten
- separate ATR-basierte Expositionsskalierung
- keine Produktionsfreigabe

## Verifiziertes Laborergebnis

TSM 126:
- 2 von 3 Assets positiv im Research
- 2 von 3 Assets positiv im Holdout
- 9 von 15 Rolling-Fenstern positiv

TSM-Ensemble 63/126/252:
- 3 von 3 Assets positiv im Research
- 3 von 3 Assets positiv im Holdout
- 11 von 15 Rolling-Fenstern positiv
- Research- und Holdout-PF auf einzelnen Assets meist nahe bzw. über 1,0,
  aber nicht in allen Rolling-Fenstern über dem bestehenden 1,10-Gate

SMA 50/200 Long/Flat:
- 3 von 3 Assets positiv im Research
- 3 von 3 Assets positiv im Holdout
- 12 von 15 Rolling-Fenstern positiv
- Research-Drawdown: SPY 8,80 Prozent, QQQ 6,39 Prozent, IWM 13,73 Prozent
- Holdout-Drawdown: SPY 5,28 Prozent, QQQ 4,78 Prozent, IWM 4,18 Prozent
- Research-PF: SPY 1,132, QQQ 1,170, IWM 1,026
- Holdout-PF: SPY 1,121, QQQ 1,151, IWM 1,075

Donchian 55/20:
- 1 von 3 Assets positiv im Research
- 2 von 3 Assets positiv im Holdout
- 6 von 15 Rolling-Fenstern positiv

Mean Reversion 20/2:
- 0 von 3 Assets positiv im Research
- 1 von 3 Assets positiv im Holdout
- 6 von 15 Rolling-Fenstern positiv

Buy-and-Hold:
- 3 von 3 Assets positiv im Research und Holdout
- 13 von 15 Rolling-Fenstern positiv

Buy-and-Hold ist dabei nur die passive Referenz. Ein positives Ergebnis dieser
Referenz beweist keinen aktiven Strategie-Edge.

## Fachliche Schlussfolgerung

Der bisherige Ansatz war nicht grundsätzlich falsch. Die Research-Governance,
Reproduzierbarkeit, OOS-Trennung und Data-Snooping-Vorsicht sind sinnvoll.

Zu eng war die eigentliche Strategie-Suchmaschine:
- sehr kurze Momentum-Horizonte
- kurze Mean-Reversion-Fenster
- ein fixer gemeinsamer Combiner
- fixer 2-Prozent-Stop
- primär Single-Asset-Betrachtung
- Optimierung über denselben kleinen Regelraum

Der neue Befund spricht dafür, die Forschung auf mittel-/langfristige
Trend-/Momentum-Familien, ehrliche Point-in-Time-Ausführung,
Volatilitätsskalierung und echte Portfolioaggregation auszurichten.

Das ist eine Forschungsneuausrichtung, keine Behauptung einer bereits
gefundenen gewinnsicheren Strategie.

## Nächster Entwicklungsweg

Die nächste Architektur soll getrennte Schichten besitzen:

Signal
→ Position Lifecycle
→ Exit
→ Volatilitätsskalierung
→ Portfolioaggregation

Danach:
1. Multi-Asset-Control
2. gemeinsame Equity-Curve
3. turnover- und kostenbewusste Ausführung
4. Long-only und Long/Short getrennt
5. begrenzte Parametervariation innerhalb einer bereits belegten Familie
6. vollständige WFO-, Rolling-WF-, Robustness-, Overfit- und Holdout-Prüfung

Die bestehenden Gates bleiben bis zu einem eigenständigen Evidenznachweis
unverändert.

## Sicherheitszustand

Paper-Only aktiv.
Live-Trading deaktiviert.
Keine Orders im Research.
Keine automatische Umschaltung auf eine neue Produktionsstrategie.
