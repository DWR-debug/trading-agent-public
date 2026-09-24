## Übergeordnetes Ziel: sehr kurze Zeit bis zu hohem Kapitalaufbau — 2026-09-24


Die operative Forschung verfolgt neben den technischen Qualitätszielen ein übergeordnetes,
vom Projektauftrag vorgegebenes Ziel: Wegen der beschriebenen finanziellen Ausgangslage
soll — soweit dies mit belastbarer Evidenz vereinbar ist — eine Strategie identifiziert
werden, die in möglichst kurzer Zeit einen hohen Kapitalaufbau ermöglicht.

Dabei gilt ausdrücklich:

- Die Dringlichkeit des Ziels darf nicht in eine Behauptung umgedeutet werden, dass sehr hohe
  Gewinne innerhalb kurzer Zeit zuverlässig erreichbar seien.
- Das Research darf deshalb hohe Renditepotenziale untersuchen, muss aber Renditepotenzial,
  Verlustwahrscheinlichkeit, Drawdown, Hebelwirkung, Kosten, Liquidität und Ruin-/Totalverlustrisiko
  getrennt ausweisen.
- Hypothesen, die nur wegen des Zielbilds attraktiv erscheinen, dürfen nicht als Evidenz
  behandelt werden. Keine Auswahl, Parameteränderung, Gateänderung oder Promotion erfolgt
  allein zur Steigerung einer gewünschten Renditekennzahl.
- Die besondere finanzielle Dringlichkeit ist ein Anforderungsparameter des Projekts, aber
  keine Ausnahme von Reproduzierbarkeit, Out-of-Sample-/Holdout-Prüfung, Kostenrealismus,
  Robustheit und Paper-Only-Safety.
- Insbesondere darf notwendiges Familiengeld nicht als risikoloses Experimentkapital
  behandelt werden.
- Ein späterer Echtgeldpfad bleibt ein separates, ausdrücklich freizugebendes Gateway und
  darf weder aus dem Zielbild noch aus positiven Backtest-/Research-Ergebnissen automatisch
  aktiviert werden.

### Priorisierte Forschungsfrage

Unter diesen Randbedingungen soll die Forschung systematisch prüfen, ob sich ein
wirtschaftlich tragfähiger, möglichst schneller Kapitalaufbau durch Kombination aus
robustem Edge, kontrolliertem Risiko, gegebenenfalls explizit untersuchtem Leverage,
Long-/Short-Mechanismen, geeigneten Märkten/Venues und realistischer Ausführbarkeit
nachweisen lässt.

Dabei ist zwischen drei Ebenen strikt zu unterscheiden:

1. **Nachweisbarer Edge:** reproduzierbare OOS-/Holdout-Evidenz unter realistischen Kosten.
2. **Kapitalwachstum:** Simulation der Kapitalentwicklung unter definiertem Risiko und
   gegebenenfalls Leverage; Szenarien sind keine Zusagen.
3. **Echtgeldfähigkeit:** erst nach separater Prüfung von Markt, Venue, Mindestorder,
   Gebühren, Slippage, Liquidität, technischem Orderpfad und ausdrücklicher Live-Freigabe.

Dieses übergeordnete Ziel ändert den Sicherheitsvertrag nicht:
`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, keine Live-Orders und keine
automatische Echtgeldpromotion.


## Zielbild: autonomes 30-Tage-Trading-Experiment mit optionalem Echtgeldpfad

Der langfristige Zielpfad ist ein möglichst autonomes 30-Tage-Trading-Experiment mit zunächst klar getrennter Forschung und einer **nur nach ausdrücklich bestätigter Freigabe** möglichen Echtgeldstufe.

### Ziel und Risikorealität

- Ziel eines möglichen Echtgeldversuchs: maximal möglicher Kontostand nach 30 Tagen.
- Es wird ausdrücklich nicht unterstellt, dass eine Strategie aus 10 EUR zuverlässig einen hohen Betrag erzeugen kann.
- Größere angestrebte Multiplikatoren gehen typischerweise mit höherem Verlustrisiko bis hin zum Totalverlust einher.
- Familienrelevantes oder notwendiges Geld soll nicht als risikoloses Kapital behandelt werden.

### Voraussetzungen für einen möglichen Echtgeldpfad

Ein späterer Echtgeldversuch setzt separat voraus:
1. ein ausdrücklich für Totalverlust freigegebenes Budget, z. B. 10 EUR;
2. eine ausdrückliche Echtgeld-/Live-Ausführungsfreigabe;
3. einen tatsächlich geeigneten Handelsplatz nach Prüfung von Gebühren, Mindestorders, Märkten und Bedingungen;
4. verlässlichen Datenzugriff;
5. eine technische Schnittstelle für Marktdaten und – nur nach Live-Freigabe – Orders;
6. explizite, messbare Regeln dafür, welche Risiken und Aktionen zulässig sind.

Die Formulierung „möglichst wenig operative Grenzen“ wird dabei als großer, aber kontrollierter Suchraum verstanden und nicht als Freigabe für blindes oder unbegrenztes Handeln.

### Angestrebter autonome Forschungs- und Entscheidungsweg

Daten → Marktuniversum → Gebühren → Liquidität → Volatilität → Strategien → Backtests → Walk-Forward → Robustheit → Positionsgrößen → tatsächliche Ausführbarkeit → laufende Neubewertung.

Der bestehende Trading Agent soll dabei als Infrastruktur dienen, insbesondere für Daten, Backtesting, Research-Governance, Risiko- und Portfolio-Controller, PaperBroker sowie spätere Ausführbarkeitsprüfungen.

Vor einem möglichen Echtgeldschritt müssen die bekannten Backtesting-Schwachstellen geschlossen und die Kandidaten gegen historische Daten reproduzierbar geprüft werden. Ein Echtgeldtest wird nur dann betrachtet, wenn technische Ausführbarkeit, Datenqualität, Kosten-/Slippage-Semantik, Robustheit und Sicherheitsverträge nachweisbar erfüllt sind.

### Aktueller Sicherheitsstatus

Dieses Zielbild **ändert den aktuellen Sicherheitsvertrag nicht**:
- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- keine Live-Orders
- keine automatische Echtgeldpromotion

Eine spätere Echtgeldstufe benötigt einen eigenen, ausdrücklich dokumentierten Freigabe- und Governance-Schritt.

## Verbindliche Arbeitsquelle / Default Repository

**Seit 2026-09-24 ist ausschließlich `DWR-debug/trading-agent-public` die Standard- und operative Arbeitsquelle für das Trading-Agent-Projekt.**

**Verbindliche Actions-Regel:** Sämtliche GitHub-Actions-Workflows für Research, Tests, CI, Validierung, Artefakt-Erzeugung und formale Experimente laufen ausschließlich aus `DWR-debug/trading-agent-public`. Das private Repository `DWR-debug/trading-agent` wird nicht als Actions-Ausführungsquelle verwendet.

Regeln:
- Neue Chats mit Bezug auf den Trading Agent starten die Statusprüfung ausschließlich gegen `DWR-debug/trading-agent-public`.
- Der aktuelle `master` dieses öffentlichen Repositories ist die primäre Quelle für Projektstatus, Research-Registry, Checkpoints, Workflows und formale Forschungsartefakte.
- Das Repository `DWR-debug/trading-agent` (privat) wird **nicht** als Standardquelle verwendet.
- Private `trading-agent`-Stände dürfen nur verwendet oder verglichen werden, wenn dies ausdrücklich angefordert wird.
- Formale Research-/Actions-Ausführung soll über `trading-agent-public` erfolgen.
- Paper-only bleibt verbindlich: `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, keine Live-Orders.

## Aktueller Checkpoint — Trial 025 Marktresidualvolatilität — 2026-09-24

Trial T-2026-09-24-025 wurde vollständig und reproduzierbar als einzelner,
vorab präregistrierter Control ausgeführt und anschließend archiviert.

### Technischer Nachweis

- PR #128: gemerged
- Merge-Commit: `16be871e5607df8555957e277d1275fe724dc494`
- Workflow-Run: `36022604471`
- Artifact-ID: `10818270142`
- Artifact-ZIP-SHA256: `183d51f7ae4cdfb817f1a6aa62c8960b6343da10a8db2e306c73f904bd4125d5`
- Report-Fingerprint: `9f2088cb95fb6f7d0d5e3a1b9e6b2857c03c5904871cad4cefaffef9533e860e`
- Manifest-Fingerprint: `bc146938fa2b112b23bc71503c1649fcf9d84f802b2ce27dc8c8e9a8441f5ed7`
- 8 vollständig symbol-disjunkte U.S.-Aktien: COST, TMO, LIN, DE, EMR, SBUX, VZ, MA
- 3.500 Candles je Asset
- 3.498 gemeinsame Point-in-Time-Returnperioden
- Research/Holdout: 2.798 / 700
- vollständige Testsuite, Safety, Disjointness, Präregistrierung, Kostenvertrag und Ergebnisintegrität: bestanden
- keine Parameter-, Threshold-, Auswahlbreiten- oder Asset-Suche
- keine Holdout-Selektion
- keine Orders

### Fachlicher Befund

**Entscheidung: NO_SUPPORT / archived_rejected**

Base:
- Research Return: +150,43 %
- Research Drawdown: 26,08 %
- Research PF: 1,118
- Research Rolling: 5/5 profitabel
- Holdout Return: +35,37 %
- Holdout Drawdown: 15,06 %
- Holdout PF: 1,156
- OOS/Research Return Ratio: 0,235
- 1,5x Kostenstress Holdout: +35,06 %
- 2,0x Kostenstress Holdout: +34,76 %
- Low-Residual-Vol minus High-Residual-Vol: -2,13 bps/Tag Research; -2,21 bps/Tag Holdout
- Gesamtturnover: 23,0

