# Trading Agent — Project Continuity

## Zweck

Dauerhafter Projekt-Handoff für die Fortsetzung über ChatGPT-Chats, Geräte und Sitzungen hinweg. Dieses Dokument hält Ziele, Sicherheitsregeln, Architektur, Research-Disziplin und den aktuellen Entwicklungsstand fest.

## Nicht verhandelbare Sicherheit

- Entwicklung und Research bleiben Paper-/Simulationsbetrieb.
- Keine Live-Orderausführung.
- `PAPER_ONLY` bleibt `True`.
- `LIVE_TRADING_ENABLED` bleibt `False`.
- Research-Automatisierung darf keine Handels-API-Credentials benötigen oder verwenden.
- Research-Ergebnisse dürfen nicht allein wegen positiver Backtests in den Produktions-/Masterpfad geschrieben werden.

## Quellen der Wahrheit

1. GitHub `DWR-debug/trading-agent`: technische Quelle der Wahrheit für Code, Tests, Workflows, Commits und reproduzierbare Research-Infrastruktur.
2. ChatGPT-Projekt: Zusammenarbeit, Entscheidungen, Ziele, Erklärungen und Research-Diskussionen.
3. Research-Reports, Manifests und Checkpoints: Evidenz für einzelne Research-Läufe.
4. Pixel 8a / S8: primär Kontrolle und Verifikation; Entwicklung möglichst über PC/GitHub.

## Zielarchitektur

`GitHub/PC -> Researchauftrag -> Daten aktualisieren -> Datenqualität -> Universe -> Backtest -> Optimierung -> Walk-Forward -> Rolling Walk-Forward -> Robustheit -> Holdout -> Quality Gates -> Ergebnisbericht -> Checkpoint/Resume`

Langfristige autonome Schleife:

`Hypothese -> Experiment -> Parameterraum -> Backtest -> Optimierung -> WF -> Rolling WF -> Robustheitsprüfung -> Holdout -> Gates -> PASSED/REJECT/BLOCKED -> nächste Hypothese`

Separate Markt-/Event-Schicht:

`Fed / Inflation / Zölle / Geopolitik / Energie / sonstige messbare Events -> Marktreaktion -> Volatilität/Volumen/Richtung -> Asset-/Sektorreaktion -> historische Wiederholbarkeit -> WF/Holdout`

Politische Ereignisse werden nur als messbare Markt-/Wirtschaftsfaktoren betrachtet. Das System enthält keine politischen Empfehlungen oder Präferenzen.

## Erreichte Basis

- Risk Engine und Paper Broker Sicherheitsmeilenstein.
- Portfolio Risk Controller im Trading Engine.
- Historische Datenloader und lokaler Market-Data-Store.
- Backtesting Engine, Metriken, Optimizer und Parameterraum.
- Walk-Forward und Rolling Walk-Forward.
- Reproduzierbares Research-Protokoll und deterministischer Permutations-Diagnosewert.
- Research-Datenqualitäts-Gates.
- Unveränderliche Run-Identität, Manifest und sicheres Resume.
- Checkpoint-basierter Multi-Dataset-Research-Runner.
- Aktien-Research mit priorisierten Universen.
- Adaptive gemeinsame Historienauswahl.
- Yahoo-Filter für offene Daily-Candles vor strenger OHLC-Validierung.
- Daily-Staleness-Behandlung für kalendersparse Marktdaten.
- GitHub/ARM64 CI und Paper-Only-Sicherheitsprüfungen.

## Aktienuniversen

1. `small_cap_high_volatility`: SOUN, RKLB, IONQ, ASTS, HIMS
2. `liquid_high_volatility`: NVDA, AMD, TSLA, COIN, PLTR
3. `penny_stock`: SNDL, BNGO, TLRY
4. `european_volatile`: RHM.DE, TUI1.DE, NEL.OL, VOW3.DE
5. `benchmark`: SPY, QQQ, IWM

Die Universen sind Research-Segmente, keine Prognosen.

## Research-Gates

Der kontrollierte Research-Pfad prüft sieben Gates:

- data_quality
- backtest
- walk_forward
- rolling_walk_forward
- robustness
- overfit
- holdout

Ein Kandidat gilt nur dann als bestanden, wenn alle erforderlichen Gates bestanden sind.

Wichtige aktuelle Schwellenwerte:

- mindestens 500 Candles
- mindestens 2 Baseline-Trades
- mindestens 10 WFO-Trades
- mindestens 30 Rolling-Trades
- mindestens 10 Holdout-Trades
- Profit Factor mindestens 1.10
- Maximal-Drawdown aus den zentralen Risk-Einstellungen
- mindestens 50 % profitable Rolling-Fenster
- höchstens 25 % Rolling-Fenster ohne Trades
- mindestens 4 Robustheitsvarianten
- mindestens 50 % profitable Robustheitsvarianten
- Stress-Test mit 1.50-fachen Kosten
- OOS/IS-Return-Verhältnis mindestens 25 %

