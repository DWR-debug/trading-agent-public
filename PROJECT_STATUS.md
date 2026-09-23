# Trading Agent — Entwicklungsstand und Zielbild

Stand: 2026-09-23
Basis: aktueller `master`-Stand nach PR #33.

## Aktueller Forschungscheckpoint — 2026-09-23

### Sicherheitsstatus

- `PAPER_ONLY = True`
- `LIVE_TRADING_ENABLED = False`
- keine Live-Ausführung
- keine Research-Orders
- keine Gate-Lockerung
- keine automatische Aktivierung von Short-/Leverage-Micro-Trading

### Evidenzlage des täglichen Kandidaten

Der unveränderte 50/50 + 10%-Vol-Budget-Kandidat wurde auf drei vollständig
symbol-disjunkten Validierungssätzen geprüft. Die Holdouts waren positiv, die
Risiko-/Rolling-Gates jedoch wiederholt unzureichend. Der gemeinsame Failure-
Fingerprint umfasst insbesondere Holdout-Drawdown, Research-Drawdown,
Rolling-Durchschnittsdrawdown und Rolling-Profit-Factor.

Der 63-Sessions-/10%-Vol-Control dämpft den Drawdown replizierbar, reduziert
aber ebenfalls Return und Profit Factor. Der 21-Sessions-Control zeigt keinen
konsistenten Holdout-Vorteil. Timing-, sleeve-spezifische und Event-Analysen
ergaben keinen replizierten Änderungsgrund.

### Micro-/Intraday-Controls

#### PR #32 — Long/Flat 15m Sidecar

PR #32 ist gemerged.

Kontrollsatz:
- BTCUSDT + ETHUSDT
- 15-Minuten-Bars
- 100.000 Candles je Asset
- 80% Research / 20% Holdout
- 5 feste Research-Rolling-Fenster
- keine Optimierung und keine Auswahl zwischen Hypothesen
- Point-in-Time-Ausführung: abgeschlossenes Signalbar -> nächster Open -> derselbe Close

Vorab getestete Hypothesen:
- Continuation: Long nach positivem Vorbar
- Reversal: Long nach negativem Vorbar

Befund im Holdout:
- beide Long/Flat-Hypothesen fallen unter dem getesteten Kostensatz auf nahezu -100%
- Buy-and-Hold über BTC/ETH war im selben Kontrolllauf deutlich positiv
- der Sidecar ist damit kein Produktionskandidat

Technischer Kontrollstatus:
- 399 Tests
- Paper-Only-Safety grün
- Ergebnis-Fingerprint geprüft
- Research-Daten und Ergebnis als GitHub-Artifact archiviert

#### PR #33 — Directional Short/Long + fester Hebel

PR #33 ist gemerged.

Der Kontrollsatz wurde vollständig symbol-disjunkt zum ersten Micro-Sidecar
gewählt:
- SOLUSDT
- BNBUSDT
- XRPUSDT
- ADAUSDT

Unveränderte 15m-/100k-/80:20-Geometrie; zusätzlich feste Exposure-Stufen
1x / 2x / 3x und Kosten-Sensitivität 0x / 0,5x / 1x / 2x / 4x des bestehenden
0,15%-Projekt-Basissatzes.

Vorab feste Richtungs-Hypothesen:
- Directional continuation: positiv -> Long, negativ -> Short
- Directional reversal: positiv -> Short, negativ -> Long

Holdout-Befund, 0x Kosten:
- Continuation 1x: -43,89%, DD 55,38%, PF 0,966
- Continuation 2x: -71,92%, DD 81,60%, PF 0,966
- Continuation 3x: -87,46%, DD 92,98%, PF 0,966
- Reversal 1x: +58,88%, DD 28,06%, PF 1,036
- Reversal 2x: +124,94%, DD 49,88%, PF 1,036
- Reversal 3x: +183,60%, DD 66,19%, PF 1,036

Der Reversal-Befund ist ausschließlich vor Kosten positiv und zugleich extrem
turnover-intensiv:
- 1x Holdout-Turnover: 20.653,5 Portfolio-Einheiten
- 3x Holdout-Turnover: 61.960,5
- bereits bei 0,5x Kosten (~0,075% je Turnover-Einheit) fällt der Holdout
  bei 1x, 2x und 3x auf nahezu -100% und PF deutlich unter 1

Die 3x-Ergebnisse sind deshalb keine belastbare Aussage über "schnelle hohe
Gewinne". Der Hebel skaliert hier einen nur knapp positiven Vor-Kosten-PF und
gleichzeitig die Drawdown- und Ausführungsexponierung. Die Long/Short-Frage
bleibt damit als Forschungsfrage interessant, aber der bisher gemessene Edge
ist nicht kostentragfähig.

Technischer Kontrollstatus:
- 403 Tests
- Paper-Only-Safety grün
- Hebelobergrenze 3x geprüft
- Integritäts-Fingerprint geprüft
- symbol-disjunkte Datenbasis und Research-Artifact archiviert
- keine Orders, keine Produktionsintegration

### Gesamtkonsequenz

Die Micro-Controls verändern den täglichen ETF-Kandidaten nicht.

Die bisherige Evidenz rechtfertigt derzeit:
- keinen Produktionswechsel auf Intraday/Micro-Trading
- keine globale Aktivierung von Shorting
- keine Erhöhung des Projekt-Hebels über 3x
- keine datengetriebene Auswahl einer Micro-Hypothese anhand dieses Holdouts

Die einzige methodisch offene und direkt aus PR #33 ableitbare Kontrollfrage ist
nun die **Kosten-/Turnover-These**: Bleibt die Reversal-Spur bestehen, wenn die
Position nicht nach jedem einzelnen 15m-Bar neu gedreht wird, sondern nur über
vorab feste längere Holding-Horizonte gehalten wird?

Der nächste Control bleibt deshalb streng präregistriert:
- neues symbol-disjunktes Universum
- beide Richtungs-Hypothesen weiterhin parallel
- feste Holding-Horizonte
- feste 1x / 2x / 3x Exposure
- feste Kosten-Stressstufen
- kein Tuning, keine Hypothesen-Auswahl, keine Produktionsintegration

Erst ein positives, kostenrobustes und unabhängig repliziertes Muster würde einen
weiteren realistischeren Execution-Control rechtfertigen.

## Sicherheitsgrundsatz

Der Trading Agent bleibt bis zu einer ausdrücklichen Freigabe ausschließlich im Paper-Trading-/Simulationsmodus.

Aktueller Sicherheitszustand:
- `PAPER_ONLY = True`
- `LIVE_TRADING_ENABLED = False`
- keine Orderausführung im Research-Workflow

Diese Bedingung ist ein nicht verhandelbares Gate für weitere Entwicklung.

## Erreicht

### Engineering und Trading-Sicherheit
- Risk Engine und Paper Broker vorhanden.
- Portfolio-Risk-Controller mit Daily-Loss- und Drawdown-Kill-Switch.
- Begrenzung offener Positionen und maximale Hebelwirkung.
- Trading Engine integriert.
- Automatisierte Tests und Safety Checks.

### Backtesting und Validierung
- Backtesting-Engine und Metriken.
- Parameter-Space und Optimierung.
- Walk-Forward- und Rolling-Walk-Forward-Validierung.
- Beschleunigte Signal-/Optimierungspfade.
- Automatisierter Backtest-Analyse-Runner.
- Research-Gates mit sieben kontrollierten Qualitätsprüfungen.

### Marktdaten
- Lokaler Market-Data-Store.
- Binance Historical Market-Data Loader.
- Historischer Mehrfachabruf.
- Automatischer Updater.
- Reproduzierbare Research-Datensätze mit Fingerprints.
- Research-Datenqualitäts-Gates für Intervall, Lücken, OHLC, Volumen, Freshness und geschlossene Candles.

### Research-Automation
- Automatischer Research-Datenworkflow.
- Manuelle, geplante und relevante Push-Trigger.
- Research-Manifest mit Daten-Fingerprints.
- Workflow-Provenienz im Manifest.
- Separate CI für normale Entwicklung.
- ARM64-CI und Paper-Only-Safety-Gates.
- Atomare Checkpoints und Resume-Funktion für lokale Multi-Dataset-Research-Läufe.

## Aktuelle Checkpoints

### PR #10
Status: **gemerged**

PR #10 hat die Reproduzierbarkeit verbessert:
- Commit-SHA
- Workflow
- Run-ID
- Run-Versuch
- Trigger
- Ref

werden im Research-Manifest festgehalten.

### PR #11
Status: **gemerged**

PR #11 ergänzt Research-Datenqualitäts-Gates:
- exakte Candle-Anzahl
- erwartetes Intervall
- keine Zeitlücken
- keine doppelten Timestamps
- keine zukünftigen Candles
- Freshness
- OHLC-Konsistenz
- nichtnegatives Volumen
- nur vollständig geschlossene letzte Candle

Der Merge-Commit ist Bestandteil des aktuellen `master`-Stands.

## Selection-Profile-Experiment 2026-09-22

PR #27 ist gemerged. Der erste vollständige Selection-Profile-Vergleich für
`small_cap_high_volatility` wurde auf dem ARM64-GitHub-Runner ausgeführt.

Forschungsinput:
- 5 Aktien: SOUN, RKLB, IONQ, ASTS, HIMS
- gemeinsame Historie: 1000 Daily-Candles je Asset
- Datenbereich: 2022-09-23 bis 2026-09-18
- identisches Datenmanifest für alle Profile
- vier Profile: `score_max`, `boundary_averse`, `risk_averse`,
  `trade_rich`

Ergebnis:
- Experimentstatus: `COMPLETED`
- alle vier Profilruns: gültiger Researchstatus `BLOCKED` und
  Klassifikation `REJECT`