Damit bestehen Return-, PF-, Rolling- und Kostenstress-Prüfungen, während
Research-/Holdout-Drawdown, OOS/Research und der präregistrierte
Low-vs-High-Residual-Volatility-Edge verfehlt werden.

### Deskriptive Failure-Diagnose

Die fünf festen Research-Fenster zeigen:
- Fenster 1: +3,59 % Return / 8,55 % DD / PF 1,054
- Fenster 2: +3,19 % / 16,81 % / 1,030
- Fenster 3: +50,56 % / 19,05 % / 1,234
- Fenster 4: +54,76 % / 24,79 % / 1,220
- Fenster 5: +0,55 % / 26,08 % / 1,017

Der Research-Ertrag wird damit stark von den mittleren zwei Fenstern getragen;
das letzte Fenster endet nahezu flat bei zugleich höchstem Drawdown. Das ist
ein deskriptiver Hinweis auf zeitlich uneinheitliche Ergebnisqualität, keine
kausale Marktregime-Aussage.

Dauerhafte Evidenz:
- `docs/trial_025_idiosyncratic_volatility_result_2026_09_24.md`
- `docs/trial_025_idiosyncratic_volatility_failure_diagnosis_2026_09_24.md`
- `research/checkpoints/trial_025_idiosyncratic_volatility_2026_09_24_result.json`
- `research/evidence/trial_ledger.json`

### Konsequenz

Trial 025 wird nicht integriert. Es folgt keine nachträgliche Suche über
Lookback, Auswahlbreite, Residualisierungsmodell, Marktdefinition oder
verwandte Volatilitätsparameter.

Der nächste fachliche Schritt bleibt eine **separat vorregistrierte und
methodisch unabhängige Kontrollfrage**. Bis dahin bleiben Strategie,
Parameterraum, Gewichte, Gates und Produktionsstatus unverändert.


# Trading Agent — aktueller Gesamtcheckpoint

Stand: 2026-09-24
Basis: aktueller `master`-Stand nach PR #112 (Trial-021-Archivierung), PR #113 (Portfolio-/Execution-Foundation) und den zuvor integrierten Research-Governance-/Regime-Layern.

## Infrastruktur-Checkpoint — Paper-only 30-Tage-Experiment-Harness — 2026-09-24

Der technische Zielpfad für ein späteres autonomes 30-Tage-Experiment ist jetzt
um einen fail-closed Paper-Harness ergänzt.

### Implementiert

- PR #129 gemerged
- Merge-Commit: `00bf1c834b38e63ec0c6bd3993a2ef8d1344d3b7`
- exakt eine bereits Evidence-eligible Strategy-ID pro Experiment
- Evidence-Gate: nur `VALIDATED_PASS`
- Holdout-Selektion blockiert den Lauf
- exakt 30 Tagesreturns
- Returns müssen bereits netto des deklarierten Kostenvertrags sein
- atomarer Checkpoint nach jedem Tag
- Resume nur bei identischem Evidence-/Return-/Kapital-Fingerprint
- reproduzierbarer Abschlussbericht
- 10 EUR als Default-Simulationskapital
- vollständiger CI-Harness mit synthetischem Validierungsfall: grün

Dauerhafte Dateien:
- `automation/paper_30_day_experiment.py`
- `tests/test_paper_30_day_experiment.py`
- `docs/PAPER_30_DAY_EXPERIMENT.md`
- `.github/workflows/paper-30-day-experiment-harness.yml`

### Methodische Bedeutung

Der Harness führt keine Strategieauswahl durch und ersetzt weder
Marktdatenakquise noch einen Broker-/Execution-Layer. Er stellt die
Kapital-/Checkpoint-/Evidence-Stufe bereit, sobald eine Strategie vorher
unabhängig validiert wurde.

Der aktuelle Fixed Candidate ist weiterhin **BLOCKED**. Deshalb wird derzeit
kein 10-EUR-Echtgeld- oder Live-Experiment gestartet.

### Nächste technische Stufe

Vor einer späteren Echtgeldfreigabe sind noch mindestens:
- ein tatsächlich evidence-eligible Kandidat;
- verifizierte Markt-/Venue-Daten;
- Mindestorder-/Gebühren-/Slippage-/Liquiditätsprüfung;
- ein explizit freigegebener Live-Ausführungspfad;
- eine separat dokumentierte Echtgeldfreigabe

erforderlich.


## Gesamtstatus

### 1. Sicherheitszustand

- `PAPER_ONLY = True`
- `LIVE_TRADING_ENABLED = False`
- keine Live-Ausführung
- keine Research-Orders
- keine Gate-Lockerung
- maximale Research-Exposure bleibt 3x und entspricht der bestehenden Projektobergrenze

### 2. Hauptstrategie / Tagesebene

Der aktuelle Forschungsfokus ist die feste Architektur aus:

- Cross-Asset SMA 50/200 inverse-volatility Trend-Sleeve
- 12-1 Cross-Sectional-Momentum Top-2 Long-only
- feste 50/50-Aggregation
- 10% annualisiertes Realized-Volatility-Budget über 63 Sessions, nur De-Risking

Der Fixed Candidate wurde in vier vollständig symbol-disjunkten ETF-Familien geprüft. Alle vier Kandidatenberichte bleiben BLOCKED.

- Research-Drawdown-Gate: 4/4 FAIL
- Rolling-PF-Gate: 4/4 FAIL
- durchschnittliches Rolling-Drawdown-Gate: 4/4 FAIL
- Holdout-Drawdown-Gate: 3/4 FAIL
- Holdout-Rendite: 4/4 positiv
- 1,5x-/2x-Kostenstress: 4/4 nichtnegativ

### 2a. Vierfacher unabhängiger Validierungs-Konsens

Der robuste Risiko-/Rolling-Failure ist damit über vier vollständig symbol-disjunkte
Validierungsfamilien repliziert. Der Befund hängt nicht mehr an einer einzelnen
Asset-Familie oder einem einzelnen historischen Satz.

Dauerhafte Evidenzablage: docs/four_validation_consensus_2026_09_23.md und
research/checkpoints/four_validation_consensus_2026_09_23.json.

### 2b. Sleeve-Aggregations-Ablation

Trend-only, 50/50 und Cross-Sectional-only wurden auf denselben vier immutable
Validierungsartefakten ausschließlich im Research verglichen.

- Trend-only dominiert 50/50 auf DD + Rolling-PF: 1/4
- Cross-Sectional-only dominiert 50/50 auf DD + Rolling-PF: 2/4
- 50/50 gleichzeitig schlechter als beide Single-Sleeves: 0/4
- 3/4-Replikationsschwelle: nicht erreicht

Der Befund lautet no_universal_aggregation_contrast. Keine Gewichtsverschiebung.

Dauerhafte Evidenzablage: docs/sleeve_aggregation_ablation_2026_09_23_result.md
und research/checkpoints/sleeve_aggregation_ablation_2026_09_23.json.

### 2c. Risk-Layer-Drawdown-Speed

Über alle 20 festen Research-Rolling-Fenster der vier Validierungen war bei
Rapid-Drawdowns die Delayed-or-Never-Rate in 3/4 Datensätzen höher als bei Slow
Drawdowns; am Episodenbeginn war Rapid in 4/4 seltener bereits de-risked.

Das ergab den deskriptiven Mechanismus-Hinweis replicated_rapid_drawdown_onset_lag.

Dauerhafte Evidenzablage: docs/risk_layer_drawdown_speed_2026_09_23_result.md
und research/checkpoints/risk_layer_drawdown_speed_2026_09_23.json.

### 2d. Risk-Layer-Window 31 vs 63

Die daraus präregistrierte Einzelintervention wurde durchgeführt:

- Rapid-Delayed-Rate verbessert: 1/4
- Rapid-Onset-Active-Rate verbessert: 1/4
- Research-DD nicht schlechter: 3/4
- Research-Rolling-PF nicht schlechter: 4/4

Der Timing-Kontrast erreicht die geforderte 3/4-Schwelle nicht. Die Hypothese
eines universellen Fensterlängen-Mechanismus ist damit nicht unterstützt.
Die 63-Session-Referenz bleibt unverändert; es erfolgt keine weitere Suche
über Fensterlängen und keine fünfte Validierung dieser Variante.

Dauerhafte Evidenzablage: docs/risk_layer_window_31_vs_63_2026_09_23_result.md
und research/checkpoints/risk_layer_window_31_vs_63_2026_09_23.json.

### 2e. Parameter-Free Shock Guard

Die aus dem negativen 31-vs-63-Control abgeleitete parameterfreie Shock-Guard-Intervention
wurde auf vier unabhängigen Sätzen geprüft. Sie verwendet
`max(63er-Vol, abs(previous_unscaled_return) * sqrt(252))` bei unverändertem 10%-Ziel.

- Rapid-Delayed-Rate verbessert: 2/4
- Rapid-Onset-Active-Rate verbessert: 1/4
- Research-DD nicht schlechter: 0/4
- Research-Rolling-PF nicht schlechter: 0/4

Der präregistrierte Timing-/Robustheitsnachweis wird klar verfehlt. Keine Shock-Guard-
Variante und kein frei gewählter Shock-Faktor werden daraus weiterentwickelt.

Dauerhafte Evidenzablage: docs/risk_layer_parameter_free_shock_guard_2026_09_23_result.md
und research/checkpoints/risk_layer_parameter_free_shock_guard_2026_09_23.json.

### 2f. Vierfach-Regime-/Sleeve-Diagnose

Auf vier vollständig symbol-disjunkten Validierungsfamilien und 20 festen Research-
Fenstern wurden negative Portfoliofenster weiter zerlegt:

