## Aktueller verifizierter Projektstand — 2026-09-25

- Ausführungs-/Research-Repository: DWR-debug/trading-agent-public
- T043: DATA_INVALID, keine wissenschaftliche Auswertung
- T044: NO_SUPPORT / archived_rejected
- T045: präregistrierte Lifecycle-/Exit-Forschungsfrage
- T045 Status: Coverage-Preflight ausstehend
- Paper-only unverändert: PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, orders_enabled=False
- kein Parameter-/Variantentuning und keine Holdout-Selektion


## Verifizierter Projektstand — 2026-09-24

Master: `3409d52f2f70d8864fa43984d2785db698af69c7`
PR #93 ist gemerged. Der Architektur-Branch wurde damit integriert.

Verifiziert:
- Trading Agent Tests: 581 passed
- Paper-Only Safety: `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False)
- Candidate Validation: erfolgreich
- Master Push CI: Trading Agent Tests, Test und Autonomous Stock Research erfolgreich
- Production Candidate bleibt BLOCKED
- Trial 017 ist als Research-only Baseline integriert; die eigentliche Datenausführung erfolgt separat und verändert keine Produktionsparameter.

Aktueller Entwicklungszweig: architecture-2026-09-24

Neu umgesetzt:
- fail-closed Strategy Lifecycle und Research Graveyard
- Adversarial Validation primitives
- Champion/Challenger Evidence Contract
- Portfolio Risk Overlay
- point-in-time GDELT Event Parser und Event Intelligence
- Trial 017 Political Event Intelligence Baseline
- deterministische Timestamp-/Kalender-Ausrichtung für Candidate Validation

Der bestehende Production Candidate bleibt BLOCKED. PAPER_ONLY=True,
LIVE_TRADING_ENABLED=False und orders_enabled=False bleiben unverändert.

Nächster Gate:
- vollständige CI-Suite
- Review des Timestamp-Vertrags
- anschließend PR-Merge nur bei grüner Suite
- danach Trial-017-Datenausführung zunächst als Research-Control

# Trading Agent – Projektstatus und Checkpoint

Stand: 2026-09-20
Zuletzt geprüft und gesichert: 2026-09-20
Haupt-Repository: DWR-debug/trading-agent
Hauptbranch: master
Aktueller Checkpoint: e7aed92091cbb548428e8f2b3fe1ba892fd48c6b

## Zweck

Der Trading Agent ist ein Paper-Trading-/Simulationsprojekt. Ziel ist ein
systematisch entwickelter und robust geprüfter Trading-Agent für die Familie.
Forschungsergebnisse gelten niemals allein als Beweis zukünftiger
Profitabilität.

## Nicht verhandelbare Sicherheitsregeln

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- Keine echten Trades.
- Keine Aktivierung von Live-Ausführung ohne ausdrückliche menschliche
  Freigabe.
- Sicherheitsprüfungen dürfen nicht abgeschwächt oder entfernt werden.
- Forschung darf keine Sicherheitsgrenzen umgehen.
- Simuliertes Kapital bleibt von echtem Geld getrennt.

## Architektur / Arbeitsweise

ChatGPT = zentrale Steuerungs-, Analyse- und Review-Ebene.

Codex / Research-Agent = kontrollierte Ausführung von Entwicklung,
Tests, Backtests, Walk-Forward, Robustheitsprüfungen, Dokumentation und
Checkpoints innerhalb definierter Sicherheits- und Qualitätsgrenzen.

GitHub = zentrale Quelle für Code, Aufgaben, Checkpoints, Ergebnisse,
Logs und Wiederherstellung.

Der gewünschte Ablauf ist:

ChatGPT
-> Projektstatus prüfen
-> Forschungsziel definieren
-> Codex/Research-Auftrag erteilen
-> Tests und Qualitätsgates
-> Ergebnisse analysieren
-> nächsten Forschungsschritt bestimmen
-> Status/Checkpoint in GitHub sichern

## Autonomie innerhalb der Grenzen

Der Research-Agent darf innerhalb der Sicherheits- und Qualitätsregeln
selbstständig:

- Strategie-Familien auswählen,
- Parameterbereiche erweitern oder verengen,
- Hypothesen verwerfen,
- zusätzliche Datenzeiträume auswählen,
- Robustheits- und Overfit-Tests bestimmen,
- instabile/überangepasste Forschungszweige beenden,
- nächste Forschungsaufträge erzeugen.

Er darf nicht:

- Live-Trading aktivieren,
- Sicherheitsprüfungen umgehen,
- Forschungsergebnisse als Profitabilitätsbeweis behandeln,
- unkontrollierte externe Änderungen vornehmen.

## Technischer Stand

Vor der Timestamp-Reparatur wurde lokal die vollständige Pytest-Suite
mit 121 Tests ausgeführt:

- 117 bestanden
- 4 fehlgeschlagen

Die vier bekannten Fehler betrafen naive Zeitstempel, die von
data/quality.py korrekt abgelehnt werden:

- tests/test_data_loader.py::test_load_valid_csv
- tests/test_data_loader.py::test_candles_are_sorted_by_timestamp
- tests/test_data_pipeline.py::test_csv_data_passes_quality_validation
- tests/test_data_quality.py::test_valid_candles_are_accepted

Ursache:
data/quality.py verlangt timezone-aware UTC-Timestamps. CSV- und
MarketDataStore-Pfade erzeugten an bestimmten Stellen naive Timestamps.

Geplanter Fix:
- validate_candles() bleibt streng.
- CSV-Timestamps ohne Offset werden als UTC interpretiert.
- CSV-Timestamps mit Offset werden nach UTC normalisiert.
- MarketDataStore.load() liefert UTC-aware UTC-Timestamps.
- Negative Tests für direkte naive Timestamps bleiben erhalten.
- Binance-Loader bleibt unverändert.
- Danach vollständige Testsuite; Commit nur bei grüner Suite.

## GitHub / Automation

GitHub-Zugriff über den ChatGPT Codex Connector ist jetzt verifiziert.

Repository-Zugriff:
- DWR-debug/trading-agent: zugänglich
- private Repository
- Connector kann lesen und schreiben

Bestehender Test-Workflow:
.github/workflows/tests.yml
- Push, Pull Request und manuell
- Python 3.13
- pytest
- Paper-Trading-Sicherheitsprüfung

Vorhandener Entwicklungsauftrag:
.github/agent_tasks/fix_timestamp_quality.md

## Codex Smoke Test

Angelegt am 2026-09-20:

- .github/agent_tasks/codex_smoke_test.md
- .github/workflows/codex-smoke-test.yml

Der Workflow läuft nur per workflow_dispatch und verwendet:

- openai/codex-action@v1
- permission-profile: :read-only
- safety-strategy: drop-sudo

Testlauf:
- GitHub Actions Run: 35520828914
- Ergebnis: FAILURE
- Ursache: API-Anfrage wurde wegen fehlender OpenAI-API-Credits beendet.
- Log: "You have no credits remaining."
- Wichtig: GitHub Checkout, Repository-Zugriff, Codex-Action, Codex CLI
  und read-only Sandbox wurden bis zum eigentlichen API-Stream erfolgreich
  durchlaufen.
- Codex konnte deshalb die eigentliche Projektanalyse und Testsuite in
  diesem Lauf noch nicht durchführen.

Nach Wiederherstellung von API-Guthaben:
1. denselben Smoke-Test erneut starten;
2. Codex-Ausgabe prüfen;
3. sicherstellen, dass keine Projektdateien verändert wurden;
4. Paper-Trading-Sicherheitswerte erneut prüfen.

## Entwicklungsphasen

Phase 1 – Infrastruktur / Smoke Test
- GitHub-Connector installiert und Repository-Zugriff verifiziert.
- GitHub Actions verifiziert.
- Codex Action technisch gestartet.
- offen: erfolgreicher Codex-Lauf nach Wiederherstellung des API-Guthabens.

Phase 2 – Controlled Development
- Codex soll einen klar begrenzten Auftrag analysieren.
- Änderungen nur auf separatem Branch.
- Vollständige Testsuite.
- Review der Änderungen.
- PR statt unkontrolliertem Push auf master.

Phase 3 – Research Automation
- Backtests
- Parameterforschung
- Walk-Forward
- Rolling Walk-Forward
- Robustheit / Overfit / Stabilität
- reproduzierbare Ergebnisse und Checkpoints

Phase 4 – Dauerhafte Research-Schleife
- nächste Forschung aus Ergebnissen ableiten
- Status, Logs und Checkpoints automatisch speichern
- unterbrochene Läufe reproduzierbar fortsetzen
- keine Live-Ausführung

## Nächste Maßnahmen

Unmittelbar:
1. API-Guthaben verfügbar machen oder automatische Aufladung sicherstellen.
2. Codex-Smoke-Test erneut ausführen.
3. Erfolgreichen Smoke-Test dokumentieren.

Danach:
4. Timestamp-Auftrag mit Codex auf einem Branch bearbeiten lassen.
5. Vollständige Testsuite muss grün sein.
6. Änderung reviewen und erst danach PR/Integration.
7. Erst nach stabilem Entwicklungsablauf Research-Automation ausbauen.

## Wiederaufnahme-Regel

Bei jeder Fortsetzung mit dem Stichwort "trading agent" zuerst diesen
Checkpoint zusammen mit dem tatsächlichen GitHub-Zustand prüfen. Nicht
aus einem veralteten Chat-Snapshot auf den aktuellen Code schließen.

Die Repository-Version ist die maßgebliche Quelle. Bei widersprüchlichen
Informationen gilt der verifizierte GitHub-Stand; Unsicherheiten werden
vor Änderungen geprüft.

## Bekannte spätere Review-Punkte

Nach dem Timestamp-Fix erneut prüfen:
- validation/walk_forward.py: Verwendung der zentralen Initialkapital-
  Konfiguration statt eines hartcodierten Werts.
- validation/rolling_walk_forward.py: Berechnung des zusammengefassten
  Profit-Factors auf exakten Trade-Daten statt einer groben Näherung.

Diese Punkte sind als Review-Aufgaben vorgemerkt und werden nicht vor dem
Timestamp-Fix verändert.


## Kostenoptimierte Research-Architektur – umgesetzt auf Branch

Der Research-Prozess wird auf lokale deterministische Rechenleistung ausgerichtet. Backtests, Parameter-Sweeps, Walk-Forward, Rolling Walk-Forward, Robustheit, Metriken und Ergebnisaggregation benötigen keine kostenpflichtige API.

Neu vorbereitet:
- automation/cost_guard.py
- automation/research_worker.py
- tests/test_cost_guard.py
- docs/COST_EFFICIENT_RESEARCH.md
- .github/workflows/research-local.yml

Die erste explizit freigegebene API-Reserve beträgt 1,00 USD. Standardmäßig gelten 0,25 USD als maximale geschätzte Kosten pro Forschungsrunde. Das restliche Guthaben bleibt unangetastet, solange kein menschlich bestätigter Budgetwechsel erfolgt.

Der Kosten-Governor ist ein Policy-Gate und kein Ersatz für die OpenAI-Abrechnung. Deterministische Forschung soll lokal ohne API-Schlüssel ausgeführt werden.

Der lokale Research-Worker erzeugt kompakte, reproduzierbare Ergebnisse unter research/results/. Rohdaten und lokale Arbeitsartefakte bleiben außerhalb des versionierten Ergebnisbereichs.

Ein self-hosted GitHub Actions Runner mit Label trading-agent-research ist für den PC vorgesehen. Die Repository-Vorbereitung ist erfolgt; die physische Einrichtung des Runners kann erst auf dem PC selbst durchgeführt werden.

## Aktueller verifizierter Projektstand — 2026-09-25

- Ausführungs-/Research-Repository: DWR-debug/trading-agent-public
- letzter verifizierter Master-HEAD vor T043: 540517c5a041b92b63d6e7bf006681e9cc0364b7
- T042: formal ausgeführt, BLOCKED / NO_SUPPORT, archiviert
- letzte Master-CI: 724 passed
- nächste präregistrierte Forschungsfrage: T043 Trend-Signal-Konsistenz
- Status: Coverage-Preflight ausstehend
- keine Parameter-/Variantensuche und keine Holdout-Selektion

Der aktuelle technische Stand wird ab jetzt nach jedem formalen Trial mit dem
Trial-Ledger und dem maschinenlesbaren Project-State abgeglichen.


## Aktueller Gesamtcheckpoint — Q010 abgeschlossen / Q011 vorgemerkt — 2026-09-25

Q-010-CROSS-TRIAL-FAILURE-DIAGNOSIS ist **COMPLETED** und wurde als rein deskriptive Governance-Diagnose ausgeführt.

Technischer Nachweis:
- Workflow: `36119705793`
- Artifact-ID: `10856102739`
- Artifact-ZIP-SHA256: `sha256:9f10a27ed267870981c8f480e868967e22c4d19a8c3562c37c9690d19dcf01c2`
- Diagnose-Fingerprint: `c11a4a2340bf4f7a9f132f53835465d57d0b12ab97770a24f3fd98492e7f9549`
- Vollständige Testsuite: **744 passed**
- Paper-only Safety: **OK**

Wiederkehrende Failure-Signatur der vier performance-validen Trials:
- Research-Risikogate: 4/4 verletzt
- Control-relative Non-Deterioration: 4/4 verletzt
- OOS/IS-Stabilität: 3/4 verletzt
- Holdout-Drawdown-Gate: 3/4 verletzt
- Positive Holdout-Rendite: 4/4, aber ohne vollständigen Evidence-Contract
- T043: DATA_INVALID und daher ohne Performanceaussage

Methodische Konsequenz:
- T041, T042, T044 und T045 werden nicht nachoptimiert.
- Kein Parameter-, Asset- oder Holdout-Re-Selection.
- Keine Gate-Lockerung.
- Kein Performance-Re-Run.
- Kein Production-Promotion-Schritt.

Nächster Research-Schwerpunkt:
`Q-011-ORTHOGONAL-INFORMATION-ALPHA-DISCOVERY`

Q011 bleibt zunächst **Discovery-only**. Eine aus Q011 abgeleitete Performancehypothese benötigt eine neue Präregistrierung, Coverage-Preflight und einen frischen vollständig symbol-disjunkten, holdout-blinden Validierungssatz.

Sicherheitsstatus:
- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- automatic_promotion=False

## Q011 Abschluss — 2026-09-25

Q-011-ORTHOGONAL-INFORMATION-ALPHA-DISCOVERY ist **COMPLETED / DISCOVERY_ONLY**.

Nachweis: Workflow 36121684164, Artifact 10857762336, Report-Fingerprint 08664ed668b61a2e149067cbe10c281f73d27b0b94ed50372877ab1203e97da8.

Der Lauf verarbeitete 3.208.523 GDELT-Zeilen und erzeugte 22 gemeinsame Marktbeobachtungen, darunter vier Event-Fenster. Die deskriptiven Beziehungen sind asset- und horizonabhängig; es wurde kein Feature für Trading ausgewählt und kein Performance-Trial autorisiert.

Die im Run-Artefakt enthaltene JSON-Datei hatte einen reinen Serialisierungsfehler: ein zusätzliches Literal `\\n` nach dem JSON-Objekt. Der eingebettete Fingerprint blieb erhalten; die Reparatur ist verlustfrei. Der Serializer-Fix ist in master und durch einen Reload-Regressionstest geschützt.

### Nächster Task

**Q-012-INFORMATION-ALPHA-TEMPORAL-STABILITY-DIAGNOSTIC** — PENDING.

Ziel ist ein längerer, vorab fixierter Zeitraum mit denselben Informationsfeatures, um zeitliche Stabilität vor einer möglichen separaten Performance-Präregistrierung zu prüfen. Keine nachträgliche Feature-Auswahl und kein Holdout-Tuning.

Sicherheitsstatus: `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`, `automatic_promotion=False`.