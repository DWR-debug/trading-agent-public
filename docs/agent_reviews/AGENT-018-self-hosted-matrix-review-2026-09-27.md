# AGENT-018 – Unabhängige Review der Continuous-QA-Matrix

**Issue:** #351  
**Taskvertrag:** `TRADING_AGENT_TASK_V1`, `task_id=AGENT-018`  
**Reviewdatum:** 2026-09-27  
**Reviewtyp:** technische, report-only Prüfung  
**Geprüfter Commit:** `88b0a587b8a2ae08cffb9cc661955cb21d38dbe4`  
**Branch:** `agent/AGENT-018-copilot-cli`

## Ergebnis

Die Matrixkonfiguration ist statisch auf genau vier feste Lanes begrenzt,
`max-parallel: 2` und `fail-fast: false` sind gesetzt. Snapshot-Download und
Manifestprüfung verwenden denselben `GITHUB_SHA`; Bootstrap und temporäre Pfade
sind auf Python 3.13.15 sowie Lane, Run-ID und Attempt zugeschnitten. Die
Sicherheitsflags werden geprüft, die Worker-Ausgabe wird als nicht-formale
Provenienz gekennzeichnet, fehlende Lane-Artefakte schlagen fehl und das
Aggregate-Gate verlangt den Erfolg des Matrix-Jobs.

**Der aktuelle QA-Gate-Stand ist dennoch nicht grün:** Zwei Regressionstests
schlagen fehl. Da `repo_qa` die gesamte Pytest-Suite startet, wird dadurch die
Matrix-Lane und folglich das Aggregate-Gate fehlschlagen. Die Befunde unten
betreffen ausschließlich die technische Review; es wurden keine Workflow-,
Research- oder Evidence-Dateien geändert.

## Befunde

### F-01 – Hoch / Gate-Blocker: Zwei Pfad-Assertions schlagen in der Testsuite fehl

**Nachweis:** `tests/test_self_hosted_research_worker.py::test_self_hosted_continuous_qa_is_run_isolated`
und `::test_continuous_qa_provenance_is_published_from_workspace` erwarten
zweifache Backslashes in den Batch-Zuweisungen (`WORK`, `PROV_ROOT` u. a.).
Die geprüfte Workflow-Datei enthält einfache Backslashes, wie sie für die
Windows-CMD-Pfade verwendet werden. Der fokussierte Testlauf meldete **2 failed,
11 passed, 1 deselected**; die fehlgeschlagenen Assertions sind die beiden
genannten Tests.

**Auswirkung:** `repo_qa` führt `python -m pytest -q` ohne Selektor aus und
führt diese Tests daher ebenfalls aus. Unabhängig davon, ob die tatsächlichen
CMD-Pfade korrekt sind, verhindert der Assertion-Widerspruch einen erfolgreichen
QA-Lauf; das Aggregate-Gate muss fehlschlagen.

**Empfehlung:** In einer separaten, autorisierten Änderung die Assertions an die
tatsächliche Pfadschreibweise angleichen und die fokussierte Suite erneut
ausführen. Die gültigen Windows-CMD-Pfade nicht allein zur Erfüllung eines
fehlerhaft doppelt escapten Stringvergleichs verändern.

### F-02 – Niedrig: Kapazitäts-Provenienz wird nur auf Vorhandensein geprüft

**Nachweis:** Der PowerShell-Schritt schreibt
`runner_capacity_<lane>_<run>_<attempt>.json`. Danach prüft die Lane lediglich,
ob die Datei existiert. Inhalt, JSON-Syntax sowie `lane`, Run-ID, Attempt und
`source_commit` werden nicht validiert. `Set-Content -Encoding UTF8` in
Windows PowerShell 5.1 schreibt üblicherweise einen UTF-8-BOM; Verbraucher, die
`utf-8` statt BOM-tolerant lesen, können diese Datei nicht direkt mit
`json.loads` einlesen.

**Auswirkung:** Die Fail-closed-Prüfung sichert das Vorhandensein der
Kapazitätsdatei, nicht deren maschinenlesbaren Inhalt oder Zuordnung zum Lauf.
Die Lane- und SHA-Prüfung für `summary.json` und `run_manifest.json` bleibt davon
unberührt.

**Empfehlung:** Vor Veröffentlichung die Kapazitätsdatei mit BOM-tolerantem
UTF-8 einlesen und Syntax, Schema sowie Lauf-/Lane-/SHA-Zuordnung fail-closed
prüfen.

### F-03 – Niedrige Dokumentationsgrenze: Hosted- und Self-hosted-Ausführung
werden vermischt