- technische Vorprüfungen und vollständige Testsuite: grün
- Paper-Only-Sicherheitsprüfung: grün
- Artifact-Archivierung: erfolgreich
- Experiment-Fingerprint:
  `0132e9e044f2beda1a08f678d2b2bac2106519ca99ed76667cd9e53d807fd455`
- GitHub Actions Run: `35729214142`
- Artifact-ID: `10694119776`
- Evidenzfamilien-Fingerprint: `c96fe74ba87240065eb185f09e9e756c0bcd6aa362765ac827650f58f569b8f7`
- Evidenzfamilie: 4 Reports, 20 Dataset-Auswertungen, 4 eindeutige Run-Fingerprints
- Aktuelle vollständige CI-Suite auf dem Research-Workflow: `242 passed`
- Gate-Failure-Matrix der 20 Dataset-Auswertungen: `data_quality 20/20`, `backtest 0/20`, `walk_forward 7/20`, `rolling_walk_forward 3/20`, `robustness 10/20`, `overfit 0/20`, `holdout 10/20`
- Das `backtest`-Gate ist ein `baseline_sanity`-Gate; es scheiterte in allen 20 Fällen am Drawdown-Limit. Selection-Profile verändern diesen Baseline-Befund nicht.
- Das `overfit`-Gate scheiterte in allen 20 Fällen am geforderten OOS-/IS-Renditeverhältnis; die beobachtete OOS-/IS-Ratio lag jeweils unter `0.25`.

Gate-Befund über 5 Assets:
- `backtest`: 0/5 bestanden bei allen Profilen
- `overfit`: 0/5 bestanden bei allen Profilen
- `walk_forward`: 0/5 boundary_averse, 3/5 risk_averse, 1/5 score_max,
  3/5 trade_rich
- `rolling_walk_forward`: 1/5 boundary_averse, 0/5 risk_averse,
  1/5 score_max, 1/5 trade_rich
- `robustness`: 1/5 boundary_averse, 3/5 risk_averse, 3/5 score_max,
  3/5 trade_rich
- `holdout`: 2/5 boundary_averse, 3/5 risk_averse, 2/5 score_max,
  3/5 trade_rich
- data_quality: 5/5 bestanden in allen Profilen
- Rolling-WF-Null-Trading-Fenster: 0 % in diesem Lauf

Diagnostischer Befund:
Der Selection-Layer verändert die ausgewählten Kandidaten tatsächlich. Das
Kontrollprofil `score_max` wählt weiterhin sehr hohe In-Sample-Renditen;
die durchschnittliche Rendite des jeweils ausgewählten Top-Kandidaten lag
bei ca. 458 %. `boundary_averse` reduzierte diesen Wert auf ca. 43 %,
beseitigte aber weder das Overfit-Gate noch erzeugte es bestandene WFO-Gates.
Der erste Lauf bestätigt daher, dass die Auswahlregel einen wesentlichen
Einfluss auf die In-Sample-Auswahl hat, liefert aber noch keinen Nachweis,
dass eine einzelne alternative Auswahlregel die Robustheitsprobleme löst.

Die Rohreports und Checkpoints liegen im GitHub-Artifact des Runs und werden
nicht in den Quellbranch geschrieben.

## Benchmark-Selection-Profile-Experiment 2026-09-22

Der erste Cross-Universe-Replikationslauf auf `benchmark` wurde erfolgreich abgeschlossen.

Forschungsinput:
- 3 Datasets: SPY, QQQ, IWM
- 2.500 Daily-Candles je Asset
- Datenbereich: 2016-10-07 bis 2026-09-18
- vier Selection-Profile
- gemeinsames vorbereitetes Datenmanifest
- GitHub Actions Run: `35731263325`
- Artifact-ID: `10695925573`
- Experiment-Fingerprint: `76b2785f9069e41c44b9638d5544cdb5a8cfc6ce4455166f4d52aebe702bf294`
- Evidenzfamilien-Fingerprint: `07be43e6bfc4823dd91c6f4eca8813c3268622674f97d84138432fb4151209bb`

Ergebnis:
- Experimentstatus: `COMPLETED`
- alle vier Profilruns: `BLOCKED` und Klassifikation `REJECT`
- vollständige Testsuite im Workflow: grün
- Paper-Only-Sicherheitsprüfung: grün
- 12 Dataset-Auswertungen insgesamt

Gate-Matrix über alle 12 Dataset-Auswertungen:
- `data_quality`: 12/12
- `backtest`: 4/12
- `walk_forward`: 1/12
- `rolling_walk_forward`: 0/12
- `robustness`: 2/12
- `overfit`: 1/12
- `holdout`: 2/12

Interpretation:
- Der `backtest`-Befund stammt aus der Baseline-Sanity-Prüfung und ist daher nicht von der Selection-Profilwahl abhängig.
- Die schwachen OOS-Gates (`walk_forward`, `rolling_walk_forward`, `overfit`) bleiben auch auf dem unabhängigen Benchmark-Universum sichtbar.
- Holdout-Ergebnisse sind gemischt und rechtfertigen keine Profil-Rangfolge.
- Der Lauf dient der Cross-Universe-Replikation und Ursachenabgrenzung, nicht der Auswahl eines „besten“ Profils.

Damit liegen jetzt zwei kontrollierte Evidenzfamilien auf getrennten Universen vor: `small_cap_high_volatility` und `benchmark`. Vor weiteren Selection-Profilvarianten ist die nächste sinnvolle Phase eine systematische Diagnose der ausgewählten Kandidaten über OOS, Rolling-WF, Robustness, Overfit und Holdout.

## Long-Horizon-Control Benchmark 2026-09-22

Der separate Horizon-Control-Lauf auf `benchmark` wurde erfolgreich abgeschlossen.

Forschungsinput:
- SPY, QQQ, IWM
- 5.000 Daily-Candles je Asset
- 4 Selection-Profile
- unveränderter Parameterraum mit 1.280 Kandidaten
- unveränderte Research-Gates, Schwellenwerte, Gebühren, Slippage und Holdout-Regeln
- gemeinsames Datenmanifest mit 5.000 Candles je Asset
- 4.500 Research-Candles + 500 Holdout-Candles je Asset

Technischer Zustand:
- Experimentstatus: `COMPLETED`
- Workflowstatus: `success`
- alle vier Profilruns: `BLOCKED` / `REJECT`
- vollständige Testsuite im Workflow: grün
- Paper-Only-Sicherheitsprüfung: grün
- keine Orderausführung
- GitHub Actions Run: `35742631852`
- Artifact-ID: `10699853862`
- Experiment-Fingerprint: `3ee18c1ed7c1e067a683230cd69f56cdf36ea4f74227a267d85d1d03c19ddd0f`

Gate-Matrix über 12 Dataset/Profile-Auswertungen:
- `data_quality`: 12/12
- `backtest`: 0/12
- `walk_forward`: 5/12
- `rolling_walk_forward`: 2/12
- `robustness`: 5/12
- `overfit`: 4/12
- `holdout`: 6/12

Kontrollvergleich zum 2.500-Candle-Benchmark:
- `walk_forward`: 1/12 -> 5/12
- `rolling_walk_forward`: 0/12 -> 2/12
- `robustness`: 2/12 -> 5/12
- `overfit`: 1/12 -> 4/12
- `holdout`: 2/12 -> 6/12
- profitable Rolling-WF-Fenster: 19/60 -> 22/60

Der längere Horizont verändert damit die Evidenzlage messbar, beseitigt das Generalisierungsproblem aber nicht. Das `backtest`-Gate ist als `baseline_sanity` selection-unabhängig und scheitert im 5.000-Candle-Lauf in allen 12 Fällen am 10-%-Drawdown-Limit; deshalb bleibt auch kein Datensatz formal vollständig bestanden.

Kandidaten-Dynamik:
- Rolling-/WFO-Kandidaten-Übereinstimmung verändert sich gegenüber 2.500 Candles deutlich.
- Die Veränderung ist profilabhängig; sie wird nicht als Profilrangfolge interpretiert.
- Der Horizon-Control zeigt damit zusätzlich, dass die verlängerte Historie die Auswahlstruktur selbst beeinflussen kann.

Fachliches Zwischenfazit:
Der 5.000-Candle-Lauf ist als eigenständiger Kontrollcheckpoint bestätigt. Die höhere Historientiefe führt zu mehr bestandenen kandidatenbezogenen OOS-/Robustness-/Overfit-/Holdout-Gates, während Rolling-WF weiterhin der zentrale Engpass bleibt. Der nächste Forschungsschritt sollte den Horizon-Effekt weiter zerlegen, insbesondere zusätzliche Trainingshistorie gegenüber der vergrößerten Holdout-Stichprobe, bevor Parameterraum, Strategie oder Gates verändert werden.

Vollständige Vergleichsdokumentation:
`docs/long_horizon_control_2026-09-22.md`

## Horizon-Dekomposition 2026-09-22

PR #63 ist gemerged. Der anschließende kontrollierte 2x2-Lauf auf dem
`benchmark`-Universum wurde erfolgreich abgeschlossen.

Kontrolliertes Design:
- Research-Historie: 2.250 Candles [2250:4500] versus 4.500 Candles [0:4500]
- Holdout: 250 Candles [4500:4750] versus 500 Candles [4500:5000]
- beide Research-Arme enden am identischen Punkt; beide Holdout-Arme beginnen
  am identischen Punkt
- vier unveränderte Selection-Profile, 1.280 Kandidaten, unveränderte Gates,
  Gebühren, Slippage und Paper-Only-Safety
- 24 Research-Läufe und 48 Dataset/Profile/Split-Zellen
- GitHub Actions Run: `35745158096`
- Artifact-ID: `10702573686`
- Diagnostic-Fingerprint:
  `031cc1f8a927bf83b94052dfc5fe98ad39d616986775bb391eb32ca70557bef2`
- Code-Version:
  `dde541d0d3f98bb88936b6e6adf3ca6a2bb0bd3f`