- 6/20 Portfoliofenster negativ
- 3/6 gemeinsame Trend+Cross-Sectional-Schwäche
- 1/6 reine Trend-Schwäche
- 2/6 reine Cross-Sectional-Schwäche
- mittlerer De-Risk-Anteil in negativen Fenstern: 81,08%
- mittlerer De-Risk-Anteil in positiven Fenstern: 49,05%

Der Befund ist deskriptiv. Er liefert keinen universellen Single-Sleeve-Verursacher
und beweist nicht, dass das De-Risking die Verluste verursacht; hohe Skalierung kann
selbst eine Reaktion auf bereits eingetretene Schwäche sein.

Dauerhafte Evidenzablage: docs/fourset_portfolio_regime_sleeve_interaction_2026_09_23_result.md
und research/checkpoints/fourset_portfolio_regime_sleeve_interaction_2026_09_23.json.

### 2g. Risk-Layer-EWMA(0,94)

Ein einzelner, extern fixierter RiskMetrics-style EWMA-Control wurde auf den
vier unabhängigen Research-Sätzen durchgeführt.

- Rapid-Delayed-Rate verbessert: 1/4
- Rapid-Onset-Active-Rate verbessert: 1/4
- Research-DD nicht schlechter: 2/4
- Research-Rolling-PF nicht schlechter: 0/4

Der präregistrierte Timing-Nachweis wird verfehlt. Die EWMA-Variante wird nicht
übernommen; es gibt keinen lambda-Suchlauf und keine fünfte Validierung.

Dauerhafte Evidenzablage: docs/risk_layer_ewma_094_2026_09_24_result.md
und research/checkpoints/risk_layer_ewma_094_2026_09_24.json.

### 2h. Risk-Layer Following-Return-Diagnose

Die bestehende 63-Session-/10%-Risk-Layer wurde auf vier unabhängigen Research-
Sätzen auf die unmittelbar folgende unskalierte Periode untersucht.

- günstige Volatility-Timing-Beziehung: 0/4
- ungünstige Beziehung: 4/4
- in allen vier Sätzen höhere mittlere Folgerendite nach De-Risking
- in allen vier Sätzen höhere positive Folgerenditenrate nach De-Risking

Der Befund ist deskriptiv und nicht kausal. Er zeigt jedoch, dass die empirische
Richtung des klassischen Volatility-Timing-Arguments auf der unmittelbaren
Tagesebene in unserem Fixed Candidate nicht repliziert wird.

Dauerhafte Evidenzablage: docs/risk_layer_following_return_diagnosis_2026_09_24_result.md
und research/checkpoints/risk_layer_following_return_diagnosis_2026_09_24.json.

### 2i. Risk-Layer Forward-Horizon-Profil

Der 4/4-Gegenbefund der Folgerendite wurde auf festen Research-Horizonten
erweitert. Günstig/ungünstig wird anhand von Mittelwert und positiver Renditerate
der unskalierten kumulierten Folgerendite klassifiziert.

- 1 Tag: ungünstig 4/4
- 5 Tage: ungünstig 4/4
- 20 Tage: ungünstig 3/4, gemischt 1/4
- 60 Tage: ungünstig 4/4

Die Beziehung ist damit nicht auf die nächste Tagesperiode begrenzt. Die
Hypothese eines rein kurzfristigen Mean-Reversion-Gegenbefunds wird nicht
bestätigt. Der Befund bleibt deskriptiv und nicht kausal.

Dauerhafte Evidenzablage: docs/risk_layer_forward_horizon_profile_2026_09_24_result.md
und research/checkpoints/risk_layer_forward_horizon_profile_2026_09_24.json.

### 2j. Downside-Volatility-Control

Der extern motivierte 63-Session-Downside-Volatility-Control wurde auf vier
unabhängigen Research-Sätzen geprüft.

- Rapid-Delayed-Rate verbessert: 0/4
- Rapid-Onset-Active-Rate verbessert: 0/4
- Research-DD nicht schlechter: 0/4
- Research-Rolling-PF nicht schlechter: 4/4

Die Variante erhöht zwar den Rolling-PF konsistent leicht, verschlechtert aber
Research-Drawdown in 4/4 und verbessert keine der präregistrierten Timing-Metriken.
Sie wird deshalb nicht übernommen.

Dauerhafte Evidenzablage: docs/risk_layer_downside_volatility_2026_09_24_result.md
und research/checkpoints/risk_layer_downside_volatility_2026_09_24.json.

### 2k. Aktueller Forschungsfokus

Die Risk-Layer-Volatilitätsfamilie ist damit weitgehend abgegrenzt:

- 31 statt 63 Sessions: nicht unterstützt
- EWMA(0,94): nicht unterstützt
- parameterfreier Ein-Tages-Shock-Guard: nicht unterstützt
- Downside-Volatility: nicht unterstützt

Die bestehende 63-Session-/10%-Risk-Layer bleibt unverändert.

Die timestamp-basierte Daten-/Kalenderausrichtung aus Issue #55 ist bereits
implementiert und durch Regressionstests abgesichert. Gemeinsame Research-Daten
werden deterministisch über die Timestamp-Schnittmenge ausgerichtet; bei zu
kurzer Schnittmenge wird fail-closed abgebrochen.

Damit ist die Daten-/Kalenderseite kein offener Blocker mehr. Der nächste
fachliche Schwerpunkt liegt bei gezielter Diagnose bzw. neuen Gegenexperimenten
zur eigentlichen Signal-/Portfolio-Drawdown-Entstehung auf sauber ausgerichteten
Daten.

Produktionsstatus bleibt BLOCKED; keine Parameter-, Gewichts- oder Gateänderung
wird aus den bisherigen Risk-Layer-Controls abgeleitet.

### 2l. Siebte Multi-Strategie-Komplementaritätsvalidierung — 2026-09-24

Der präregistrierte siebte Control wurde auf einem neuen vollständig symbol-disjunkten
Datensatz erfolgreich technisch und methodisch ausgeführt.

- Workflow-Run: 36001213390
- Artifact-ID: 10808382149
- Report-Fingerprint: 730fa24672298e943d8b146184aa6919281b1345a6dbd04461bd476efa4a0654
- 3.500 gemeinsame Tages-Candles
- 3.498 gemeinsame Point-in-Time-Return-Perioden
- Research/Holdout: 2.798 / 700
- vollständige Testsuite, Safety, Präregistrierung und Ergebnisintegrität: grün

Basis-Szenario:

- Trend-only: Research +7,03%, DD 25,71%, PF 1,0221; Holdout +25,61%, DD 13,13%, PF 1,1649
- Cross-sectional-only: Research +171,17%, DD 14,26%, PF 1,1833; Holdout +27,99%, DD 12,85%, PF 1,1704
- 50/50-Blend: Research +109,70%, DD 15,61%, PF 1,1352; Holdout +30,68%, DD 13,69%, PF 1,1811

Die vorab definierten Komplementaritätsvergleiche zeigen keinen universellen
Komplementaritätsnachweis auf diesem siebten Satz:

- Research-DD des Blends nicht schlechter als beide Einzelvarianten: nein
- Research-Rolling-PF des Blends nicht schlechter als beide Einzelvarianten: nein
- Holdout-DD des Blends nicht schlechter als beide Einzelvarianten: nein
- Holdout-PF des Blends nicht schlechter als beide Einzelvarianten: ja
- Blend-Rendite positiv in Research und Holdout: ja

Entscheidung: NO_UNIVERSAL_COMPLEMENTARITY_EVIDENCE. Keine Gewichtsanpassung,
keine weitere Gewichtssuche auf diesem Datensatz und keine Produktionsintegration.

Dauerhafte Evidenzablage:
docs/multi_strategy_complementarity_validation_2026_09_24_result.md
und
research/checkpoints/seventh_multi_strategy_complementarity_2026_09_24.json.

### 2m. Research-/Evidence-Governance

Der Research-Prozess besitzt jetzt einen fail-closed Evidence-Contract.

Jede promotionsrelevante Evidenz kann an Trial-ID, Artifact-Digest, Report-/Manifest-
Fingerprint, Code-Commit, Research-/Holdout-Scope, benannte Gates und den Safety-
Vertrag gebunden werden. Holdout-Nutzung zur Selektion blockiert die Evidence.
Fehlende Gates, ungültige Provenienz und nicht bestandene Gates führen nicht zu
einer automatischen Freigabe.

Dauerhafte Ablage:
research/evidence_contract.py
und
docs/EVIDENCE_GOVERNANCE.md.

Der Contract ersetzt oder lockert keine bestehenden Research-/Holdout-/Rolling-
oder Kostenstress-Gates.

### 2n. Regime-/Meta-Layer

Ein erster reiner Beobachtungs-Layer ist in master integriert.

Er berechnet ausschließlich aus bereits beobachteten Returns:

- annualisierte realisierte Volatilität
- positive Asset-Breite
- Downside-Breite
- Cross-Sectional-Dispersion
- mittlere paarweise Korrelation

Es gibt noch keine unvalidierte automatische Regimeklassifikation. Der sichere
Unknown-State-Pfad bleibt damit erhalten; ein unvalidierter Marktstatus führt
weiterhin zu HOLD_CASH.

### 2o. Political/Event-Alpha

Trial-017/017b ist als gehärtete, PIT-fähige Event-Intelligence-Pipeline in master
integriert.

Der erste neue Event-Alpha-Control (EVENT-ALPHA-2026-09-24-001) wurde technisch
geschlossen und archiviert. Zwei Ausführungen bestanden Tests, Paper-only-Sicherheit,
Universums-Disjointness und Präregistrationsprüfung, konnten den Research-/Holdout-
Report jedoch wegen fehlender historischer GDELT-Tagesdateien im festgelegten
2025-04-01 bis 2025-09-30 Fenster nicht vollständig erzeugen.

