# Agenten-gestützte Hypothesenforschung

## Zweck

Kostenfreie Agentenressourcen werden im Trading-Agent-Projekt gezielt für Aufgaben eingesetzt, bei denen sprachliche Synthese, Gegenpositionen, Mechanismusbildung oder Forschungsdesign einen echten Mehrwert gegenüber deterministischer lokaler Berechnung liefern.

Die zentrale Regel lautet:

> **Lokale Rechenleistung für Berechnung; kostenfreie Agentenressourcen für Hypothesen.**

## Zulässige Agentenaufgaben

Agenten dürfen insbesondere:
- aus archivierter Evidenz mehrere voneinander unabhängige, mechanistisch begründete Hypothesen ableiten;
- bestehende Failure-Signaturen, Marktmechanismen und Literatur-/Domänenwissen gegeneinander abgleichen;
- Gegenhypothesen und Falsifikationsbedingungen formulieren;
- Forschungsfragen orthogonal zu bereits verworfenen Varianten entwerfen;
- Präregistrierungen, Testdesigns und Kontrollbedingungen kritisch reviewen;
- ungewöhnliche oder widersprüchliche Ergebnisse interpretieren;
- mehrere Hypothesen zu einer kleinen, explizit begründeten Forschungsliste verdichten.

## Nicht delegieren

Agentencredits werden nicht für deterministische Arbeit verbraucht, die lokal reproduzierbar und wesentlich günstiger durchgeführt werden kann:
- Backtests
- Parameter-Sweeps
- Walk-Forward-/Rolling-Berechnungen
- Datenimport und Datenqualität
- Coverage-Preflights
- Metrikberechnung
- Ergebnisaggregation
- CI-Tests
- Artefaktserialisierung
- identische Wiederholungen bereits beantworteter Rechenaufgaben

## Schutz vor Data Snooping

Agenten erhalten bevorzugt kompakte, eingefrorene Evidence-Summaries statt Rohdaten, vollständiger Trade-Listen oder Holdout-Ausgaben.

Eine Agentenantwort ist **Ideenmaterial, keine Evidenz**.

Insbesondere:
- kein Agent darf anhand des finalen Holdouts eine Hypothese auswählen;
- kein Agent darf nachträglich Parameter eines formal laufenden Trials verändern;
- keine Agentenantwort darf einen alten Trial rückwirkend optimieren;
- jede für einen Performanceversuch ausgewählte Hypothese benötigt eine neue Präregistrierung;
- die endgültige Berechnung bleibt deterministisch und reproduzierbar.

## Effizienzregel für das kostenlose Kontingent

Das kostenlose Kontingent soll möglichst viel unabhängige Denkarbeit pro verbrauchter Runde liefern.

Bevorzugtes Muster:
1. **Bündelung:** mehrere klar getrennte Hypothesenfragen in einem Agentenlauf statt vieler kleiner Folgefragen.
2. **Diversität:** unterschiedliche Denk-Linsen anfordern, z. B. Marktmechanismus, Behavioral/Information, Portfolio-Interaktion, Falsifikation.
3. **Kompakte Inputs:** nur die relevanten eingefrorenen Befunde übergeben.
4. **Strenge Ausgabeform:** pro Hypothese Mechanismus, beobachtbare Vorhersage, mögliche Falsifikation, notwendige Daten und vorgeschlagene Kontrollbedingung.
5. **Deterministische Weiterverarbeitung:** Die erzeugten Hypothesen werden anschließend lokal geprüft und nur nach Präregistrierung formal getestet.
6. **Kein Wiederholen ohne neue Information:** ein Agentenlauf wird nur wiederholt, wenn neue Evidenz oder eine klar neue Fragestellung vorliegt.

## Erste geplante Agentenrunde

### Scope

Grundlage ist die archivierte Failure-Diagnose T041/T042/T044/T045 sowie Q011.

### Auftrag

Erzeuge einen kleinen Satz orthogonaler, mechanistisch unterschiedlicher Alpha-/Informationshypothesen, die:
- nicht bloß eine weitere Variante der bereits getesteten Risiko-, Volatilitäts-, Trendkonsistenz- oder Lifecycle-Control-Familien sind;
- mit realistisch verfügbaren Tagesdaten potenziell messbar sind;
- Point-in-Time sauber formulierbar sind;
- ohne Holdout-Selektion auskommen;
- eine klare Nullhypothese und Falsifikationsbedingung besitzen;
- vor einem Performance-Trial zunächst als Discovery/Diagnostik geprüft werden können.

### Pflichtformat

Für jede Hypothese:
- Hypothesen-ID
- Mechanismus
- ökonomische Intuition
- messbare Vorhersage
- erforderliche Datenquelle
- Point-in-Time-Regel
- mögliche Confounder
- Falsifikationskriterium
- warum sie orthogonal zu T041/T042/T044/T045 ist
- minimaler deterministischer Preflight

Die Agenten dürfen **keine Gewinnerauswahl anhand von Holdout-Ergebnissen** treffen. Die Ausgabe dient anschließend als Input für eine separate, präregistrierte Research-Entscheidung.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- automatic_promotion=False