Haupteffekte auf die Gate-Passrate:
- `walk_forward`: Trainingseffekt +25,0 Prozentpunkte; Holdout-Effekt 0
- `rolling_walk_forward`: Trainingseffekt -8,3 Prozentpunkte; Holdout-Effekt 0
- `robustness`: Trainingseffekt +16,7 Prozentpunkte; Holdout-Effekt 0
- `overfit`: Trainingseffekt +25,0 Prozentpunkte; Holdout-Effekt 0
- `holdout`: Trainingseffekt +8,3 Prozentpunkte; Holdout-Effekt +33,3 Prozentpunkte
- `backtest`: Trainingseffekt -33,3 Prozentpunkte; Holdout-Effekt 0
- `data_quality`: unverändert 12/12

Die Holdout-Größenprüfung verändert bei identischer Trainingsbedingung den
ausgewählten Kandidaten nicht. Damit ist der Holdout-Effekt von einer
Selection-Änderung getrennt.

Kandidaten-Dynamik:
- 10 von 12 Asset/Profile-Kombinationen ändern ihren WFO-selected candidate
  zwischen 2.250 und 4.500 Research-Candles.
- Betroffen sind vor allem `mean_reversion.window` (7/12),
  `mean_reversion.threshold` (6/12) und `momentum.lookback` (5/12).
- `risk_per_trade` ändert sich in 2/12 Fällen; `leverage` in keinem Fall.
- Die Änderungen treten bei SPY in 3/4, QQQ in 4/4 und IWM in 3/4 Profilen auf.

Failure-Kriterien:
- Rolling-WF bleibt von `profit_factor` besonders stark geprägt:
  9/12 Failure-Fälle im kurzen Trainingsarm und 10/12 im langen.
- `overfit` bleibt trotz deutlicher Verbesserung ein wiederkehrendes Problem:
  OOS-/IS-Ratio unter Minimum in 11/12 kurzen und 8/12 langen Trainingsarmen.
- Robustness bleibt häufig kosten-/variantenabhängig:
  Stress-Kosten-Failure 9/12 kurz und 7/12 lang.
- WFO-PF-Failure sinkt mit zusätzlicher Trainingshistorie von 9/12 auf 7/12,
  bleibt aber häufig.
- Holdout-Failures sind stark von der Holdout-Größe abhängig; der 500-Candle-
  Holdout beginnt am gleichen Datum wie der 250-Candle-Holdout und enthält
  zusätzlich dessen späteres Folgejahr. Der Effekt ist deshalb ein
  Holdout-Horizont-/Stichprobeneffekt und kein reiner statistischer
  'mehr Beobachtungen'-Effekt.

Wichtigster Befund:
Die Verbesserung von WFO, Robustness und Overfit im ursprünglichen
2.500-vs.-5.000-Candle-Vergleich ist unter dem kontrollierten gemeinsamen
Research-Endpunkt klar mit der zusätzlichen Trainingshistorie vereinbar.
Der Rückgang des Backtest-Baseline-Gates ist im selben Kontrollarm ebenfalls
sichtbar. Dagegen wird die Rolling-WF-Verbesserung des ursprünglichen
2.500-vs.-5.000-Vergleichs nicht durch zusätzliche Trainingshistorie erklärt:
im gemeinsamen-Endpunkt-Control sinkt die Rolling-WF-Passrate sogar von 3/12
auf 2/12, während die Holdout-Größe keinen Einfluss auf dieses Gate hat.

Damit ist Rolling-WF als eigenständiger diagnostischer Engpass bestätigt.
Die nächste Research-Stufe ist daher eine zeit-/fensterbezogene Zerlegung
der Rolling-WF-Differenz, einschließlich Window-Geometrie, Kandidatenwechsel
und konkreter Failure-Kriterien. Strategie, Parameterraum, Selection-Profile
und Gates bleiben bis dahin unverändert.

## Liquid-High-Volatility-Selection-Profile-Experiment 2026-09-22

Der dritte kontrollierte Cross-Universe-Lauf auf `liquid_high_volatility` wurde erfolgreich abgeschlossen.

Forschungsinput:
- 5 Aktien: NVDA, AMD, TSLA, COIN, PLTR
- gemeinsame Historie: 1.000 Daily-Candles je Asset
- Datenbereich: 2022-09-23 bis 2026-09-18
- 900 Research-Candles + 100 Holdout-Candles je Asset
- gemeinsames vorbereitetes Datenmanifest
- vier Selection-Profile
- GitHub Actions Run: `35732439851`
- Artifact-ID: `10696625568`
- Experiment-Fingerprint: `48654c5297e14b13b3d40b5c9c93db25fbedcc4d7204a54d5feacad568727845`
- Evidenzfamilien-Fingerprint: `60770e8df46416c0c5afccd2739250462118d4d7c53958452dd09fa5b7e39bd9`

Technischer Zustand:
- Experimentstatus: `COMPLETED`
- Workflowstatus: `success`
- alle vier Profilruns: `BLOCKED` und Klassifikation `REJECT`
- vollständige Testsuite im Workflow: grün
- Paper-Only-Sicherheitsprüfung: grün
- keine Orderausführung im Research-Workflow
- Evidenzfamilie: 4 Reports, 20 Dataset-Auswertungen, 4 eindeutige Run-Fingerprints
- Datenqualität: 20/20 bestanden

Gate-Matrix über alle 20 Dataset-Auswertungen:
- `backtest` / Scope `baseline_sanity`: 0/20
- `walk_forward` / Scope `selected_candidate_oos`: 7/20
- `rolling_walk_forward` / Scope `rolling_selected_candidate_oos`: 3/20
- `robustness` / Scope `selected_candidate_robustness`: 6/20
- `overfit` / Scope `selected_candidate_train_vs_oos`: 1/20
- `holdout` / Scope `selected_candidate_holdout`: 7/20

Wesentliche Detailbefunde:
- Das `backtest`-Gate scheiterte wie im ersten Kontrolluniversum in allen 20 Fällen am Baseline-Drawdown-Limit; dieser Befund ist ausdrücklich nicht selection-profilabhängig.
- Das `overfit`-Gate bestand nur in 1/20 Fällen. Damit bleibt das Verhältnis zwischen In-Sample- und OOS-Rendite über die meisten ausgewählten Kandidaten hinweg ein wiederkehrendes Problem.
- Das Rolling-Walk-Forward-Gate bestand nur in 3/20 Fällen; Null-Trading-Fenster traten dabei nicht auf.
- Holdout und Robustness sind gemischt: einzelne Kandidaten bestehen diese Gates, aber nicht in einer Weise, die zu durchgehend bestandenen Datensätzen führt.
- Die Selection-Profile verändern die tatsächlich ausgewählten Kandidaten. Der Lauf liefert aber keinen Nachweis dafür, dass eines der vier Profile die beobachteten Generalisierungsprobleme über das Universum hinweg beseitigt.

Cross-Universe-Befund nach drei kontrollierten Evidenzfamilien:
- `small_cap_high_volatility`: 20 Dataset-Auswertungen
- `benchmark`: 12 Dataset-Auswertungen
- `liquid_high_volatility`: 20 Dataset-Auswertungen
- insgesamt: 52 Dataset-Auswertungen
- `data_quality`: 52/52
- `backtest`: 4/52
- `walk_forward`: 15/52
- `rolling_walk_forward`: 6/52
- `robustness`: 18/52
- `overfit`: 2/52
- `holdout`: 19/52

Interpretation:
Die drei getrennten Kontrolluniversen bestätigen die technische Reproduzierbarkeit des Research-Pfads und zeigen zugleich ein wiederkehrendes Muster bei den kandidatenbezogenen OOS-/Generalisierungsprüfungen. Das ist noch keine Aussage über die Ursache auf Strategieebene, aber ausreichend Evidenz dafür, vor weiteren Selection-Profilvarianten zunächst die ausgewählten Kandidaten und die konkreten Gate-Kriterien diagnostisch auseinanderzunehmen.

Die Gates, Schwellenwerte und Selection-Profile wurden für diesen Kontrolllauf nicht verändert. Die Permutationsdiagnostik bleibt wie vorgesehen rein diagnostisch, unadjustiert und wird nicht zu einer künstlichen Gesamt-Signifikanz zusammengeführt.

Die Rohreports und Checkpoints liegen im GitHub-Artifact des Runs und werden nicht in den Quellbranch geschrieben.


## Systematische Gate- und Kandidaten-Diagnose 2026-09-22

Nach der dritten kontrollierten Cross-Universe-Replikation wurde die fachliche
Diagnose erweitert, ohne Research-Gates, Schwellenwerte, Parameterraum oder
Selection-Profile zu verändern.

PR #54 ist gemerged:
- strukturierte Failure-Kriterien aus den bereits vorhandenen Gate-Details
- nicht-exklusive Kriterienzählung
- Gesamt- und profilbezogene Failure-Diagnostik
- fehlgeschlagene Kriterien zusätzlich pro Dataset im Evidence Summary

PR #55 ist gemerged:
- Kandidatenakte pro Dataset/Profile
- deterministischer Selected-Candidate-Fingerprint
- bereits berechnete WFO/OOS-, Rolling-WF-, Robustness-, Overfit- und
  Holdout-Metriken in gemeinsamer diagnostischer Struktur
- keine erneute Research-Berechnung für die Diagnose

Erste fachliche Auswertung über die drei archivierten Kontrolluniversen:
- 52 Dataset/Profile-Auswertungen insgesamt
- `backtest`-Drawdown-Kriterium verletzt: 48/52
- `walk_forward`-OOS/Profit-Kriterium:
  - OOS-Profit nicht positiv: 25/52
  - Profit Factor unter Minimum: 32/52
  - OOS-Drawdown über Maximum: 19/52