- Lauf 36001720932: HTTP 404 beim benötigten historischen GDELT-Tagesexport
- Lauf 36003014680: HTTP 404 sowohl Primärquelle als auch getesteter AWS-Fallback
- Letzter vollständig akquirierter Eventtag: 2025-06-13
- kein Alpha-Ergebnis, keine Holdout-Auswahl, keine Parameteränderung
- keine Produktionsintegration

Die technische Abschlussdokumentation liegt in
docs/event_alpha_validation_2026_09_24_technical_closure.md sowie im
Checkpoint research/checkpoints/event_alpha_2026_09_24_technical_failure.json.

Eine erneute Event-Alpha-Validierung erfordert zuerst einen vollständig verifizierten
historischen Event-Datenbezug und wäre als neuer Control separat zu präregistrieren.

### 2p. Turn-of-Month Calendar Alpha — 2026-09-24

Die präregistrierte Turn-of-Month-Kalenderhypothese wurde auf einem vollständig
symbol-disjunkten globalen Country-ETF-Universum technisch vollständig und
methodisch reproduzierbar ausgeführt.

- Workflow-Run: 36006749490
- Artifact-ID: 10810214406
- Artifact-Digest: sha256:c00a489e5604a83e5f1d66123ff612d0f0fba92170f355870721f507c9cfad43
- Code-Commit: 546fd8aad0008923bb63f70936b57882f579ef9f
- Report-Fingerprint: 27df7c6ba36083d599d39c65fdd5fd089ec9216bd03211a42b8530c75ee3e85a
- Market-Manifest-Fingerprint: 181895cab3682cf89694d085f71802b802b183e7ffa02c9cfa64d04ffe07cdc4
- 8 Assets, 3.500 Candles je Asset, 3.498 Returns
- Research/Holdout: 2.798 / 700
- vollständige Testsuite: 615 bestanden
- Paper-only, Universums-Disjointness, Präregistrierung und Ergebnisintegrität: bestanden
- keine Auswahl, keine Parameter-/Threshold-Suche, keine Orders

Die Implementierung wurde vor der eigentlichen Forschungsrechnung auf die bereits
präregistrierte Regel ausgerichtet: letzter Handelstag des Monats plus erste drei
Handelstage des Folgemonats. Die Präregistrierung selbst wurde nicht nachträglich
geändert.

### Fachlicher Befund

Basis-Szenario:

- Research: -11,67% Return, 24,40% Drawdown, PF 0,963
- Holdout: -1,92% Return, 9,29% Drawdown, PF 0,977
- Research-Rolling: 3/5 Fenster positiv
- OOS/Research-Ratio: 0,00
- TOM-Mittelrendite minus Nicht-TOM im Research: +0,0789 Prozentpunkte pro Tag
- TOM-Mittelrendite minus Nicht-TOM im Holdout: +0,0187 Prozentpunkte pro Tag
- Turnover: 267 Research / 68 Holdout

Kostenstress verschlechtert den Befund weiter:

- 1,5x Kosten: Holdout -6,81%, PF 0,891
- 2x Kosten: Holdout -11,45%, PF 0,817

Von den elf festen Entscheidungschecks bestehen nur vier:
die TOM-gegen-Nicht-TOM-Mittelrendite in Research und Holdout, die
Research-Rolling-Quote von 3/5 und das Holdout-Drawdown-Gate.

Verfehlt werden insbesondere Research-Return/Drawdown/PF, OOS/Research,
Holdout-Return/PF sowie beide Kostenstress-Checks.

### Entscheidung

NO_SUPPORT / archived_rejected.

Der Control liefert damit trotz positiver deskriptiver TOM-Mittelrendite keinen
robusten kostenbereinigten Portfolio-Nachweis. Es gibt keine Produktionsintegration,
keine Gewichtsanpassung, keine TOM-Varianten-Suche und keine nachträgliche
Gateänderung.

Dauerhafte Evidenzablage:

- docs/turn_of_month_validation_2026_09_24_result.md
- research/checkpoints/turn_of_month_2026_09_24_result.json
- research/evidence/trial_ledger.json

Der nächste Research-Schritt bleibt außerhalb dieser Kalenderregel; es erfolgt
kein weiteres TOM-Tuning auf Basis dieses Resultats.

### 2q. Open/Close Gap-Reversal — Trial 018 technischer Abschluss — 2026-09-24

Trial T-2026-09-24-018 wurde technisch geprüft, aber wegen unzureichender gemeinsamer historischer Datenbasis vor der eigentlichen Forschungsrechnung beendet.

- Workflow-Run: 36007923924
- Code-Commit: d781ec519e64076c6c0ee9c6cf2508a6035adbb4
- vollständig disjunktes Universum: SPYM, IJR, IEFA, IEMG, IVE, IVW, VOE, VOT
- Vorgabe: 3.500 gemeinsame Tages-Candles
- tatsächlich nach fünf Akquisitions-/Alignment-Versuchen: 3.496 gemeinsame Candles
- vollständige Testsuite und Paper-only-Sicherheitsprüfung: bestanden
- Universums-Disjointness: bestanden
- Research-/Holdout-Auswertung: nicht gestartet
- Ergebnisartifact: nicht vorhanden
- keine Auswahl, keine Parameter-/Threshold-Suche, keine Orders

Methodische Konsequenz: Dies ist weder ein positives noch ein negatives Alpha-Ergebnis. Die ursprüngliche Präregistrierung wird nicht nachträglich geändert. Eine neue Datenbasis erhält deshalb eine neue Trial-ID.

### 2r. Open/Close Gap-Reversal — Trial 019 technischer Abschluss — 2026-09-24

Trial T-2026-09-24-019 wurde vor der eigentlichen Forschungsrechnung beendet. Nach fünf Akquisitions-/Alignment-Versuchen standen nur 3.322 gemeinsame Tages-Candles zur Verfügung, obwohl der unveränderte Control-Vertrag 3.500 verlangt.

- Workflow-Run: 36008838474
- Code-Commit: 0207942727f204382c89b09a575a0fcd456685fb
- vollständige Testsuite, Paper-only-Sicherheit und Universums-Disjointness: bestanden
- Research-/Holdout-Auswertung: nicht gestartet
- kein Ergebnisartifact, keine Auswahl, keine Parameter-/Threshold-Suche, keine Orders

Methodische Konsequenz: Kein Alpha-Befund. Die Präregistrierung wird nicht nachträglich umgebaut. Der nächste Versuch erhält daher eine neue Trial-ID und ein datenverifizierteres Universum.

### 2s. Open/Close Gap-Reversal — Trial 020 technischer Abschluss — 2026-09-24

Trial T-2026-09-24-020 wurde vor der eigentlichen Forschungsrechnung beendet. Nach fünf Akquisitions-/Alignment-Versuchen standen nur 3.322 gemeinsame Tages-Candles zur Verfügung, obwohl der unveränderte Control-Vertrag 3.500 verlangt.

- Workflow-Run: 36009263715
- Code-Commit: e4d960ecc8f06aaceaa1ddc1997fda6c2c9ebcd5
- vollständig disjunktes Universum: SPYG, SPYV, SPTM, SPMD, SDY, RWR, XNTK, XPH
- vollständige Testsuite und Paper-only-Sicherheit: bestanden
- Universums-Disjointness: bestanden
- Research-/Holdout-Auswertung: nicht gestartet
- kein Ergebnisartifact, keine Auswahl, keine Parameter-/Threshold-Suche, keine Orders

Methodische Konsequenz: Dies ist weder ein positives noch ein negatives Alpha-Ergebnis. Die Präregistrierung wird nicht nachträglich verändert. Der nächste Versuch erhält eine neue Trial-ID und eine anders strukturierte, vorab verifizierte Datenbasis.

### 2t. Open/Close Gap-Reversal — Trial 021 Ergebnis — 2026-09-24

Trial T-2026-09-24-021 wurde auf einem vollständig symbol-disjunkten U.S.-Aktienuniversum vollständig und reproduzierbar ausgeführt. Die Daten-, Safety-, Präregistrations- und Integritätsprüfungen bestanden; der eigentliche Research-/Holdout-Control wurde vollständig gerechnet.

- Workflow-Run: 36010070504
- Artifact-ID: 10812385942
- Artifact-Digest: sha256:c00a489e5604a83e5f1d66123ff612d0f0fba92170f355870721f507c9cfad43
- 8 Assets: JNJ, KO, PG, WMT, XOM, CVX, MCD, PEP
- 3.500 Candles/Asset, 3.498 Returns, Research/Holdout 2.798/700
- vollständige Testsuite: 617 bestanden
- Paper-only, Universums-Disjointness, Präregistrierung und Ergebnisintegrität: bestanden
- Report-Fingerprint: 8af136b92c4c114d16fe6951d609f20939c15c840d9952c878e5de15d9cdb2da
- Manifest-Fingerprint: 181895cab3682cf89694d085f71802b802b183e7ffa02c9cfa64d04ffe07cdc4
- Code-Commit: 24a47f77306d76b930b81a73e96ed5748d1bf88d

### Fachlicher Befund

Basis-Szenario:

- Research: -99,97% Return, 99,97% Drawdown, PF 0,217
- Research-Rolling: 0/5 profitable Fenster
- Holdout: -88,12% Return, 88,16% Drawdown, PF 0,210
- OOS/Research-Ratio: 0,00
- Gap-Reversal-Edge: Research negativ, Holdout gering positiv
- Turnover: 5.595 Research / 1.399,75 Holdout

Kostenstress verschlechtert den Befund weiter:

- 1,5x Kostenstress: Holdout -95,86%, PF 0,102
- 2x Kostenstress: Holdout -98,56%, PF 0,054

