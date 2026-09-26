# Research Queue — 2026-09-24

## Aktuelle Reihenfolge

1. T040 Network Momentum Repair: **BLOCKED**. Coverage war valide, aber die festen Evidenz-Gates wurden klar verfehlt.
2. Adversarial Failure-Diagnose: **COMPLETED**. T040 wurde strukturell analysiert; zusätzlich wurden T022/T023/T025/T027/T028 als historische Vergleichsbasis ausgewertet.
3. **Portfolio Risk Control**: T041 ausgeführt und BLOCKED. Keine Gewichtungs-/Lookback-Nachsuche.
4. **Laufende Live-/Updated-Data Discovery** über `benchmark` plus `cross_asset_trend`; Discovery erzeugt nur Kandidaten und keine Performanceevidenz.
5. Champion / Challenger unter unverändertem Evidence-Vertrag.
6. Danach neue Volatility- und Relative-Value-Familien, falls die Evidenzlage dies trägt.

## Governance

Neue Performancehypothesen werden separat präregistriert und benötigen vor jeder Auswertung einen
Daten-/Coverage-Pass. Holdout-Ergebnisse dürfen niemals zur Asset-, Parameter- oder Hypothesenauswahl
verwendet werden.

Failure-Diagnose ist rein ableitend und darf keine Parameter, Assets oder Gates nachträglich verändern.

T028 ist ausschließlich ein Risk-Control-Hinweis. Ein möglicher neuer Portfolio-Risk-Trial muss
auf einem neuen, vollständig symbol-disjunkten Validierungsuniversum und mit vorab fixierter Regel laufen.

## Laufende Beobachtung

Der Unified Research Orchestrator beobachtet standardmäßig das Benchmark-Universum täglich.
Beobachtungen werden mit Zeitpunkt und Fingerprint als Artifact gesichert. Discovery kann Hypothesen
erzeugen; erst eine neue Präregistrierung darf formale Evidenz erzeugen.

## Sicherheit

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
orders_enabled=False  
automatic_promotion=False  
bezahlte Agenten-/API-Nutzung: 0 USD


## Queue-Fortsetzung — 2026-09-25

T042 ist formell abgeschlossen und als **NO_SUPPORT / archived_rejected** dokumentiert.
Die Volatilitäts-/Risk-Control-Linie wird nicht durch Lookback-, Threshold- oder
Gewichtssuche fortgesetzt.

### Neuer Schwerpunkt: T043 Trend-Signal-Variabilität

T043 prüft eine einzige, vorab fixierte Signal-Konsistenzhypothese:
Die bestehende 50/50-Architektur bleibt unverändert; nur das Trend-Signal wird
von der bisherigen 50/200-SMA-Regel auf eine **unanimous 63/126/252-TSM-
Konsistenzregel** umgestellt. Ein Asset ist im Trend-Sleeve nur dann long,
wenn alle drei bereits verfügbaren Point-in-Time-Tenor-Renditen positiv sind;
bei jeder Uneinigkeit bleibt es flat.

Keine Parameter-, Varianten-, Threshold- oder Holdout-Suche. Vor Performanceauswertung
steht ein Coverage-Preflight auf einem vollständig symbol-disjunkten Universum.

Ablauf:
Coverage-Preflight -> eingefrorener Coverage-Snapshot -> formale Research-Auswertung
-> blinder Holdout -> Kostenstress -> Evidence-Gate -> Archivierung.

Sicherheitszustand bleibt unverändert:
PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, orders_enabled=False, automatic_promotion=False.


## Queue-Fortsetzung — T044 abgeschlossen / T045 vorbereitet — 2026-09-25

T044 ist als **NO_SUPPORT / archived_rejected** abgeschlossen. Die getestete
63/126/252-TSM-Konsistenzfilterung wird nicht weiter verfeinert.

### Q-009 / T045 — Position-Lifecycle / Exit-Control

Die nächste orthogonale Forschungsfrage betrifft die bisher nicht separat
evaluierte Position-Lifecycle-Schicht. T045 testet genau einen festen
ATR-Trailing-Exit als Challenger gegen den unveränderten 50/50-Control:

**höchster Schlusskurs seit Einstieg − 3 × ATR(20)**.

Der Exit gilt nur für die Trend-Sleeve. Das bestehende SMA-50/200-Signal, die
Cross-Sectional-Sleeve, das 10%-Portfolio-Volatilitätsbudget, Kosten, PIT-Vertrag
und Gates bleiben unverändert.

Nach einem Stop bleibt das Asset bis zum nächsten monatlichen Baseline-Rebalance
flat. Bei weiterhin positiver Baseline-Allokation erfolgt die Re-Entry mit neuem
Trailing-High. Die übrigen Trendgewichte werden nicht renormalisiert.

T045 verwendet ein neues vollständig symbol-disjunktes Universum mit 13 Assets,
3.520 angeforderten Roh-Candles und einem Ziel von 3.500 gemeinsamen Candles.