- `rolling_walk_forward`:
  - profitable-window-Quote unter Minimum: 43/52
  - Profit Factor unter Minimum: 35/52
  - Gesamtprofit nicht positiv: 31/52
  - zu wenige Trades: 4/52
- `robustness`:
  - gestresster Nettoprofit negativ: 32/52
  - profitable Variantenquote unter Minimum: 25/52
- `overfit`:
  - OOS-/IS-Ratio unter Minimum: 50/52
  - nichtpositiver Train-Return: 13/52
- `holdout`:
  - Profit Factor unter Minimum: 31/52
  - Nettoprofit nicht positiv: 26/52
  - zu wenige Trades: 7/52
  - Drawdown über Maximum: 2/52

Die Failure-Kriterien sind ausdrücklich nicht exklusiv: eine einzelne
fehlgeschlagene Gate-Auswertung kann mehrere Bedingungen gleichzeitig
verletzen. Die Zahlen sind daher keine additiven Fehlerursachen.

Fachliche Bedeutung:
- Das häufigste kandidatenbezogene Muster ist das zu schwache OOS-/IS-
  Renditeverhältnis; dies betrifft 50 von 52 Auswertungen.
- Rolling-WF zeigt zusätzlich eine wiederkehrend zu geringe Quote profitabler
  Zeitfenster.
- Robustness und Holdout liefern gemischte Befunde, zeigen aber wiederkehrend
  Schwächen bei Profitabilität, Profit Factor und Kostensensitivität.
- Die drei Kontrolluniversen zeigen unterschiedliche ausgewählte Kandidaten
  je Selection-Profil; die Diagnose dient deshalb der Ursachenabgrenzung und
  nicht einer Profilrangfolge.

Nächste fachliche Stufe:
Die vorhandenen Kandidatenakten werden nun zeitlich und kandidatenbezogen
auseinandergelegt. Insbesondere werden Rolling-WF-Fenster, WFO-OOS-Metriken,
Holdout-Metriken und Robustness-Befunde auf wiederkehrende Muster je Asset und
Kandidatenstruktur geprüft. Ziel ist eine belastbare Ursachenbeschreibung,
nicht die Anpassung bestehender Gates.


## Zeit- und Kandidaten-Diagnose 2026-09-22

Die archivierten Reports der drei kontrollierten Universen wurden über alle
260 Rolling-Walk-Forward-Fenster hinweg ausgewertet. Diese Analyse nutzt
ausschließlich bereits berechnete Research-Ergebnisse und verändert keine
Research-Gate-Entscheidung.

Zeitliche Befunde:
- 260 Rolling-WF-Fenster insgesamt
- 91 Fenster mit positivem Nettoprofit
- damit 35,0 % profitable Fenster über die gesamte Familie
- profitable Fenster je Fensterposition:
  - Fenster 1: 18/52
  - Fenster 2: 20/52
  - Fenster 3: 17/52
  - Fenster 4: 22/52
  - Fenster 5: 14/52
- In allen fünf Positionen liegt der Median-Nettoprofit unter null.
- Das fünfte Rolling-Fenster weist mit 14/52 die niedrigste Profitabilitätsquote
  auf; das vierte mit 22/52 die höchste. Kein einzelnes Fenster erreicht die
  50-%-Marke über die gesamte Evidenzfamilie.

Kandidaten-Dynamik:
- Pro Dataset existieren fünf Rolling-WF-Fenster mit jeweils eigener
  In-Sample-Auswahl.
- Der in den Rolling-Fenstern gewählte Kandidat entspricht im Mittel nur in
  45,4 % der Fenster dem festen WFO-Kandidaten.
- Das Ausmaß der zeitabhängigen Neuauswahl unterscheidet sich zwischen den
  Selection-Profilen.
- Der Befund beschreibt zeitabhängige Neuauswahl und ist nicht automatisch ein
  Fehler: Rolling-WF optimiert bewusst in jedem Trainingsfenster neu.
- Die Kandidatenakte trennt deshalb künftig Kandidatenwechsel von
  Performanceverschlechterung.

Profilstruktur:
- score_max wählt durchgehend risk_per_trade = 1,0 % und leverage = 1,0.
- risk_averse wählt durchgehend risk_per_trade = 0,25 % und leverage = 1,0.
- trade_rich wählt durchgehend risk_per_trade = 0,25 % und leverage = 1,0.
- boundary_averse wählt durchgehend leverage = 1,5 und risk_per_trade zwischen
  0,5 % und 0,75 %; die Strategieparameter konzentrieren sich zusätzlich auf
  einen engeren Bereich um längeres Momentum/Mean-Reversion.
- Die Selection-Profile erzeugen damit tatsächlich unterschiedliche
  Auswahlstrukturen. Die Ergebnisse zeigen jedoch keine durchgehende
  Übertragung dieser In-Sample-Unterschiede in stabile OOS-Ergebnisse.

Asset-/Universumsheterogenität:
- Die OOS-Befunde sind nicht identisch über alle Assets. Im
  liquid_high_volatility-Universum zeigen COIN und andere Assets
  unterschiedliche WFO-/Holdout-Muster; NVDA und TSLA weisen jeweils 0/4
  positive WFO-Ergebnisse über die vier Profile auf.
- Im benchmark-Universum zeigt IWM 0/4 positive WFO-Ergebnisse.
- Solche Unterschiede sind deskriptiv; sie werden nicht als Rangfolge von
  Assets oder Selection-Profilen interpretiert.

Zwischenfazit:
Die Daten stützen zwei getrennte Arbeitshypothesen für die nächste Prüfung:
1. Kandidaten können sich über Zeitfenster verändern.
2. Selbst bei positiver Gesamtleistung einzelner Rolling-Fenster bleibt die
   Profitabilität über die fünf Fenster hinweg nicht stabil genug für die
   bestehende Rolling-WF-Anforderung.

Diese Befunde sind noch keine Ursachenbeweise auf Strategieebene. Als Nächstes
wird geprüft, ob bestimmte Parameterstrukturen und Kandidatenwechsel
systematisch mit einzelnen Failure-Kriterien zusammenfallen. Die Gates,
Schwellenwerte und Selection-Profile bleiben dabei unverändert.

## Parameter-/Failure-Korrelation 2026-09-22

Die 52 Dataset/Profile-Auswertungen und 260 Rolling-WF-Fenster wurden
innerhalb der bestehenden Research-Gates nach Parameter-/Failure-Zusammenhängen
untersucht. Die Analyse ist explorativ; Korrelationen werden nicht als
kausale Effekte oder als Ranking von Parametern interpretiert.

Risikoparameter:
- Auf Rolling-WF-Fensterebene korreliert risk_per_trade stark mit
  Drawdown (Spearman rho ca. 0,63); leverage zeigt einen deutlich kleineren
  Zusammenhang mit Drawdown (rho ca. 0,18).
- Der Effekt ist mit der bestehenden Positionsgrößenlogik vereinbar und
  daher primär als Expositions-/Risikoeffekt zu lesen, nicht als Nachweis
  einer besseren oder schlechteren Signalqualität.
- Für Profit Factor zeigen risk_per_trade und leverage keinen vergleichbar
  stabilen Zusammenhang.

Strategieparameter:
- Innerhalb einzelner Selection-Profile existieren punktuelle Zusammenhänge,
  aber keine profilübergreifend stabile Richtung.
- Im risk_averse-Profil ist ein längerer Momentum-lookback innerhalb der
  13 Dataset-Auswertungen mit weniger WFO-Profit-Factor-Failures verbunden
  (Spearman rho ca. -0,57); derselbe Zusammenhang ist in den anderen
  Profilen nicht stabil reproduziert.
- Im boundary_averse-Profil ist höheres risk_per_trade mit mehr WFO-Drawdown-
  Failures verbunden (rho ca. 0,68). Das ist konsistent mit dem obigen
  Expositionsbefund.
- Ebenfalls im boundary_averse-Profil ist ein längeres
  Mean-Reversion-Fenster mit mehr Rolling-Workflow-Fehlschlägen beim
  Gesamtprofit verbunden (rho ca. 0,69); wegen n=13 und fehlender
  Replikation in anderen Profilen ist dies nur ein Prüfhinweis.
- Auf Rolling-WF-Fensterebene sinken mit größerem Momentum-lookback und
  höherem Mean-Reversion-Threshold die Trade-Zahlen deutlich; dies zeigt
  die erwartbare Abhängigkeit der Signalhäufigkeit von den Parametern,
  ist aber kein Profitabilitätsnachweis.

Overfit-spezifischer Befund:
- Nur 2/52 Auswertungen bestehen das Overfit-Gate.
- Beide Fälle stammen aus boundary_averse und verwenden
  risk_per_trade = 0,5 %, leverage = 1,5 und Momentum-lookback = 8.
- Die beiden Mean-Reversion-Konfigurationen unterscheiden sich beim
  Threshold (0,02 bzw. 0,03).
- Keiner dieser beiden Fälle liefert gleichzeitig einen durchgehend
  bestandenen OOS-/Rolling-/Holdout-Nachweis; ein Overfit-Pass allein ist
  daher keine ausreichende Evidenz.

Zwischenfazit:
Der zentrale Befund bleibt nicht ein einzelner „guter“ Parameterwert,
sondern die fehlende stabile Übertragung von In-Sample-Auswahl in mehrere
unabhängige OOS-Prüfungen. Die wenigen profilinternen Zusammenhänge sind
geeignete Kandidaten für gezielte Folgeprüfungen, aber noch keine Grundlage
für eine Änderung des Parameterraums oder der Research-Gates.

Nächste fachliche Stufe:
Prüfen, ob die beobachteten Failure-Muster an bestimmte zeitliche Marktphasen
oder Asset-Typen gekoppelt sind und ob dieselben Kandidatenstrukturen in
unterschiedlichen Universen wiederholt auftreten. Erst danach wird über eine
mögliche Änderung von Strategie- oder Parameterraum nachgedacht.