Alle elf präregistrierten Entscheidungschecks werden verfehlt. Insbesondere gibt es keinen positiven Research-/Holdout-Portfolioertrag, keine ausreichende Drawdown-/PF-Stabilität, keine profitable Rolling-Historie, kein OOS/IS-Signal und keine Kostenrobustheit.

### Entscheidung

NO_SUPPORT / archived_rejected.

Der Control wird nicht in die Produktion integriert. Es erfolgt keine Varianten-, Schwellenwert-, Asset- oder Kostenoptimierung innerhalb dieser Research-Familie. Die Gap-Reversal-Familie gilt damit als methodisch geprüft und für weitere direkte Tuning-Versuche geschlossen.

Dauerhafte Evidenzablage:
- docs/open_close_gap_reversal_trial021_result.md
- research/checkpoints/open_close_gap_reversal_trial021_result.json
- research/evidence/trial_ledger.json

Der nächste Forschungsschritt muss eine orthogonale Alpha-Familie prüfen.

### 2u. Portfolio-/Execution-Foundation — 2026-09-24

Nach Abschluss der unabhängigen Alpha-Controls wurde eine rein technische
Foundation für die spätere Portfolio- und Execution-Schicht ergänzt.

Portfolio:
- deterministische Validierung bereits festgelegter signierter Exposures
- explizite Gross-, Net- und Per-Symbol-Limits
- deterministische Sleeve-Komposition
- keine automatische Normalisierung, Optimierung oder Auswahl

Execution/Kosten:
- separates opt-in Kostenmodell für Gebühr, Slippage und Spread
- explizite Round-Trip-Kosten
- explizite Short-Borrow-Kosten pro Tag
- bestehende PaperBroker-/Backtest-Defaults wurden bewusst nicht verändert

Die Foundation verändert keine bestehende Strategie, keine Research-Gates,
keine Produktionskonfiguration und führt keine Orders aus.

Dauerhafte Evidenzablage:
- portfolio/allocator.py
- execution/cost_model.py
- docs/PORTFOLIO_EXECUTION_FOUNDATION.md
- research/checkpoints/portfolio_execution_foundation_2026_09_24.json

### 2v. Portfolio Risk-Parity — Trial 022 Ergebnis — 2026-09-24

Trial T-2026-09-24-022 wurde vollständig und reproduzierbar auf zwei neuen,
symbol-disjunkten U.S.-Aktienuniversen ausgeführt. Die zugrunde liegenden
Trend-/Cross-Sectional-Signale blieben unverändert; ausschließlich die
Portfolioaggregation wurde als präregistrierter Control verändert.

- Workflow-Run: 36012719190
- Artifact-ID: 10813113637
- Artifact-Digest: sha256:a2419c933b4f0d84adf4cd7e187deb1bfa4261691bffa12f1dddf829bbeb1ed7
- Trend-Manifest: e102276bb387ca7174271c663402d17f445d77fcd3cde23d0e54854b807ab657
- CS-Manifest: 2a4dd8c6d67041c388fb41518faf6d16d68e8d785356b322e8380de5f69d72ab
- Report-Fingerprint: feeb659b4c0ac59082e333200327e1b44407902c6f69e5fd72f75dd9c16c4313
- Code-Commit: 757da1ba764db79c9c602f6f5cd71f035cbbecf2
- 13 Assets, 3.500 Candles/Asset, 3.498 Returns, Research/Holdout 2.798/700
- vollständige Testsuite: 628 bestanden
- Paper-only, Universums-Disjointness, Präregistrierung und Ergebnisintegrität: bestanden
- keine Auswahl, keine Parameter-/Gewichtssuche, keine Orders

### Fachlicher Befund

Dynamische 63-Sessionen-Inverse-Volatilität:

- Research: +103,90%, DD 42,93%, PF 1,090
- Holdout: +100,52%, DD 23,83%, PF 1,273
- Rolling Research: 4/5 profitable Fenster
- OOS/Research-Ratio: 0,967
- Holdout-Turnover: 17,18; davon Allokations-Turnover 4,97

Unveränderte 50/50-Referenz:

- Research: +121,73%, DD 41,29%, PF 1,093
- Holdout: +114,92%, DD 24,87%, PF 1,289

Damit verbessert die dynamische Allokation zwar den Holdout-Drawdown geringfügig
und erfüllt Return-, Rolling-, OOS/IS-, Holdout-PF- und Kostenstress-Bedingungen.
Sie verfehlt jedoch die harten Drawdown-Grenzen von 10% in Research und Holdout,
liegt beim Research-PF knapp unter 1,10 und verschlechtert gegenüber 50/50 sowohl
Research- als auch Holdout-Return und PF.

### Entscheidung

NO_SUPPORT / archived_rejected.

Keine Produktionsintegration, keine Gewichtsanpassung und keine erneute Suche über
Lookback, Caps oder Allokationsregeln aus diesem Holdout-Befund.

Der nächste methodische Schritt ist eine Failure-Diagnose der Portfolioaggregation:
insbesondere die Trennung von Allokations-Turnover/Kosten, Sleeve-Risiko und der
Frage, ob die dynamische Gewichtsänderung tatsächlich die Drawdown-Failures adressiert.

### 2w. Portfolio Risk-Parity Failure-Diagnose — 2026-09-24

Trial 022 wurde nicht promotet. Die deskriptive Failure-Diagnose ist abgeschlossen.
Sie führt keine neue Parameter- oder Gewichtssuche und keine Gateänderung durch.

- Holdout-Drawdown gegenüber 50/50: ca. 1,04 Prozentpunkte niedriger
- Holdout-Return gegenüber 50/50: ca. 14,40 Prozentpunkte niedriger
- zusätzlicher Allokations-Turnover: 4,97
- mechanischer zusätzlicher Holdout-Kosten-Drag: ca. 0,64 Prozentpunkte
- durchschnittliche Holdout-Gewichte: 59,46% Trend / 40,54% Cross-Sectional
- das verbleibende Return-Residuum wird ausdrücklich nicht kausal interpretiert

Konsequenz:
- kein Risk-Parity-Tuning
- keine Lookback-/Cap-/Normalisierungssuche
- keine Produktionsintegration der dynamischen Allokation

### 2x. Execution-Kosten-Semantik-Audit — 2026-09-24

Der Research-Kostenstandard ist jetzt explizit als Contract abgesichert:
10 bps Fee + 5 bps Slippage = 15 bps One-Way bzw. 30 bps Round Trip.

BacktestEngine und ExecutionCostModel entsprechen diesem Contract. Der historische
PaperBroker-Default liegt bei 5 bps Fee + 5 bps Slippage und wird deshalb fail-closed
als nicht research-kompatibel erkannt. Der PaperBroker wurde nicht rückwirkend verändert.

Dauerhafte Ablage:
- execution/cost_contract.py
- docs/EXECUTION_COST_AUDIT.md
- research/checkpoints/execution_cost_audit_2026_09_24.json

### 2y. PaperBroker Research-Kostenpfad — 2026-09-24

Der historische PaperBroker-Default bleibt unverändert bei 5 bps Fee + 5 bps
Slippage. Für research-kompatible Paper-Simulation existiert jetzt ein expliziter
Opt-in über den zentralen ResearchExecutionCostContract mit 10 bps Fee + 5 bps
Slippage.

Die vollständige Regression und der dedizierte Kosten-Audit sind grün.
Keine Strategie-, Gate- oder historische Ergebnisänderung.

### 2z. Governed Champion/Challenger-Accounting — 2026-09-24

Die bestehende Champion/Challenger-Schicht ist jetzt an den zentralen
Evidence-Contract gebunden.

- Vergleich nur bereits vorhandener Evidence-Snapshots
- gemeinsame Gates und Provenienzänderungen werden deterministisch dokumentiert
- Holdout-Nutzung zur Selektion wird explizit blockierend markiert
- Paper-only-Sicherheit wird geprüft
- kein Ranking, kein Gewinner, keine automatische Promotion
- keine Parameter-, Gewicht-, Threshold- oder Asset-Suche

Dauerhafte Ablage:
- research/champion_challenger.py
- docs/GOVERNED_CHAMPION_CHALLENGER_ACCOUNTING.md
- research/checkpoints/governed_champion_challenger_accounting_2026_09_24.json

### 2aa. MAX-Effect Cross-Sectional Control — Trial 023 — 2026-09-24

Trial T-2026-09-24-023 wurde vollständig und reproduzierbar auf einem neuen,
vollständig symbol-disjunkten U.S.-Aktienuniversum ausgeführt.

- Workflow-Run: 36016871406
- Artifact-ID: 10815121247
- Report-Fingerprint: bfaeb216996b2f32acd55fff06e217344f24de6aca373a661bedd873c06bb594
- Manifest-Fingerprint: 66a17c515f85af51cfbd6d4402fc67c9d2c6cbb215eefdfe459052e2d5618d6b
- Code-SHA des Workflow-Laufs: 3b05c02c16901329112814bdb1c7d3486df88fff
- ORCL, CSCO, TXN, ADP, UPS, ABT, GILD, AMGN
- 3.500 Candles/Asset, 3.498 Returns, Research/Holdout 2.798/700
- vollständige Vorprüfungen, Ergebnisintegrität und Artifact-Upload: grün
- keine Parameter-/Threshold-/Asset-Suche, keine Holdout-Selektion, keine Orders

Basis:

- Research: +285,84%, DD 24,63%, PF 1,148, Rolling 4/5
- Holdout: +38,85%, DD 16,26%, PF 1,144
- OOS/Research-Ratio: 0,136
- Low-MAX minus High-MAX: Research +1,44 bps/Tag; Holdout -0,41 bps/Tag
- 1,5x Kostenstress Holdout: +35,80%
- 2x Kostenstress Holdout: +32,82%

Entscheidung: NO_SUPPORT / archived_rejected.