**Nachweis:** Die geprüfte Workflow-Datei verwendet für Matrix-Lanes
`runs-on: windows-latest`, benennt sich „Continuous QA (hosted Python)“ und
bootstrappt Python lokal. Der Runner-Leitfaden erläutert an anderer Stelle, dass
Python-Ausführung auf GitHub-hosted Runnern erfolgt, beschreibt im
Parallelisierungsabschnitt aber Self-hosted Research-Jobs mit dem Label
`[self-hosted, trading-agent-research]` im Zusammenhang mit der Vier-Lane-Matrix.

**Auswirkung:** Betriebsleser können die tatsächliche Ausführungsumgebung und
Runner-Kapazität der Matrix missverstehen. Der Workflow selbst routet die
Matrix-Lanes nicht auf den registrierten Self-hosted Runner.

**Empfehlung:** Dokumentation klar zwischen dem hosted Python QA-Workflow und
dem registrierten Self-hosted Research-Runner unterscheiden.

## Kontrollübersicht

| Prüffeld | Ergebnis | Begründung |
|---|---|---|
| Vier feste Matrix-Lanes | **Bestanden** | Statische Liste: `repo_qa`, `data_qa`, `design_qa`, `local_reproduction`. |
| Parallelität / Fail-fast | **Bestanden** | `max-parallel: 2`, `fail-fast: false`. |
| Windows-CMD | **Statisch plausibel; Laufzeit nicht verifiziert** | Workflow nutzt `shell: cmd`, `curl.exe`, `tar.exe`, CMD-Variablen und Windows-Pfade. Regressionstests scheitern an doppelt escapten Erwartungsstrings (F-01); kein Windows-Lauf in dieser Review. |
| Lane-/Run-/Attempt-Isolation | **Bestanden** | Temporäre Lane-Artefakte und Provenienzpfade enthalten Run-ID, Attempt und Lane; der Workspace-Provenienzpfad ist je Datei ebenso differenziert. |
| Unveränderter `GITHUB_SHA` | **Bestanden mit Scope-Grenze** | codeload-URL verwendet `%GITHUB_SHA%`; das Manifest muss denselben SHA enthalten. Die heruntergeladene Archividentität wird nicht separat gehasht. |
| Python 3.13.15 | **Bestanden** | Version im NuGet-Endpunkt und in den temporären Pfaden ist festgelegt; Python-Version wird ausgegeben und `pip` geprüft. |
| Sicherheitsinvarianten | **Bestanden** | Workflow prüft `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `ORDERS_ENABLED=False`, `AUTOMATIC_PROMOTION=False`; Provenienzvalidierung prüft diese Werte erneut im Manifest. |
| Artifact-/Provenienz-Fail-closed | **Teilweise bestanden** | Lane-Manifest und Summary werden validiert; Upload läuft mit `if: always()` und `if-no-files-found: error`. Kapazitätsdatei wird nur auf Existenz geprüft (F-02). |
| Aggregate-Gate | **Bestanden** | `if: always()` plus `needs: qa_lane`; `needs.qa_lane.result` muss exakt `success` sein. |
| Keine Research-Evidence / Live-Ausführung | **Bestanden nach statischer Prüfung** | Output geht nach `research/runs/self_hosted`; kein Workflow-Schreibpfad nach `research/evidence`. Die festen Worker-Lanes enthalten QA-/Guard-/Testkommandos, keine Live-Order- oder Promotion-Ausführung; Evidence-Marker sind `false`. |

## Verifikation und Ressourcenstatus

- `python -m pytest -q tests/test_self_hosted_research_worker.py -k 'not q022'`:
  **2 fehlgeschlagen, 11 bestanden, 1 übersprungen**. `q022` wurde ausgelassen,
  um keine deterministische Research-Berechnung auszuführen.
- Der relevante GitHub-Actions-Lauf `36324393797` war beim Preflight **pending**
  auf SHA `e5e06810b60b149a4faeafb17ceda717c69c3084`; sein Resultat wurde nicht als
  abgeschlossen verifiziert.
- Der GitHub-Runner-Endpunkt verweigerte den Zugriff; Status des registrierten
  Self-hosted Runners daher **nicht zugänglich**. Kein zusätzlicher Workflow
  wurde gestartet. Paid Usage und Live-Ausführung: **nicht verwendet**.
- Die Prüfung hat keine Research-Evidence berechnet oder verändert und keine
  Holdout-, Parameter-, Asset-, Horizon-, Gate- oder Promotionsentscheidung
  getroffen.

## Handoff

**Änderung:** ausschließlich diese Review-Datei. **Hauptrisiko/offener Punkt:**
F-01 muss in einem separat autorisierten Task behoben werden, bevor die
vollständige Matrix als grün gelten kann. F-02 und F-03 sind zusätzliche
Provenienz-/Dokumentationsverbesserungen; keine Research- oder Safety-Gates
ändern.