## Seit dem letzten Projektcheckpoint abgeschlossen

### Immutable Research Input

- PR #28 gemerged.
- Das Research-Datenmanifest besitzt einen eigenen deterministischen Fingerprint.
- Der Research-Run verweigert die Ausführung bei manipuliertem oder nicht zum lokalen Dataset passendem Datenmanifest.

### Research-Ergebnis als reproduzierbare Einheit

- PR #29 gemerged.
- Das Ergebnis-Manifest enthält die vollständige Run-Identität.
- Zusätzlich wird ein deterministischer `result_fingerprint` gespeichert.
- Laufzeit-Zeitstempel verändern den Ergebnis-Fingerprint nicht.

### Checkpoint-/Recovery-Integrität

- PR #30 gemerged.
- Checkpoints erhalten einen deterministischen `checkpoint_fingerprint`.
- Manipulierte Checkpoints werden erkannt.
- Legacy-Checkpoints ohne Integritätsprüfung werden beim Resume aus Sicherheitsgründen abgelehnt.
- Die bestehende `run_fingerprint`-Prüfung bleibt zusätzlich aktiv.
- CI auf PR #30: 218 Tests bestanden; normale Tests, ARM64 Research Smoke Test und Test-Workflow grün.

### Ergebnis-Integrität bei der Verwendung

- PR #32 gemerged.
- Research-Reports mit `result_fingerprint` können jetzt vor ihrer Auswertung verifiziert werden.
- Manipulierte oder fehlende Ergebnis-Fingerprints werden als ungültig abgelehnt.
- Der zentrale Research-Run-Workflow und der autonome Stock-Research-Workflow erzwingen die Prüfung vor der Status-/Gate-Auswertung.
- CI auf PR #32: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### Ergebnis-Integrität bei der Verwendung (aktualisiert)

- PR #32 gemerged.
- Research-Reports mit `result_fingerprint` werden vor zentraler Workflow-Auswertung verifiziert.
- Manipulierte oder fehlende Ergebnis-Fingerprints werden fail-closed abgelehnt.
- Zentraler Research-Run und Autonomous Stock Research erzwingen die Prüfung.

### Strikte Resume-Identität

- PR #34 gemerged.
- `resume=True` im zentralen Multi-Dataset-Runner erfordert zwingend eine verifizierte `run_fingerprint`.
- Checkpoints ohne gültige Run-Identität oder mit abweichender Run-Identität werden fail-closed abgelehnt.
- Regressionstests decken fehlende und abweichende Run-Fingerprints ab.
- CI auf PR #34: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### Legacy-Local-Research abgegrenzt

- PR #35 gemerged.
- Der ältere `research-local`-/`research_worker`-Pfad ist ausdrücklich als nicht-autoritative Diagnose gekennzeichnet.
- Auch dieser Output besitzt eine Run-Identität und einen verifizierbaren Ergebnis-Fingerprint.
- Der Legacy-Pfad darf dauerhaft keinen Writeback auf `research/autonomous-results` durchführen.
- CI auf PR #35: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### Research-Freshness-Grenzen

- PR #37 gemerged.
- Exakte Freshness-Grenzen sind regressionsgesichert: Intraday `3 × Intervall`, Daily `7 × 1d`.
- Geschlossene Candles bleiben zwingend; die Produktionsschwellen wurden nicht verändert.
- CI auf PR #37: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### End-to-End-Research-Recovery

- PR #38 gemerged.
- Multi-Dataset-Resume nach simuliertem Abbruch ist regressionsgesichert.
- Bereits abgeschlossene Datensätze werden beim Resume nicht erneut ausgeführt.
- CI auf PR #38: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### Experiment-State-Integrität

- PR #39 gemerged.
- Research-Experiment-Loop und Selection-Profile-Experiment besitzen vollständige State-Fingerprints.
- Manipulierte oder alte States ohne Integritätsprüfung werden beim Resume abgelehnt.
- CI auf PR #39: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### Statistik- und Evidenzhärtung

- PR #41 gemerged.
- Optimierungs-Suchraumgröße und archiviertes Top-N werden im Research-Ergebnis dokumentiert.
- Permutationsdiagnostik wird reproduzierbar mit Trials und Seed festgehalten.
- Die Diagnostik bleibt ausdrücklich unadjustiert und kein eigenständiges Gate.
- CI auf PR #41: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### Evidenzumfang und Vergleichsfamilien

- PR #42 gemerged.
- Research-Reports enthalten einen expliziten Evidenzumfang (`single_dataset`/`multi_dataset`).
- Ein einzelner Backtest wird ausdrücklich nicht als ausreichende Entscheidungsgrundlage markiert.
- Selection-Profile-Experimente dokumentieren mehrere Profile als gemeinsame explorative Vergleichsfamilie.
- CI auf PR #42: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### Holdout-Isolation

- PR #43 gemerged.
- Research- und Holdout-Teilmengen werden per Dataset-Fingerprint regressionsgesichert.
- Die zeitliche Trennung und vollständige Abdeckung des Gesamtdatensatzes werden getestet.
- CI auf PR #43: alle vier ausgelösten Prüfungen erfolgreich, einschließlich ARM64 Research Smoke Test.

### Kontrollierte Evidenzfamilien

- PR #45 gemerged.
- Mehrere bereits validierte Research-Reports können zu einer gemeinsamen Evidenzfamilie aggregiert werden.
- Jeder Quellreport wird vor Aggregation über seinen `result_fingerprint` verifiziert.
- Die Evidenzfamilie erhält einen eigenen deterministischen `evidence_fingerprint`.
- Permutationsdiagnostiken bleiben einzeln erhalten; es wird kein künstliches Gesamt-p oder Ranking erzeugt.
- PR #46 gemerged.
- Die Selection-Profile-Pipeline archiviert die Evidenzfamilie automatisch zusammen mit den bestehenden Experiment-Artefakten.
- PR #48 gemerged.
- Die Evidenzfamilie enthält zusätzlich eine reproduzierbare Gate-Failure-Matrix je Gesamtfamilie und je Selection-Profil.
- Der Experiment-State persistiert jetzt den tatsächlichen `run_manifest.json`-Pfad und kann damit die gemeinsame vorbereitete Datenbasis auch nach Resume eindeutig referenzieren.
- PR #51 gemerged.
- Jedes Gate trägt jetzt einen expliziten Evidenz-Scope; insbesondere ist `backtest` als `baseline_sanity` dokumentiert, während OOS-/Robustness-/Overfit-/Holdout-Gates den ausgewählten Kandidaten betreffen.

## Rolling-WF Zeitphasen- und Geometrie-Control 2026-09-22

PR #64 ist gemerged. Der kontrollierte Rolling-Control wurde auf derselben
4.500-Candle-Benchmark-Research-Basis durchgeführt. Strategie, Parameterraum,
Selection-Profile und Gate-Schwellen blieben unverändert; Holdout-Daten wurden
nicht verwendet.

Technischer Zustand:
- Workflow: `success`
- GitHub Actions Run: `35747170025`
- Artifact-ID: `10703836878`
- Code-Version: `62d91c0fa802e983e62879aa0bb7155202f8d7e0`
- Diagnostic-Fingerprint:
  `06ba10b5fb540de887fd2494f8cc328fa849b8f80ac0a867b16386a73525e0e2`
- Vollständige Testsuite: grün
- ARM64 Research Smoke Test: grün
- Paper-Only-Safety: grün
- Orders: deaktiviert

Geometrie-Control:
- Small: 1.125 Training / 225 Test / 225 Step / 15 Fenster -> Rolling-Gate 1/12
- Large: 2.250 Training / 450 Test / 450 Step / 5 Fenster -> Rolling-Gate 2/12
- Die Large-Testblöcke entsprechen exakt den Small-Paaren 6-7, 8-9, 10-11,
  12-13 und 14-15.
- Die zusätzliche Fensteranzahl löst den Rolling-WF-Engpass damit nicht.

Zeitphasen unter Small-Geometrie:
- frühe Fenster 1-5: 17/60 profitabel, Gesamtprofit ca. -309,00 EUR
- mittlere Fenster 6-10: 24/60 profitabel, Gesamtprofit ca. +38,22 EUR
- aktuelle Fenster 11-15: 26/60 profitabel, Gesamtprofit ca. -186,87 EUR
- In allen drei Phasen liegt der Median des Fensterprofits unter null.

Kandidatenpersistenz:
- Small-Geometrie: durchschnittlich ca. 48,2 % gleiche Kandidaten in benachbarten
  Fenstern; median 42,9 %; durchschnittlich 6,9 eindeutige Kandidaten je Asset/Profile
- Large-Geometrie: durchschnittlich ca. 33,3 % gleiche Kandidaten in benachbarten
  Fenstern; median 25,0 %; durchschnittlich 3,25 eindeutige Kandidaten je Asset/Profile
- Kandidaten werden im Rolling-WF bewusst neu ausgewählt; die niedrige Persistenz
  ist daher kein eigenständiger Fehler, aber sie ist relevant für die Stabilität
  der OOS-Übertragung.

Failure-Kriterien:
- Small: `profit_factor` 11/12, `profitable_window_ratio` 9/12,
  `nonpositive_total_profit` 9/12
- Large: `profit_factor` 10/12, `profitable_window_ratio` 8/12,
  `nonpositive_total_profit` 8/12

Asset/Profile-Ebene:
- Small-Gate bestanden: QQQ / `boundary_averse`
- Large-Gate bestanden: SPY / `boundary_averse` und QQQ / `risk_averse`
- Diese vereinzelten Passes werden nicht als Profilrangfolge interpretiert.

Fachliches Zwischenfazit:
Der verbleibende Rolling-WF-Engpass ist nicht durch eine bloße Verfeinerung der
Fensterzahl erklärbar. Die profitable Aktivität konzentriert sich zeitlich nicht
auf einen durchgehend positiven Abschnitt; insbesondere die mittlere Phase ist
als einzige aggregiert leicht positiv, während frühe und aktuelle Phasen negativ
sind. Gleichzeitig wechseln die ausgewählten Kandidaten häufig zwischen Fenstern.