Die absoluten Drawdown-Gates, die OOS/Research-Schwelle und der positive
Holdout-MAX-Edge werden verfehlt. Keine MAX-Varianten-, Fenster-, Auswahlbreiten-
oder Kosten-Suche wird daraus abgeleitet.

Dauerhafte Evidenzablage:
- docs/trial_023_max_effect_result_2026_09_24.md
- research/checkpoints/trial_023_max_effect_result_2026_09_24.json
- research/evidence/trial_ledger.json

### 2ab. MAX-Effect Failure-Diagnose — 2026-09-24

Der wichtigste deskriptive Befund ist die fehlende Holdout-Stabilität des
Charakteristiksignals: Der Low-MAX-vs-High-MAX-Edge dreht von +1,44 bps/Tag im
Research auf -0,41 bps/Tag im Holdout.

Zusätzlich liegen die Holdout-Rendite nur bei +38,85%, der Holdout-Drawdown bei
16,26% und die OOS/Research-Ratio bei 0,136. Der Kostenstress bleibt zwar
positiv, beseitigt aber weder den Drawdown-Failure noch die OOS-Schwäche.

Der Control wird nicht integriert. Die Failure-Diagnose ist deskriptiv; es wird
keine Kausalität oder Übertragbarkeit auf die Literatur behauptet.

### 2ac. Low-Volatility Cross-Sectional Control — Trial 024 — 2026-09-24

Trial T-2026-09-24-024 wurde vollständig und reproduzierbar auf einem neuen,
vollständig symbol-disjunkten U.S.-Aktienuniversum ausgeführt.

- Workflow-Run: 36018203202
- Artifact-ID: 10814949024
- Report-Fingerprint: feb4376f1da051aa157efba098354ffce13ecc75969b4ded849dd90f8e9f1203
- Manifest-Fingerprint: b8359acf7d532c6989dd41b31d6d8fdd836b3b1668c20b6fcadf3e2cfc0695da
- Code-SHA des Research-Laufs: feead383cde51b310a535cbeb439a616bf0ec246
- INTC, QCOM, AVGO, HON, LMT, RTX, CSX, NSC
- 3.500 Candles/Asset, 3.498 Returns, Research/Holdout 2.798/700
- vollständige Vorprüfungen und Ergebnisintegrität: grün
- keine Parameter-/Threshold-/Asset-Suche, keine Holdout-Selektion, keine Orders

Basis:
- Research: +146,08%, DD 42,53%, PF 1,108, Rolling 5/5
- Holdout: +46,03%, DD 18,54%, PF 1,175
- OOS/Research-Ratio: 0,315
- Low-Vol minus High-Vol: Research -3,17 bps/Tag; Holdout -10,40 bps/Tag
- 1,5x Kostenstress Holdout: +45,81%
- 2x Kostenstress Holdout: +45,59%

Entscheidung: NO_SUPPORT / archived_rejected.

Die Low-Vol-Charakteristik erfüllt zwar Return-, PF-, Rolling-, OOS/Research- und
Kostenstress-Bedingungen, verfehlt aber die absoluten Drawdown-Gates und den
Low-Vol-Edge bereits im Research sowie erneut im Holdout. Keine weitere
Low-Vol-Suche oder Produktionsintegration.
### 3. Micro-Trading: aktueller Abschluss des 5m-Controls

PR #39 und der anschließende CI-Fix PR #40 sind gemerged.

Der reproduzierte 5m-Control wurde vollständig und ohne Fehler archiviert:

- Run: 35864646499
- Artifact-ID: 10752437642
- Artifact-Digest: sha256:dd61e11247d0c8016efd4200419176aa44b589002071922415fd987a06700a26
- Ergebnis-Fingerprint: 4b1328912a1b8dac35e1a4bbf2993e449a48c04d352f7e987d0ffeb3aa367fb5
- vollständige Testsuite im Control: 430 bestanden
- Paper-Only und Ergebnisintegrität: bestanden
- keine Orders

5m-Ergebnis auf AAVEUSDT / XLMUSDT / ALGOUSDT / FILUSDT:

- Long 1x, 0x Kosten: +32,33% Holdout, DD 9,32%, PF 1,069, Turn-t-Stat 1,83
- Long 1x, 0,25x Kosten: -99,11% Holdout
- Short 1x, 0x Kosten: -26,34% Holdout, DD 32,42%, PF 0,935
- Buy-and-Hold-Proxy: +34,32% Holdout

Der 5m-Control liefert damit keinen eigenständigen kostenrobusten Nachweis.
Der Long-0x-Befund liegt nahe am Buy-and-Hold-Proxy und fällt bereits bei einem
Bruchteil des Projektkosten-Basissatzes massiv ab. Short liefert bereits ohne
Kosten einen negativen Holdout-Befund.

### 5. Gesamtfokus ab jetzt

Die Gap-Reversal-Familie ist abgeschlossen: technische Trials 018–020 und
vollständiger negativer Trial 021; kein weiteres Gap-Reversal-Tuning.

Trial 022 zur lagged 63-Sessionen-Inverse-Volatilitäts-Allokation ist abgeschlossen
und nicht promotet. Die Failure-Diagnose zeigte keine ausreichende Robustheit.

Trial 023 zur monatlichen Low-MAX-Charakteristik ist ebenfalls abgeschlossen und
nicht promotet. Der Research-Edge dreht im Holdout ins Negative; Drawdown und
OOS/Research bleiben unzureichend. Keine weitere MAX-Suche.

Daten-/Kalenderausrichtung, Execution-Kostenvertrag und Champion/Challenger-
Accounting sind technisch gehärtet.

Nächster Forschungsschritt:
Eine einzelne, orthogonale, vorab präregistrierte Charakteristik- oder Signal-
Hypothese auf einem vollständig neuen und symbol-disjunkten Datensatz. Vor dem
Research-Lauf werden Datenverfügbarkeit, PIT-Semantik, Kostenvertrag, Safety und
Holdout-Nichtauswahl in CI geprüft.

Bestehende Signale, Parameter, Gewichte und Gates bleiben unverändert.
Kein Live-Trading und keine automatische Produktionspromotion.

## Literaturreferenz für den Micro-Control

Shanaev, Vasenin und Stepanov, „Turn-of-the-candle effect in bitcoin returns“,
Heliyon 9(3), 2023, DOI 10.1016/j.heliyon.2023.e14236.
Die Studie nutzt 1-Minuten-Daten und definiert den Turn-of-the-Candle-Effekt an
Minute 00/15/30/45. Das Repository verwendet diese Arbeit ausschließlich als
Hypotheseninspiration; Ergebnisse werden unabhängig überprüft.

---

Stand: 2026-09-23
Basis: aktueller `master`-Stand nach PR #37.

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

Holdout:
- Continuation und Reversal fallen unter dem getesteten 0,15%-Basiskostensatz
  beide auf nahezu -100%
- Buy-and-Hold über BTC/ETH war im selben Kontrolllauf positiv

#### PR #33 — Directional Short/Long + fester Hebel

PR #33 ist gemerged.

Vollständig symbol-disjunkter Kontrollsatz:
SOLUSDT / BNBUSDT / XRPUSDT / ADAUSDT.

Feste Richtungen:
- Continuation: positiv -> Long, negativ -> Short
- Reversal: positiv -> Short, negativ -> Long

Holdout, 0x Kosten:
- Continuation 1x: -43,89%, DD 55,38%, PF 0,966
- Reversal 1x: +58,88%, DD 28,06%, PF 1,036
- Reversal 3x: +183,60%, DD 66,19%, PF 1,036

Der Reversal-Effekt kollabierte bereits bei 0,5x des Projekt-Basissatzes
(~0,075% je Turnover-Einheit) auf nahezu -100%.

#### PR #35 — Holding-Horizon / Turnover-Control

PR #35 ist gemerged.

Vollständig symbol-disjunkt:
DOGEUSDT / LTCUSDT / LINKUSDT / AVAXUSDT.

Vorab feste Horizonte:
- H1 = 15 Minuten
- H4 = 60 Minuten
- H16 = 240 Minuten

Reversal, 1x, Holdout:
- H1 / 0x: +89,12%, DD 31,45%, PF 1,046, Turnover 40.000
- H4 / 0x: +227,50%, DD 11,86%, PF 1,082, Turnover 9.999
- H4 / 0,1x: -26,91%, PF 0,984
- H16 / 0x: +66,17%, DD 17,07%, PF 1,037, Turnover 2.499
- H16 / 0,1x: +14,22%, DD 21,96%, PF 1,013
- H16 / 0,25x: -34,92%, PF 0,977

Der Turnover sinkt mit der Haltedauer stark, aber die ökonomische Robustheit
bleibt unzureichend. Beim H16/1x/0x-Research waren vier von fünf Rolling-
Fenstern negativ.

#### PR #37 — unabhängige Holding-Horizon-Replikation

PR #37 ist gemerged.

Identisches Protokoll auf einem vierten, vollständig symbol-disjunkten Satz:
DOTUSDT / ATOMUSDT / UNIUSDT / NEARUSDT.

Die Replikation ergibt:
- Continuation ist bei 1x/0x über H1, H4 und H16 negativ.
- Reversal ist bei 1x/0x:
  - H1: +179,82%, DD 45,40%, PF 1,059, Turnover 40.000
  - H4: +41,61%, DD 33,84%, PF 1,023, Turnover 9.999
  - H16: -4,98%, DD 31,57%, PF 1,002, Turnover 2.499
- Bereits bei 0,1x Kosten sind die Reversal-Holdouts H1/H4/H16 jeweils
  deutlich negativ.
- Auch bei H16 zeigt die Forschung keine stabile Übertragung: drei von fünf
  Rolling-Fenstern sind negativ; der Gesamt-Holdout-PF liegt praktisch bei 1.