Schwellenwerte werden nicht abgesenkt, nur um einen Lauf erfolgreich aussehen zu lassen.

## Aktueller Automatisierungsstand

PR #21 wurde in `master` gemergt:

`2fc48f1cfb54ad994b33609f8e8dc516724d010a`

PR #21 ergänzt den autonomen Aktien-Research-Workflow:

- täglicher Schedule
- manueller Start mit Universe-Auswahl
- Ausführung nach relevanten Research-Code-Änderungen
- adaptive gemeinsame Historie
- vollständige Tests vor Research
- zwingende Paper-Only-Prüfung
- harte Research-Gates
- Artefakt-Sicherung
- kein Research-Writeback
- keine Orderausführung

PR #22 ist die nächste aktive Entwicklungsebene:

**checkpointbasierter Research-Experiment-Loop**

Ziel:

- dauerhafter Loop-State
- atomische Checkpoints
- sicheres Resume
- Klassifizierung in `PASSED`, `REJECT`, `BLOCKED`

Dabei bleibt die bestehende gated Research-Pipeline die einzige Ausführungsbasis.

Nach PR #22 folgt der automatische Hypothesen-/Experiment-Layer.

## Research-Ergebnis vs. Workflow-Status

Ein Research-Lauf kann fachlich `BLOCKED` oder `REJECT` sein, obwohl die technische Pipeline fehlerfrei gearbeitet hat. Ein erwartetes Gate-Ergebnis ist daher kein Infrastrukturfehler. Technische Ausnahmen, ungültige Reports oder Verletzungen der Safety-/Reproduzierbarkeitsregeln bleiben echte Workflow-Fehler.

Rolling Walk-Forward verwendet ein datenrelatives Ausführungsprofil. Standardmäßig werden 50 % der Research-Historie zum Training, 10 % zum Testen und 10 % als Verschiebung verwendet. Diese Ausführungsparameter sind Bestandteil der unveränderlichen Run-Identität.

## Research-Disziplin

Ein einzelner profitabler Backtest reicht niemals für die Annahme einer robusten Strategie.

Die Evidenzkette lautet:

- saubere historische Daten
- deterministische Reproduzierbarkeit
- begrenzte Optimierung
- echte Out-of-Sample-Validierung
- wiederholte Rolling-Out-of-Sample-Validierung
- Robustheit gegen Parameteränderungen und höhere Kosten
- unangetasteter Holdout
- explizite Quality Gates
- gespeicherte Fingerprints, Manifests, Reports und Checkpoints

Echtgeldhandel gehört ausdrücklich nicht zur aktuellen Projektphase.

## Geräte-/Arbeitsmodell

Primäres Entwicklungsziel: PC + GitHub.

Pixel 8a: temporäre Verifikation/Kontrolle.

S8: später primäres mobiles Kontrollgerät.

Manuelle Termux-Arbeit wird auf das notwendige Minimum reduziert.

## Kontinuitätsregel

Bei der Fortsetzung des Projekts gilt:

Wenn der Nutzer `trading agent` schreibt, zuerst den aktuellen GitHub-/Projektzustand verifizieren und erst danach Änderungen oder Research-Läufe starten.

Keine Annahmen über:

- aktuelle Commits
- lokalen Checkout
- Reports
- API-Signaturen
- Pfade
- Feldnamen
- laufende Workflows

Bei unbekanntem Zustand zuerst den minimal nötigen Verifikationsschritt ausführen.

## Roadmap

### Phase 1 — Fundament
End-to-End-Gated-Research vollständig durchlaufen lassen und Sicherheits-/Reproduzierbarkeitsregeln erhalten.

### Phase 2 — PC/GitHub-Automatisierung
Research primär über GitHub/PC betreiben und Gerätearbeit minimieren.

### Phase 3 — Autonome Research-Schleife
Checkpoint-Orchestrierung, Experimentzustand, automatische Hypothesenwahl und resumierbare Ausführung fertigstellen.

### Phase 4 — Robustheit / Anti-Overfitting
Cross-Asset-, Zeitperioden-, Parameter-, Kosten- und Regime-Robustheit verstärken. Holdout unangetastet halten.

### Phase 5 — Markt-/Event-Layer
Messbare Makro- und Marktereignisse als separate Research-Schicht integrieren, insbesondere USA, ohne politische Präferenzbildung.

### Phase 6 — Paper-Trading
Nur Kandidaten, die die Research-Gates und Robustheitsanforderungen erfüllen, kontrolliert in eine längere Paper-Trading-Phase überführen.

### Phase 7 — Echtgeld
Erst nach belastbarer Evidenz und separater Entscheidung. Echtgeldkonto und ggf. Handels-API werden erst dann technisch relevant.