Der nächste sinnvolle Kontrollschritt ist daher keine Parameteränderung, sondern
eine Kandidaten-Migrationsanalyse: Welche konkreten Parameterwechsel treten
zwischen aufeinanderfolgenden Rolling-Fenstern auf, und wie häufig fallen diese
mit `profit_factor`, `nonpositive_total_profit` oder `profitable_window_ratio`
Failures zusammen? Diese Analyse bleibt rein diagnostisch.

## Kandidaten-Migrationsanalyse 2026-09-22

PR #65 ist gemerged. Die Analyse verwendet ausschließlich den archivierten Rolling-Geometrie-Control-Report aus Run 35747170025 und führt keine neuen Backtests oder Optimierungen aus.

Technischer Zustand:
- Merge-Commit: `45ac4ca0cc075c81683264840235047f46edb9e9`
- Source-Code-Version: `62d91c0fa802e983e62879aa0bb7155202f8d7e0`
- Source-Diagnostic-Fingerprint: `06ba10b5fb540de887fd2494f8cc328fa849b8f80ac0a867b16386a73525e0e2`
- Analysis-Fingerprint: `171faa85316d7f9b5377263ea7058cdd30cc6c679626adf89d2e37b3978ad9`
- 216 Rolling-Transitionen: 119 Migrationen, 97 stabile Transitionen
- Migrationsrate: 55,1 %
- Paper-Only: True; Live-Trading: False; Orders: False
- alle fünf Checks auf dem PR-Commit grün

Gesamtvergleich:
- positive Destination-Rate: Migration 37,0 % vs. Stabilität 37,1 %
- PF >= 1,10: Migration 32,8 % vs. Stabilität 30,9 %
- DD <= 10 %: Migration 94,1 % vs. Stabilität 97,9 %
- Median-Destination-Profit: Migration -1,67 EUR vs. Stabilität -3,06 EUR

Damit gibt es über alle Transitionen keinen starken einheitlichen Unterschied zwischen Kandidatenwechsel und stabiler Kandidatenwahl. Die Unterschiede hängen von der Rolling-Geometrie ab; daher ist keine einfache allgemeine Regel „Migration schlechter/besser“ belegt.

Parameter-Assoziationen über alle 216 Transitionen:
- `risk_per_trade`: 22 Änderungen; positive Destination 54,5 % bei Änderung vs. 35,1 % ohne Änderung
- `momentum.lookback`: 76 Änderungen; 32,9 % vs. 39,3 %
- `mean_reversion.window`: 75 Änderungen; 32,0 % vs. 39,7 %
- `mean_reversion.threshold`: 62 Änderungen; 40,3 % vs. 35,7 %
- `leverage`: 0 Änderungen

Die kleinen bzw. unterschiedlich großen Teilstichproben und die explorative Fragestellung erlauben daraus keine Kausalitäts- oder Parameterentscheidung. Die Destination-Flags bleiben Fensterdiagnostik und sind nicht identisch mit den formalen Rolling-Gate-Kriterien.

Fachliches Fazit:
PR #65 bestätigt die Kandidatenmigration als reale Eigenschaft des Rolling-WF, erklärt den verbleibenden Rolling-WF-Engpass aber nicht durch einen einfachen Migration-vs.-Stabilität-Effekt. Die Gates, Schwellenwerte, Selection-Profile und der Parameterraum bleiben deshalb unverändert.

Als nächste diagnostische Stufe folgt die zeit- und assetbezogene Failure-Analyse: Welche konkreten Rolling-Failure-Kriterien häufen sich in bestimmten Marktphasen und Asset-Typen, und wie verhalten sie sich über unterschiedliche Kandidatenwechsel hinweg?

Vollständige Auswertung:
`docs/candidate_migration_analysis_2026-09-22.md`

## Zeit-/Asset-Failure-Analyse 2026-09-22

Die diagnostische Zeit-/Asset-Analyse ist abgeschlossen und auf dem workflow_run-Pfad erfolgreich automatisiert.

Technischer Zustand:
- PR #67 gemerged; aktueller master: b8ae1999fa842ce4b03a272f303298d5187b31d3
- Rolling-Control Source Run: 35747170025
- Candidate-Migration Source Run: 35749957065
- Candidate-Migration Artifact-ID: 10704770495
- Time/Asset Analysis Run: 35750002836
- Time/Asset Artifact-ID: 10704985412
- Time/Asset Analysis-Fingerprint: 274c5328ad89209121061890c670cafe131f7bf22715b50538c50e8afbb5038e
- 24 Evaluationen / 240 Rolling-Fenster
- 262 Tests im Diagnoseworkflow
- Paper-Only-Safety grün
- Cross-Workflow-Artefakte erfolgreich geladen und per Provenienz/Fingerprint verifiziert

Formale Rolling-Failures:
- profit_factor: 21/24
- nonpositive_total_profit: 17/24
- profitable_window_ratio: 17/24

Zeitbefund:
- large/early: 54,2 % positive Fenster, +170,28 EUR
- large/middle: 25,0 %, -101,77 EUR
- large/recent: 25,0 %, -328,88 EUR
- small/early: 28,3 %, -309,00 EUR
- small/middle: 40,0 %, +38,22 EUR
- small/recent: 43,3 %, -186,87 EUR

Asset-Befund:
- IWM: 8/8 nonpositive-profit Failures, 8/8 PF-Failures, 6/8 profitable-window-ratio Failures
- QQQ: 4/8, 6/8, 6/8
- SPY: 5/8, 7/8, 5/8

Die große Geometrie zeigt den deutlichsten zeitlichen Qualitätsabfall nach der frühen Phase. Die kleine Geometrie verbessert die positive Fensterquote im Verlauf, erreicht aber keine stabile positive Profitübertragung über die Phasen.

Kandidatenmigration bleibt auch unter Zeit-/Asset-Konditionierung geometrieabhängig. Es gibt keinen stabilen allgemeinen Effekt, nach dem Migrationen die Folgefenster systematisch verschlechtern oder verbessern.

Konsequenz:
- keine Änderung am Parameterraum
- keine Änderung an Selection-Profilen
- keine Änderung an Gate-Schwellen
- keine Änderung an Gebühren/Slippage
- keine neue Handelsausführung

Die nächste diagnostische Stufe ist die Prüfung konkreter Marktregime-/Volatilitätszustände und wiederkehrender Parameterkombinationen gegen dieselben Failure-Kriterien. Diese Prüfung bleibt zunächst ebenfalls rein diagnostisch.

Vollständige Auswertung:
docs/time_asset_failure_analysis_2026-09-22.md

## Synchronisationscheckpoint nach PR #81 — 2026-09-22

PR #81 ist gemerged.

- Merge-Commit: `9438d0528bfb5db187d6cb6ebe3795ee6c78bef0`
- Training-only Selection-Stability-Control: abgeschlossen und in `master`
- Selection-Profile-Consensus-Control: weiterhin rein diagnostisch
- Paper-Only: True
- Live-Trading: False
- Orders im Research: False
- Post-Merge `Trading Agent Tests`: Run 35762040743, success
- Post-Merge `Test`: Run 35762040734, success

### Stability-/Consensus-Befund

Der Training-only-Control umfasst 240 Evaluationen auf derselben unveränderten Rolling-Control-Basis.

- Kandidatenpersistenz insgesamt: 53,3 %
- stabile Fälle: 128
- instabile Fälle: 112
- OOS-positive Rate stabil: 36,7 %
- OOS-positive Rate instabil: 37,5 %
- Median OOS-Profit stabil: -3,04 EUR
- Median OOS-Profit instabil: -2,55 EUR

Damit erklärt Kandidatenstabilität allein den OOS-Engpass nicht.

Der Cross-Profile-Consensus-Control zeigt über 60 gemeinsame Marktfenster:

- 0/60 Fenster mit Konsens aller vier Profile
- 0/60 Fenster mit Konsens von mindestens drei Profilen
- 56/60 Fenster mit vier unterschiedlichen Kandidaten

Die Konsens-/Stabilitätsdiagnostik bleibt deshalb bewusst deskriptiv und wird nicht in eine neue Selection-Regel überführt.

### Bereits abgeschlossene Regime-/Failure-Diagnostik

Die nachgelagerten Regime-Layer waren bereits vor PR #81 auf demselben immutable Rolling-Control-Artifact abgeschlossen und werden nicht redundant neu berechnet:

- Regime-/Volatilitätsanalyse: Workflow Run 35753219417, Analyse-Fingerprint `95f7b843b3be5588a721d0f4e4877968526c489ea3e82d88801a66c931040836`
- kombinierte Regime-/Trend-/Choppiness-Analyse: Workflow Run 35753706618, Analyse-Fingerprint `33536438050b545f2c3e2a484f1941197f3205570f2cc3de9283e14bc81f94d0`
- Asset-x-Regime-Interaktion: Workflow Run 35754173209, Analyse-Fingerprint `fc069b7fff159dc9772162cbdf781d42bbcd41a52755d04ada1ffab2ce67581d`
- Kandidaten-Migrations-Nachwirkung: Workflow Run 35754677449, Analyse-Fingerprint `988cae167144d58f1e4baf69e7f311c2c441ef46154c3d5aa2c2acdd29ee5cff`

Gemeinsamer Befund dieser Layer:
- kein einzelnes Volatilitäts-, Trend-/Choppiness- oder Asset-Regime erklärt den Rolling-WF-Engpass geometrieunabhängig
- Kandidatenmigration ist real, erklärt den Engpass allein aber nicht
- die beobachteten Regimeeffekte sind asset- und geometrieabhängig
- die vorhandenen Parameterassoziationen sind explorativ und nicht kausal

