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