Keine Parameter-/Varianten-/Schwellensuche und keine Holdout-Selektion.


## T045 Abschluss — 2026-09-25

Q-009-T045-POSITION-LIFECYCLE-EXIT-CONTROL ist formal abgeschlossen und **BLOCKED**. Die feste ATR-Lifecycle-Hypothese erhielt keine Promotions-/Nicht-Verschlechterungs-Evidenz. Vor einem neuen Trial wird die kumulierte Failure-Signatur über T041–T045 ausgewertet.


### Q-010 — Cross-Trial Failure-Diagnose

Q-010 ist nach Abschluss von T045 **PENDING**. Die Diagnose bleibt rein ableitend: T041–T045 werden gemeinsam auf wiederkehrende Failure-Modi ausgewertet, ohne Parameter-, Asset-, Holdout- oder Gate-Selektion. Erst danach wird eine neue Performancehypothese präregistriert.

## Q010 Abschluss — 2026-09-25

Q-010-CROSS-TRIAL-FAILURE-DIAGNOSIS ist **COMPLETED**. Die formale Diagnose wurde einmal autorisiert und ausgeführt.

- Workflow: `36119705793`
- Artifact-ID: `10856102739`
- Diagnose-Fingerprint: `c11a4a2340bf4f7a9f132f53835465d57d0b12ab97770a24f3fd98492e7f9549`
- 744 Tests bestanden
- 4/4 performance-valide Trials scheitern am Research-Risikogate
- 4/4 scheitern an der Control-Non-Deterioration
- 3/4 scheitern am OOS/IS-Stabilitätsgate
- 3/4 scheitern am Holdout-Drawdown-Gate
- T043 bleibt DATA_INVALID und trägt keine Performanceaussage

Die Diagnose ist rein ableitend. Fixed Candidate, Parameterraum, Gates und Holdout-Regeln wurden nicht verändert. Es gab keinen Re-Backtest und keine Promotion.

### Q-011 — Orthogonal Information/Alpha Discovery

Q-011 ist als **PENDING** vorgemerkt. Vor einem weiteren Performance-Trial wird eine neue, orthogonale Informations-/Alphaquelle untersucht. Die Discovery soll nur eine vorab fixierbare Hypothese liefern; Performanceevidenz entsteht erst nach neuer Präregistrierung, Coverage-Preflight und blindem, vollständig symbol-disjunktem Holdout.

Der nächste Schritt bleibt bewusst außerhalb der bereits mehrfach geprüften Portfolio-Risk-, Volatilitäts-, Trend-Konsistenz- und Lifecycle-Exit-Controls.

Sicherheitszustand bleibt unverändert: `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`, `automatic_promotion=False`.


## Queue-Fortsetzung — Q012/Q013 abgeschlossen, Q014 vorbereitet — 2026-09-25

### Q-012 — Information-Alpha Temporal Stability

Q012 wurde als **COMPLETED_DISCOVERY_ONLY** abgeschlossen. Die 180-Tage-Diagnostik über SPY/TLT/GLD ergab 123 gemeinsame Beobachtungen und 25 Event-Fenster. Next-Day-Vorzeichen waren in 12/18 festen Asset/Feature-Paaren zwischen den beiden Hälften konsistent; Five-Day in 9/18. Daraus folgt keine allgemeine stabile GDELT-Beziehung und keine Performancefreigabe.

### Q-013 — Information-Alpha Mechanism Redundancy

Q013 wurde als **COMPLETED_DISCOVERY_ONLY** abgeschlossen. Die vier festen Intensitäts-/Breitenfeatures event_count, attention_score, source_breadth und article_count zeigten im Event-Sample eine mittlere absolute Spearman-Korrelation von 0,9532. Mean Tone war gegenüber diesen Merkmalen deutlich weniger redundant. Die 25 Event-Fenster bleiben klein; die Return-Assoziationen sind kein Trading- oder Kausalnachweis.

### Q-014 — Long-Window Mechanism Redundancy

Q014 ist **PENDING** und präregistriert. Die sechs unveränderten Q011-Features und die festen Mechanismusgruppen werden über 365 Tage diagnostisch erneut ausgewertet, um die Event-Stichprobe zu vergrößern. Mindestvertrag: 80 gemeinsame Beobachtungen und 40 Event-Fenster; bei Nichterfüllung **DATA_INSUFFICIENT**.

Q014 bleibt vollständig diagnostisch. Keine Feature-, Asset-, Horizon-, Parameter- oder Holdout-Selektion und kein Performance-Trial. Jede spätere Trading-Hypothese benötigt eine neue Präregistrierung, frische symbol-disjunkte Coverage und unveränderte Evidence-Gates.

## Q014 Abschluss — 2026-09-25

Q-014-INFORMATION-ALPHA-MECHANISM-REDUNDANCY-LONG-WINDOW ist **COMPLETED / DISCOVERY_ONLY**.