Die unveränderte Forschungsbasis bleibt der Benchmark-Rolling-Control mit 5.000 Candles je Asset, 4.500 Research-Candles und 60 eindeutigen Rolling-Testfenstern.

## Streng geschichtete Hypothesenbildung und kontrolliertes Gegenexperiment 2026-09-22

Nach der Regime-Parameter-Failure-Matrix wurde die Evidenz streng auf
wiederkehrende Profil-/Asset-/Geometrie-Kontexte geschichtet. Dabei wurde genau
eine experimentbereite Hypothese identifiziert:

- Selection-Profil: `trade_rich`
- Geometrie: `small`
- Intervention: ausschließlich `mean_reversion.window` 10 gegen 5
- unverändert: `risk_per_trade=0.0025`, `leverage=1.0`,
  `momentum.lookback=3`, `mean_reversion.threshold=0.01`
- formaler Evidenzsatz: IWM und QQQ
- SPY wurde zusätzlich als nicht vorab bestimmtes Hold-out-Asset mitgerechnet,
  aber nicht für die formale Hypothesenentscheidung verwendet

### Reproduzierbarkeitskontrolle

- Historischer Rolling-Control: Run 35747170025
- Historischer Source-Commit: `62d91c0fa802e983e62879aa0bb7155202f8d7e0`
- Historischer Report-Fingerprint:
  `06ba10b5fb540de887fd2494f8cc328fa849b8f80ac0a867b16386a73525e0e2`
- Historischer Manifest-Fingerprint:
  `2f7124c41901a79f3b7dda684e991ba2008ff09ef0f2a36c96469f2615538836`
- Exakter Replay mit Rohdatenarchiv: Run 35766606233
- Replay-Artifact-ID: 10712781758
- Replay-Artifact-Digest:
  `sha256:128d99bd79978181e5660cda3bcd34a969e8bd8ac9ae7374b3eba369b25c7599`
- Dataset-Fingerprints:
  - IWM: `51a385563ebd0a3a659d844bcbeccab354f79fd52c1d521633865ff0de476821`
  - QQQ: `7923245473b99e9f9f32dafe58d48c3ba101454048eba04a9c14508aacc3b52f`
  - SPY: `8c62c32b84fa68b7633670302f90a7f935dc047a1a7ae33cc0e561e79f8266a3`

Der Replay reproduziert den historischen Rolling-Control auf dem historischen
Source-Commit exakt und archiviert die damals verwendeten Roh-Candles. Die
reguläre Rolling-Control-Pipeline auf aktuellem `master` archiviert Rohdaten
inzwischen ebenfalls; der historische Replay-Workflow bleibt deshalb ein
einmaliger Rekonstruktions-/Provenienzpfad und wurde nicht in `master` übernommen.

### Kontrolliertes Gegenexperiment

PR #87 ist gemerged:
- Merge-Commit: `3eac2f216b4a8ed71233344cc00b53f984283484`
- Workflow Run: 35768392064
- Artifact-ID: 10712493969
- Artifact-Digest:
  `sha256:6ac2a2d139d3ea3ae99695384d8d60451f306ed9225dfe289b6f7c5cfcd1592d`
- Analysis-Fingerprint:
  `b8b71d4ed86de96c60b8885862a38da61a88d105fd13d62efd6aff2c562b425a`
- Gegenexperiment: 25 formale gepaarte OOS-Fenster über IWM + QQQ
- unveränderte OOS-Fenster, identisches Kosten-/Backtest-Modell
- der Originalkandidat wurde vor jeder Gegenrechnung gegen die gespeicherten
  Rolling-Window-Metriken reproduziert
- vollständige Testsuite: 299 bestanden
- Paper-Only: True; Live-Trading: False; Orders: False

Formales Ergebnis über IWM + QQQ:
- Baseline-Gesamtprofit: `-112,03 EUR`
- Counterfactual-Gesamtprofit: `-118,86 EUR`
- gepaarte Differenz: `-6,82 EUR`
- positive Fensterquote: 28,0 % vs. 28,0 %
- PF-Passrate: 20,0 % vs. 28,0 %
- IWM: positive Fenster 38,5 % -> 23,1 %, PF-Pass 23,1 % -> 23,1 %
- QQQ: positive Fenster 16,7 % -> 33,3 %, PF-Pass 16,7 % -> 33,3 %

Formaler Status:
`hypothesis_not_supported_on_paired_control`

Die Hypothese ist damit nicht als tragfähiger Änderungsgrund bestätigt. Das
Muster ist zudem assetabhängig: QQQ verbessert die beiden primären
Diagnosemetriken, IWM verschlechtert die positive Fensterquote bei unverändertem
PF-Pass. Der negative Gesamtprofitunterschied spricht zusätzlich gegen eine
Umstellung auf `window=5` in diesem Kontrollsatz.

Zusätzlicher Hold-out-Befund für SPY:
- 12 gepaarte Fenster
- Profitdelta: `-1,22 EUR`
- positive Fensterquote: 33,3 % -> 41,7 %
- PF-Passrate: 33,3 % -> 41,7 %

Dieser SPY-Befund ist nur ergänzende Hold-out-Evidenz und keine nachträgliche
Neuformulierung der Hypothese.

### Konsequenz

- keine globale Parameteränderung
- keine Änderung des Parameterraums
- keine Änderung der Selection-Regeln
- keine Änderung der Research-Gates
- keine Änderung von Gebühren oder Slippage
- keine neue Handelsausführung

Der nächste fachliche Schritt ist deshalb **Evidenz-Ausweitung statt
Parameter-Tuning**: weitere vorab definierte, streng gepaarte Gegenexperimente
dürfen nur aus reproduzierbaren, wiederkehrenden Kontrasten entstehen. Es darf
nicht aus dem negativen Ergebnis nachträglich eine neue Auswahlrichtung
abgeleitet werden.

## Nächste Ziele

### 1. Wiederholbare Hypothesenbildung über mehrere Evidenzfamilien

Die erste formale Hypothese wurde sauber widerlegt. Der nächste Research-Layer
soll deshalb nicht den verworfenen Parameter weiter variieren, sondern prüfen,
ob überhaupt ein zweiter, unabhängig replizierbarer Ein-Parameter-Kontrast
über mehrere Assets und Zeitkontexte existiert.

Dabei bleiben Datenbasis, Gates, Selection-Profile und Parameterraum unverändert.

### 2. Controlled-Reexperiment als Standardpfad härten

Der gepaarte Gegenexperiment-Control bleibt diagnostisch und Paper-Only. Für
künftige Läufe sollen Source-Run, Rohdaten-Manifest, OOS-Fenster, Baseline-
Reproduktion und Intervention automatisch als unveränderliche Provenienz-Kette
gespeichert werden.

### 3. Dauerhafte Evidenzarchivierung

Die GitHub-Artefakte haben weiterhin eine begrenzte Aufbewahrungsfrist. Die
dauerhafte Research-Kette soll deshalb zusätzlich eine kompakte, im Repository
gespeicherte Provenienz-/Checkpoint-Datei mit Run-IDs, Commits, Fingerprints,
Safety-Status und Interpretation jedes zentralen Controls führen.

### 4. Keine Abkürzung über Parameter- oder Gateänderungen

Solange keine über mehrere unabhängige Kontexte replizierte Ursache/Hypothese
vorliegt, bleiben Strategie, Parameterraum, Selection und Gates unverändert.
Die Paper-Only-Sicherheitsbedingung bleibt aktiv.

### 5. Technische Restpunkte

Parallel bleiben die Architekturpunkte:
`Dataset → Manifest → Code-Version → Research-Konfiguration → deterministischer
Run → Gates → Ergebnis → Fingerprint → Archiv`

Insbesondere:
- Workflow-Level-Recoverytests vollständig schließen
- dauerhafte Archivierung jenseits der 30-Tage-GitHub-Artefakte härten
- Provenienz und Restore-Kette weiter gegen Unterbrechung und Zustandsabweichungen testen


# Aktueller Research-Checkpoint: Strategieneuausrichtung und Mechanismen 2026-09-22

## Ausgangslage

Die bisherige kurze Momentum-/Mean-Reversion-Sucharchitektur hat trotz umfangreicher
Research-Governance bislang keinen stabilen OOS-Edge geliefert. Die bisherigen
Cross-Universe-Auswertungen zeigten insbesondere ein wiederkehrendes
OOS-/IS- und Rolling-WF-Problem.

Der neue Forschungsweg untersucht deshalb bekannte Strategiefamilien und
trennt Signal, Ausführung, Risiko und Portfolioebene.

## PR #89–#101: wesentliche Ergebnisse

### Architektur-Control

Der aktuelle Momentum-/Mean-Reversion-Combiner war auf dem Kontrollsatz robuster
als jede Einzelkomponente, ist aber selbst noch kein positiver Edge-Nachweis.

- Combiner Rolling-OOS: -6,19 EUR
- Momentum-only: -43,55 EUR
- Mean-Reversion-only: -50,16 EUR
- Combiner Holdout: +31,29 EUR
- Paper-Only blieb aktiv

### Literatur-Strategie-Labor

Auf SPY/QQQ/IWM zeigten feste, nicht optimierte Trendfamilien deutlich bessere
zeitliche Stabilität als die bisherige kurze Mean-Reversion-Komponente.

Besonders relevant:
- TSM-Ensemble 63/126/252: 11/15 Rolling-Fenster positiv
- SMA 50/200 Long/Flat: 12/15 Rolling-Fenster positiv
- Mean Reversion 20/2: 6/15 Rolling-Fenster positiv

Die Laborstudie verwendet Point-in-Time-Ausführung
Close(t) -> Open(t+1) und separate ATR-basierte Exposition.

### Multi-Asset Trend

Der Cross-Asset-Control erweitert die Aktienbasis auf:
SPY, EFA, TLT, GLD, DBC, UUP, QQQ, IWM.