Damit wurde die in PR #35 beobachtete H16-/0,1x-Spur nicht repliziert.
Der bisherige einfache 15m-Directional-Reversal-Ansatz ist daher kein belastbarer
Micro-Edge und wird nicht in die Produktionsarchitektur übernommen.

Technischer Kontrollstatus:
- 412 Tests
- Paper-Only-Safety grün
- vollständiger Protokoll-/Symbol-Guard grün
- Ergebnis-Fingerprint:
  `47646775594402e9e39bd687272c1ad1955a4fe75013b642d59dea2a3575d17a`
- Artifact-ID: `10750207859`
- keine Orders, keine Produktionsintegration

### Aktueller Micro-Gesamtbefund

Vier voneinander unabhängige Micro-Kontrollen zeigen ein konsistentes
wissenschaftliches Bild:

- Ein einfacher 15m-Continuation-Ansatz trägt nicht.
- Ein einfacher 15m-Reversal-Ansatz kann starke Vor-Kosten-Returns erzeugen,
  aber diese sind extrem sensitiv auf Kosten und Turnover.
- Längere Holding-Horizonte reduzieren Turnover, erzeugen aber keinen replizierten
  kostenrobusten Edge.
- Shorting und 3x Hebel vergrößern die Exposure; sie liefern keinen separaten
  Evidenznachweis für einen nachhaltigen Edge.
- Die bisher getestete Micro-Familie bleibt damit ein Forschungsbefund, nicht
  ein Produktionskandidat.

### Ein letzter andersartiger Micro-Control

Statt die gescheiterte Bar-to-Bar-Richtung weiter zu variieren, wird genau ein
andersartiger, literaturbasierter Kontrollmechanismus geprüft: der sogenannte
Turn-of-the-Candle-Effekt, bei dem sich Renditen an den 15-Minuten-Grenzen
konzentrieren sollen.

Dieser Ansatz ist methodisch anders, weil das Signal kalender-/zeitbasiert ist
und nicht aus der Richtung des unmittelbar vorherigen Bars abgeleitet wird.

Der Control bleibt strikt getrennt:
- neue symbol-disjunkte 5m-Datenbasis
- feste UTC-Minutenmodulo-Regel für 00/15/30/45
- feste Long-/Short-Richtung als Gegenkontrollen
- 1x / 2x / 3x Exposure
- feste Kosten-Sensitivität
- keine Optimierung und keine Übernahme in die Tagesstrategie

Ein positives Ergebnis wäre weiterhin nur eine Forschungsreplikation. Erst bei
robuster, kostenfester und unabhängiger Evidenz würde ein realistischerer
Execution-Control folgen.

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

## Aktueller Checkpoint — Trial 026 Common-Market-Momentum-Gate — 2026-09-24

Trial T-2026-09-24-026 wurde vollständig und reproduzierbar auf
DWR-debug/trading-agent-public ausgeführt und als NO_SUPPORT /
archived_rejected abgeschlossen.

### Technischer Nachweis

- PR #130, anschließend gemerged
- Merge-Commit: f6d3e27d000df688b65a46c2407e349f75ed5651
- Workflow-Run: 36026930038
- Artifact-ID: 10820420657
- Artifact-SHA256: sha256:600c70bbb015c026208299dcee6ac3b370d580d7f29da2fcabdc7518e69c3523
- Report-Fingerprint: 094e7d6264ecfc96dbe8ce3b1770543754e1df66a5fa572fafa6c6a071c47e73
- Manifest-Fingerprint: 6b8b0405adb5b95b31b14b4b81432eaa789dead64860c027c7cd22b159a29dda
- 3.500 Candles je Symbol
- 3.498 gemeinsame PIT-Returns
- 2.798 Research / 700 Holdout
- vollständige Vorprüfungen und Ergebnisintegrität: grün
- keine Orders

### Fachlicher Befund

Die feste Common-Market-Gate-Intervention verschlechterte den festen
50/50-Kandidaten deutlich:

- Research: +27,58 % -> -4,99 %
- Research-DD: 23,37 % -> 34,01 %
- Research-PF: 1,054 -> 0,996
- profitable Rolling-Fenster: 4/5 -> 2/5
- Holdout: +1,41 % -> -0,79 %
- Holdout-DD: 19,95 % -> 19,69 %
- Holdout-PF: 1,018 -> 1,003

Nur der Holdout-Drawdown wurde marginal verbessert. Die Intervention verfehlte
sämtliche zwölf absoluten Prüfkriterien und vier der fünf
Nicht-Verschlechterungsbedingungen.

Das Gate war im Research in 76,73 % und im Holdout in 99,57 % der Perioden
aktiv. Trotz nahezu vollständiger Aktivierung im Holdout blieb die
Holdout-Rendite negativ. Dieser Befund ist deskriptiv.

### Konsequenz

- keine Threshold-/Lookback-Suche
- keine zweite Gate-Variante auf demselben Datensatz
- keine Änderung am festen Kandidaten
- keine Leverage-/Short-Ausweitung
- keine Produktionsintegration
- keine Orders

### Nächster methodischer Fokus

Nach Trial 026 wird die Forschung nicht in eine weitere allgemeine
Volatilitäts-/Cash-Gate-Suche ausgeweitet. Die bereits vorhandene
Cross-Sectional-Reversal-Diagnostik ist die nächste vorgesehene
orthogonale Hypothesenquelle. Eine daraus abgeleitete Intervention muss erneut
präregistriert, vollständig symbol-disjunkt und holdout-blind validiert werden.

Dauerhafte Ablage:

- docs/trial_026_common_market_momentum_gate_result_2026_09_24.md
- research/checkpoints/trial_026_common_market_momentum_gate_result_2026_09_24.json
- research/evidence/trial_ledger.json

### Sicherheitsstatus

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Research-Orders
- keine Live-Ausführung


## Aktueller Checkpoint — Trial 027 Fixed TSM Ensemble Trend Sleeve — 2026-09-24

Trial T-2026-09-24-027 wurde vollständig auf `DWR-debug/trading-agent-public`
ausgeführt und als **NO_SUPPORT / archived_rejected** abgeschlossen.

### Technischer Nachweis

- PR #132 gemerged
- Workflow-Run: `36029169717`
- Artifact-ID: `10820593251`
- Artifact-SHA256: `sha256:1320c20515be7d24e64f23d9af7090ab4c9f9bb53b6e17c16b924a84e878c247`
- Report-Fingerprint: `57b87f09de867cb2ef535aaf7e6132618d5e116ca36b04d9968cc8c5b327cf51`
- Manifest-Fingerprint: `c817bd74d4912316726dbc51347fe0dab22049acadd753bef0bdece89fe59748`
- 13 neue vollständig symbol-disjunkte ETFs
- 3.500 Candles je Asset
- 3.498 gemeinsame PIT-Returns
- 2.798 Research / 700 Holdout
- Vorprüfungen, vollständige Testsuite, Safety und Ergebnisintegrität: grün
- keine Orders

### Fachlicher Befund

Fixed Candidate vs. TSM Challenger im Base-Szenario:

- Research Return: +57,55 % -> +56,76 %
- Research DD: 16,34 % -> 16,52 %
- Research PF: 1,096 -> 1,096
- profitable Rolling-Fenster: 4/5 -> 4/5
- Ø Rolling DD: 12,82 % -> 13,32 %
- OOS/IS: 0,461 -> 0,521
- Holdout Return: +26,55 % -> +29,57 %
- Holdout DD: 13,45 % -> 10,66 %
- Holdout PF: 1,164 -> 1,182

Der Challenger verfehlt weiterhin Research-Drawdown, Research-PF,
Rolling-PF, durchschnittlichen Rolling-Drawdown und Holdout-Drawdown.
Der Nicht-Verschlechterungsvertrag scheitert bei Research-Return,
Research-Drawdown und durchschnittlichem Rolling-Drawdown.

### Konsequenz

- keine TSM-Lookback-Suche
- keine TSM-Definition ändern
- keine Gewichtsanpassung
- keine Gate-Lockerung
- keine Produktionsintegration
- keine Echtgeldfreigabe
- keine Orders

Dauerhafte Ablage:

- `docs/trial_027_tsm_ensemble_trend_sleeve_result_2026_09_24.md`
- `research/checkpoints/trial_027_tsm_ensemble_trend_sleeve_result_2026_09_24.json`
- `research/evidence/trial_ledger.json`

### Sicherheitsstatus

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Research-Orders
- keine Live-Ausführung


## Aktueller Checkpoint — Trial 028 Per-Sleeve Volatility Budget — 2026-09-24

Trial T-2026-09-24-028 wurde vollständig und reproduzierbar ausgeführt und als **NO_SUPPORT / archived_rejected** abgeschlossen.

### Technischer Nachweis

- PR #134 gemerged
- finaler Workflow: `36038357899`
- Artifact-ID: `10825414801`
- Artifact-SHA256: `sha256:1d733848e28cdecf0c7ea9a5a85dcf0cf9f089fa79eeaafe341c424743c74834`
- Report-Fingerprint: `ee00872c970d9c6935ced344a5642b5b17e27e8ce072a97462518b5a203bc57a`
- Manifest-Fingerprint: `f99f1b40c931c860987c26c65fe988a9d140c866f7370fddad2e40af2ec9b2dd`
- 13 neue vollständig symbol-disjunkte ETFs
- 3.500 Candles je Asset
- 3.498 gemeinsame PIT-Returns
- 2.798 Research / 700 Holdout
- 662 Tests und alle Vorprüfungen: grün
- keine Orders

### Fachlicher Befund