Die 365-Tage-Diagnostik über SPY/TLT/GLD erzeugte 250 gemeinsame Beobachtungen und 55 Event-Fenster. Die vier festen Intensitäts-/Breitenfeatures blieben stark redundant (mean abs Spearman **0,94116** im Event-Sample), während Mean Tone deutlich orthogonaler zu dieser Volumen-/Breitenfamilie blieb. Die Return-Assoziationen sind heterogen und rein deskriptiv.

Technischer Nachweis: Workflow `36158184847`, Artifact `10874472512`, Report-Fingerprint `ab617984b57cf20ea2ac9e2458ac8a519b139abf8587dab751bd63e1d5d39d6d`. Die gesamte vierteilige, checkpointfähige Ausführung war erfolgreich.

Q014 ändert weder Strategieparameter noch Gates und autorisiert kein Performance-Trial.

### Nächster Queue-Eintrag — Q015

**Q-015-INFORMATION-ALPHA-MECHANISM-DISCRIMINATION-DIAGNOSTIC** — **PENDING**.

Ziel: inkrementelle Information der bereits fixierten sechs Q011-Features innerhalb der vorab definierten Mechanismusgruppen rein diagnostisch untersuchen. Keine Feature-, Asset-, Horizon-, Parameter- oder Holdout-Selektion; keine Performancefreigabe. Vor Ausführung ist eine eigene Präregistrierung erforderlich.

Sicherheitszustand bleibt unverändert: `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`, `automatic_promotion=False`.



## Q017 Abschluss / Q018 Start — 2026-09-26

Q017-ORTHOGONAL-HYPOTHESIS-DESIGN-ROUND ist als **COMPLETED / DESIGN_ONLY** abgeschlossen.
Der daraus abgeleitete Q017-G3-Source-Feasibility-Lauf blieb **DATA_INSUFFICIENT**;
keine Performanceauswertung und keine Auswahl-/Tuningaktion erfolgte.

### Q018 — Orthogonal Official Event-Source Design

Q018 ist als **PENDING / DESIGN_ONLY** vorgemerkt. Drei bewusst ungerankte,
point-in-time-fähige, kostenlose offizielle Informationsquellen werden zuerst nur
auf Source-Feasibility geprüft:

1. SEC Form 4 Insider-Flow Events.
2. Federal Reserve FOMC Policy-Decision Events.
3. U.S. Treasury 10-Year Auction-Demand Events.

Ablauf:
Source-Coverage -> PIT-Provenienz -> deterministisches Parsing -> nur bei bestandenem
Datenvertrag separate Performance-Präregistrierung.

Kein Holdout, keine Parameter-/Asset-/Feature-/Horizon-/Threshold-Suche und keine
Performancefreigabe durch die Designrunde.

Sicherheitszustand:
PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, orders_enabled=False, automatic_promotion=False.


## Q018 Abschluss / Q019 Start — 2026-09-26

Q018 Source-Feasibility ist **COMPLETED**. Das gemeinsame Gate ist `DATA_INSUFFICIENT`;
A und B scheiterten an reproduzierbarem HTTP-403-Zugriff aus GitHub Actions, C bestand die
vorab definierte Treasury-Source-Coverage.

Die Kandidaten wurden nicht gerankt. Der nächste objektive Gate-Schritt ist ausschließlich
die bereits source-feasible Q018-C-Familie:

### Q019 — Treasury Auction Signal Contract

**PREREGISTERED_COVERAGE_ONLY**

- feste Q018-Validierungsuniversum
- Treasury 10-Year Note
- Signal: Vorzeichen der Veränderung des Bid-to-Cover-Verhältnisses gegenüber der unmittelbar vorherigen Auktion
- PIT: `record_date`, Aktion erst am nächsten verfügbaren gemeinsamen Trading-Tag
- Prüfung: Vollständigkeit, Duplikate, numerische Werte, deterministisches Parsing, PIT-Mapping
- keine Rendite-/P&L-Berechnung
- kein Holdout
- keine Parameter-, Asset-, Feature-, Horizon-, Threshold- oder Varianten-Suche


## Q019 abgeschlossen / Q020 gestartet — 2026-09-26

Q019 Treasury Auction Signal/PIT Contract ist **COMPLETED / COVERAGE_VALIDATED**. Der verifizierte Lauf `36238205065` lieferte 89 gemappte Ereignisse und 0 terminale Ereignisse; keine Performanceauswertung und keine Holdout-Nutzung.

Q020 ist **PREREGISTERED_COVERAGE_ONLY** und prüft nun die kanonische OHLCV-Coverage des bereits fixierten Q018-Universums. Bei Nichterfüllung von 3500 gemeinsamen Candles gilt `DATA_INSUFFICIENT`; Assets oder Sample-Geometrie dürfen nicht nachträglich geändert werden.