Der feste SMA-50/200-Trend blieb auf dieser breiteren Anlageklassenbasis robust:
- Holdout +46,34 %
- Holdout Drawdown 14,61 %
- Holdout PF 1,277
- 4/5 Rolling-Fenster positiv
- unter 2x Kosten: +44,31 %, PF 1,265, ebenfalls 4/5 Rolling-Fenster positiv

### Cross-Sectional Momentum

Ein zweiter, unabhängiger Mechanismus wurde als 12-1 Cross-Sectional Momentum
identifiziert und repliziert:

- Formation: 252 Handelstage
- letzter Monat übersprungen: 21 Handelstage
- monatliche Reallokation
- Top-2 Long-only

Unabhängige Replikation auf NVDA/AMD/TSLA/COIN/PLTR:
- Holdout +72,49 %
- Holdout Drawdown 28,22 %
- Holdout PF 1,268
- 3/5 Rolling-Fenster positiv
- 2x Kosten: +71,17 %, PF 1,264

Direkter Same-Universe-Control auf dem achtteiligen Cross-Asset-Universum:
- Holdout +69,61 %
- Drawdown 16,85 %
- PF 1,256
- 4/5 Rolling-Fenster positiv
- 2x Kosten: +65,60 %, PF 1,244
- Buy-and-Hold zum Vergleich: +46,83 %, Drawdown 11,56 %, PF 1,296

Damit ist Cross-Sectional Momentum als Mechanismus replizierbar, aber aufgrund
der höheren Drawdown-Seite noch kein alleiniger Produktionskandidat.

### Mechanismus-Konvergenz

Die bereits unabhängig replizierten Mechanismen wurden erstmals als feste
50/50-Sleeves kombiniert:

- Cross-Asset SMA 50/200 inverse volatility
- 12-1 Cross-Sectional Momentum Top-2 Long-only

Ohne Optimierung:
- Research-Korrelation 0,5035
- Holdout-Korrelation 0,6398
- 50/50 Holdout +52,61 %
- Holdout Drawdown 15,09 %
- Holdout PF 1,332
- 80 % der Rolling-Fenster positiv
- 2x Kosten: +51,70 %, Drawdown 15,12 %, PF 1,326

Der Effekt ist vor allem eine bessere Risikostruktur gegenüber dem
Cross-Sectional-Sleeve allein.

### Volatilitätsbudget

Anschließend wurde genau eine neue Risikohypothese getestet:
10 % annualisiertes Realized-Volatility-Ziel über 63 vorherige Handelstage,
nur De-Risking, nie Hebel.

Die Signale und Sleeve-Gewichte blieben unverändert.

Ergebnis:
- unskaliert: +52,61 % Holdout, Drawdown 15,09 %, PF 1,332
- 10%-Vol-Budget: +18,20 % Holdout, Drawdown 6,07 %, PF 1,321
- 2x Kosten: +17,73 % Holdout, Drawdown 6,11 %, PF 1,312
- mediane Holdout-Skalierung: 0,375
- minimale Skalierung: 0,316

Das 10%-Volatilitätsbudget reduziert den Drawdown deutlich und erhält den
Profit Factor nahe dem Ausgangsniveau. Es ist deshalb ein relevanter
Risikokontroll-Baustein, aber noch keine Produktionsfreigabe.

## Aktuelle Arbeitsannahme

Die Forschung verschiebt sich damit von:

kurzes Momentum + Mean Reversion + 1.280-Kandidaten-Optimierung

zu:

Trend / Cross-Sectional Momentum -> Point-in-Time-Ausführung -> separates Risiko-
budget -> Portfolioaggregation -> erst danach begrenzte Optimierung.

Die bestehenden Research-Gates bleiben unverändert.

Die positive Evidenz ist derzeit bewusst als Kandidaten-/Mechanismus-Evidenz
klassifiziert. Keiner der neuen Controls ersetzt die vollständige
Produktionsvalidierung.

## Nächster Zielschritt

Der nächste sinnvolle Schritt ist eine vollständige Kandidatenvalidierung des
festen 50/50 + 10%-Vol-Budget-Systems auf einer unabhängigen, ausreichend langen
Datenbasis mit:

- strikt getrenntem Research und Holdout
- mehreren festen Rolling-Fenstern
- realistischen Kostenannahmen
- Robustness-/Kostenstress
- OOS-/IS-Verhältnis
- Drawdown- und PF-Prüfung
- unabhängiger Holdout-Prüfung
- zusätzlicher Total-Return-Sensitivität für ETF-basierte Sleeves

Dabei wird weiterhin keine Parameteroptimierung als Abkürzung verwendet.

## Sicherheitszustand

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Research-Orders
- keine automatische Live-Ausführung
- keine Gate-Lockerung
- keine globale Produktionsstrategie geändert


## Aktueller Checkpoint nach Kandidatenvalidierung — 2026-09-22

PR #103 enthält die erste vollständige unabhängige Kandidatenvalidierung der
neuen festen 50/50 + 10%-Vol-Budget-Architektur.

### Validierungsbasis

- neue, vollständig disjunkte Asset-Universen:
  - Trend: DIA, EEM, LQD, IEF, VNQ, USO, FXE, TIP
  - Cross-Sectional: XLK, XLF, XLE, XLV, XLI
- 3.500 Daily-Candles je Asset
- 3.498 gemeinsame Return-Beobachtungen nach der zweistufigen
  Point-in-Time-Return-Konstruktion
- 2.798 Research-Returns + 700 vollständig blinde Holdout-Returns
- 5 feste Rolling-Fenster
- Base, 1,5x und 2x Kostenstress
- keine Optimierung, keine Selection-Profile, keine Signal- oder
  Sleeve-Änderung
- Total-Return-Sensitivität über Yahoo Adjusted Close
- Validierung asset-unabhängig, aber nicht out-of-time

### Technischer Zustand

- PR #103
- technischer Status des Validierungslaufs: COMPLETED
- Kandidatenstatus: BLOCKED
- GitHub Actions Run: 35784541912
- Artifact-ID: 10719572732
- Report-Fingerprint:
  9766e07ba1d63b1cc5ee901a1a7e3570187fcbbc463b7295fb1cb221dc66fbf9
- Trend-Manifest:
  c9a2a44f04703db86dc455113b3d128451683a930bdea8ec84b54a0b47a925a4
- Cross-Sectional-Manifest:
  61f560824ca09bf4f87330af2e07e0cec1464625ad075674159b6496ce8117d3
- vollständige Testsuite im erfolgreichen Validierungslauf: 362 bestanden
- Paper-Only-Safety: bestanden
- keine Research-Orders

### Fachlicher Befund

Base, 10%-Vol-Budget:
- Research Return: +42,30 %
- Research Drawdown: 16,81 %
- Research PF: 1,075
- Holdout Return: +29,78 %
- Holdout Drawdown: 12,01 %
- Holdout PF: 1,194
- OOS/IS-Ratio: 0,704
- profitable Research-Rolling-Fenster: 4/5

Bestanden wurden:
- positive Research-Gesamtrendite
- profitable-window-Quote
- OOS/IS-Ratio
- positiver Holdout
- Holdout-PF
- 1,5x-Kostenstress
- 2x-Kostenstress
- positive Total-Return-Sensitivität

Verfehlt wurden ausschließlich:
- Research-Drawdown <= 10 %
- Rolling-Research-PF >= 1,10
- durchschnittlicher Rolling-Drawdown <= 10 %
- Holdout-Drawdown <= 10 %

Kostenstress:
- 1,5x Holdout: +28,58 %, DD 12,10 %, PF 1,187
- 2x Holdout: +27,39 %, DD 12,18 %, PF 1,179

Total-Return-Sensitivität:
- Holdout-Renditedelta: +6,23 Prozentpunkte
- Holdout-Drawdowndelta: -0,15 Prozentpunkte
- Holdout-PFdelta: +0,0368

### Bedeutung für die Gesamtarchitektur

Die neue Architektur zeigt damit auch auf einem neuen Asset-Satz weiterhin einen
positiven Holdout-Befund. Gleichzeitig ist die Risikoseite noch nicht stabil
genug, um die unveränderten Produktions-/Research-Gates vollständig zu erfüllen.

Der 10%-Volatilitätsbudget-Layer verbessert gegenüber der unskalierten Referenz
die Drawdown-Seite deutlich, beseitigt den Engpass aber nicht:
- unskaliert Research DD 25,27 %, Holdout DD 15,80 %
- mit Vol-Budget Research DD 16,81 %, Holdout DD 12,01 %

Der Befund ist deshalb keine Produktionsfreigabe und kein Anlass zur
nachträglichen Anpassung der Gate-Schwellen oder zur datengetriebenen
Parameterwahl.

### Nächster Research-Schritt

Der nächste Schritt ist jetzt keine weitere Optimierung des Kandidaten, sondern
eine Failure-/Risk-Diagnose der unabhängigen Validierung:

1. Drawdown-Zerlegung über die 5 Rolling-Fenster und die beiden Mechanismus-Sleeves.
2. Prüfung, ob die DD-Failures aus gemeinsamen Marktphasen, einzelnen Assets,
   oder der festen 50/50-Aggregation stammen.
3. Gepaarter Kontrolllauf der bereits fixierten Architektur mit unverändertem
   Signal-/Sleeve-Design, sofern die Diagnose eine vorab definierte, nicht
   nachträglich optimierte Kontrollfrage ergibt.
4. Danach erst Entscheidung, ob ein weiterer unabhängiger Validierungssatz oder
   ein kontrolliertes Risiko-Reexperiment methodisch gerechtfertigt ist.

Bis dahin bleiben Strategie, Parameterraum, Selection und Gates unverändert.

## Sicherheitsstatus

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- keine Live-Ausführung
- keine Research-Orders
- keine Gate-Lockerung