Der per-Sleeve-Volatilitäts-Control reduziert den Research-Drawdown von 22,48 % auf 17,55 %, erhöht den Research-PF von 1,075 auf 1,085 und reduziert den Holdout-Drawdown von 10,25 % auf 9,65 %; gleichzeitig sinkt der Research-Return um 0,44 Prozentpunkte und der Holdout-Return um 0,21 Prozentpunkte.

Damit bleibt der Control **BLOCKED / NO_SUPPORT**: alle Research-Risiko-/PF-Gates sind noch nicht vollständig erfüllt und die Return-Nicht-Verschlechterung gegenüber dem Fixed Candidate scheitert.

### Konsequenz

- kein Tuning
- keine weitere Cash-/Volatilitäts-Gate-Suche
- keine Produktionsintegration
- keine Echtgeldfreigabe
- keine Orders

### Nächster methodischer Fokus

Kapitalallokation zwischen den bestehenden Sleeves: ein einmalig präregistrierter,
fixer Risk-Parity-/Risk-Contribution-Control auf einem neuen vollständig
symbol-disjunkten Datensatz, mit identischem Kosten-, PIT- und Holdout-Vertrag.

Dauerhafte Ablage:
- `docs/trial_028_per_sleeve_vol_budget_result_2026_09_24.md`
- `research/checkpoints/trial_028_per_sleeve_vol_budget_result_2026_09_24.json`
- `research/evidence/trial_ledger.json`

### Sicherheitsstatus

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Research-Orders
- keine Live-Ausführung


## Aktueller Checkpoint — Trial 029 DATA_INVALID — 2026-09-24

Trial T-2026-09-24-029 wurde vor jeder Performanceauswertung als **DATA_INVALID** abgeschlossen.

- Workflow: `36039285580`
- Artifact: `10826146206`
- Artifact-SHA256: `sha256:652627afbe7ab0cb39d374d986a32d265c779d9f96b27f233d3b8108477fc036`
- Ziel: 3.500 Candles je Symbol
- 12/13 Symbole: 3.520 Candles
- IEFA: 3.496 Candles
- gemeinsamer Kalender: 3.496
- keine Research-/Holdout-Evaluation
- keine wissenschaftliche Performanceaussage

Die Abweichung entstand durch die tatsächliche historische Abdeckung von IEFA;
der Datenvertrag wurde weder gelockert noch nachträglich angepasst.

### Konsequenz

Trial 029 wird nicht als negatives Performance-Ergebnis gewertet. Der nächste
Researchsatz wird vor der Präregistrierung ausschließlich auf historische
Datenabdeckung und gemeinsamen Kalender vorgeprüft. Erst ein bestandenes
Coverage-Preflight wird als neuer, vollständig disjunkter Trial präregistriert.

### Sicherheitsstatus

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Research-Orders
- keine Live-Ausführung


## Aktueller Checkpoint — Trial 030 Sleeve Volatility Parity Confirmation — 2026-09-24

Trial T-2026-09-24-030 wurde vollständig auf `DWR-debug/trading-agent-public` ausgeführt und als **NO_SUPPORT / archived_rejected** abgeschlossen.

- Coverage-Preflight: `36040186007`
- Research-Workflow: `36040997311`
- Artifact: `10825679094`
- Artifact-SHA256: `sha256:cc46dfadb3581fab21012b651b857b32e06a43dc37399d45479423da899f2191`
- Report-Fingerprint: `26cc96a1d7210a97443016f5374fccc2e1c466ce2eb1f6859ca778c9a3eefabe`
- Manifest-Fingerprint: `9ef4c9fa58e6a8a573d0836379572d7a441a2fb5300fc4eca33155b2059cf224`
- 3.498 gemeinsame PIT-Returns; 2.798 Research / 700 Holdout
- vollständige Vorprüfungen und Ergebnisintegrität grün; keine Orders

### Befund

Fixed 50/50: Research +32,69 %, DD 18,30 %, PF 1,064; Holdout +23,54 %, DD 12,37 %, PF 1,148.

Sleeve-Parity: Research +21,19 %, DD 19,19 %, PF 1,046; Holdout +23,56 %, DD 12,32 %, PF 1,149.

Damit verbessert der Control die Holdout-Seite nur marginal, verfehlt aber die Research-Gates und den Nicht-Verschlechterungsvertrag.

### Konsequenz

Keine weitere Risk-Parity-/Volatility-Parity-Suche und kein Tuning dieses Controls. Der nächste Fokus wechselt auf einen signalbasierten Cross-Sectional-Control: feste 12-1-Rendite geteilt durch formation-periodische Realized Volatility, auf einem neuen vollständig disjunkten Universum.

### Sicherheitsstatus

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Research-Orders
- keine Live-Ausführung


## Aktueller Gesamtcheckpoint — Trial 031 abgeschlossen — 2026-09-24

Trial T-2026-09-24-031 wurde auf dem öffentlichen Arbeitsrepository vollständig ausgeführt, ausgewertet und anschließend archiviert.

- PR #142: gemerged
- Merge-Commit: `52f51aff2e9aeb828f8d3c5c2889bd4960cef0f8`
- Research-Workflow: `36043071782`
- Artifact: `10826903506`
- Artifact-Digest: `sha256:9b42882a4ee9082c2b6194f4b671513b7da50685d850bac561aaa3df1bab551a`
- Report-Fingerprint: `f22e6cad28fbfbf73495f35da056b0bb8fe80c30ecd7d54deb09385452533cad`
- 13/13 vollständig disjunkte ETFs; 3.500 Candles je Asset; 3.498 gemeinsame PIT-Returnperioden
- Research/Holdout: 2.798 / 700
- Trial-031-Prereq und Research: beide grün
- korrigierte vollständige Testsuite: **671 passed**
- Paper-only: keine Orders

### Fachlicher Befund

**NO_SUPPORT / archived_rejected**

Risk-adjusted CS gegenüber Fixed 50/50:

- Research Return: -8,37 % vs. +1,65 %
- Research Max DD: 26,77 % vs. 22,65 %
- Research PF: 0,994 vs. 1,011
- Holdout Return: +24,47 % vs. +27,14 %
- Holdout Max DD: 14,56 % vs. 15,59 %
- Holdout PF: 1,150 vs. 1,165
- profitable Rolling-Fenster: 3/5
- Rolling-PF: 0,994
- OOS/IS: 0,00

Der Control verfehlt damit mehrere absolute Research-Gates und die wesentlichen
Nicht-Verschlechterungsbedingungen. Positive Holdout-/Kostenstress-Teilbefunde
reichen nicht für eine Promotion.

### Konsequenz

- keine Integration in die Produktionsstrategie
- kein Tuning der risikoadjustierten Momentumfamilie
- Fixed Candidate bleibt **BLOCKED**
- kein 30-Tage-Paper-Experiment freigeschaltet
- nächste Forschung wechselt wieder auf eine orthogonale, signal- oder
  architekturbezogene Kontrollfrage außerhalb der bereits mehrfach geprüften
  Volatilitäts-/Risk-Layer-Varianten
- für jeden neuen Trial weiterhin: Coverage-Preflight vor Präregistrierung,
  vollständig disjunktes Universum, blinder Holdout, identischer Kostenvertrag,
  keine Holdout-Selektion

### Synchronisationsstand

Der Master enthält Trial 031 und dessen vollständige Archivierung; der exakte aktuelle HEAD wird direkt aus dem GitHub-Master-Ref gelesen. Trial 031 ist in
`research/evidence/trial_ledger.json`, in einem dauerhaften Result-Checkpoint
und in der Projektdokumentation archiviert.


## Aktueller Checkpoint — Trial 032 Relative-Value Coverage DATA_INVALID — 2026-09-24

Trial T-2026-09-24-032 wurde vor jeder Performanceauswertung als **DATA_INVALID** beendet.

- Coverage-Workflow: `36043628557`
- QQQM: 1.493 statt 3.520 angeforderter Tages-Candles
- keine Research-/Holdout-Evaluation
- kein Datenvertrag gelockert
- keine Performanceauswahl

Konsequenz: 032 wird nicht als Performanceergebnis gewertet. Für den nächsten
Preflight ersetzt 033 ausschließlich QQQM durch QQEW; alle übrigen Paare bleiben
unverändert.

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders


## Korrektur des Forschungs-Checkpoints — 2026-09-24

Die Trial-ID `T-2026-09-24-032` ist bereits formal für **Relative Value ETF Pairs** vergeben und als **DATA_INVALID** archiviert. Sie wird nicht für eine andere Hypothesenfamilie wiederverwendet.

Ein zwischenzeitlicher Residual-Momentum-Entwurf wurde ausschließlich auf einer nicht gemergten Preflight-Branch aufgebaut. Diese Branch wurde wegen nicht verfügbarer Yahoo-Ticker verworfen und ist **kein formaler Trial-Ergebnisstand**.

Konsequenz:

- T032 bleibt unverändert **DATA_INVALID / relative_value_etf_pairs**
- Residual Momentum erhält bei erneuter Verfolgung die nächste freie Trial-ID: **T033**
- kein Performance-Experiment ohne bestandenes Coverage-Preflight
- kein Lockern des Datenvertrags
- weiterhin PAPER_ONLY=True und LIVE_TRADING_ENABLED=False



## Aktueller Checkpoint — Trial 033 Relative-Value Coverage DATA_INVALID — 2026-09-24

Trial 033 wurde vor jeder Performanceauswertung als **DATA_INVALID** beendet.

- Coverage-Workflow: `36043884651`
- IEMG: 3.496 statt 3.520 Daily-Candles
- keine Research-/Holdout-Evaluation
- kein Datenvertrag gelockert

Konsequenz: 033 wird nicht als Performanceergebnis gewertet. Für 034 wird IEMG ausschließlich durch EEMV ersetzt; alle übrigen Paare und Regeln bleiben unverändert.

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
