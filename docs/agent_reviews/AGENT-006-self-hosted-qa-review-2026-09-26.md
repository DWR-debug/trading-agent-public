# AGENT-006 – Technische Review des Self-hosted-QA-/Provenance-Systems

**Issue:** #278  
**Taskvertrag:** `TRADING_AGENT_TASK_V1`, `task_id=AGENT-006`  
**Reviewdatum:** 2026-09-27  
**Reviewtyp:** technische, report-only Prüfung; keine Research- oder Performancebewertung  
**Geprüfter Stand:** Arbeitszweig `agent/AGENT-006-copilot-cli`, Commit `4813b4f`  

## Ergebnis

Das System ist grundsätzlich als begrenzte QA-/Reproduktionskette aufgebaut: Es gibt keine
`pull_request`-Ausführung, die Lanes sind statisch vorgegeben, die Ausführung verwendet
einen `GITHUB_SHA`-Snapshot, die Paper-only-Flags werden vor und nach der Lane geprüft, und
`run_manifest.json` sowie `summary.json` werden als nicht-formale Provenienz behandelt.
Die Continuous-QA-Matrix ist mit `fail-fast: false`, `max-parallel: 2`, globaler
Concurrency und einem abschließenden Aggregate-Gate sinnvoll begrenzt.

Die Prüfung findet jedoch drei behebbare technische Risiken und zwei kleinere
Provenienz-/Betriebsgrenzen. Diese Review empfiehlt keine Änderung an Evidence-Gates,
Holdouts, Forschungsparametern, Promotion oder Live-Ausführung.

## Befunde

### F-01 – Mittleres Risiko: Bootstrap- und Python-Abhängigkeiten sind nicht
inhaltlich verifiziert

**Nachweis:** `.github/workflows/self-hosted-research-worker-v4.yml` und
`.github/workflows/self-hosted-continuous-qa.yml` laden Python 3.13.15 als NuGet-Paket
und installieren anschließend `pytest`, `pandas`, `exchange-calendars`, `statsmodels==0.15.0`
und `pypdf`. Für das NuGet-Paket gibt es keine SHA-256-Prüfung oder andere im Workflow
festgelegte Integritätsprüfung; mehrere Python-Abhängigkeiten und ihre transitiven
Abhängigkeiten sind nicht vollständig versioniert.

**Auswirkung:** TLS schützt den Transport, ersetzt aber keine reproduzierbare
Artefaktidentität. Ein verändertes oder anders aufgelöstes Paket kann den QA-Code
technisch verändern. Das schwächt Reproduzierbarkeit und Supply-Chain-Provenienz,
ohne unmittelbar eine Live-Ausführung zu ermöglichen.

**Empfehlung:** Für Python und jede installierte Abhängigkeit einen freigegebenen
Hash-/Lock-Vertrag verwenden oder auf einen versionierten, im Repository bzw. in einem
vertrauenswürdigen Artifact-Pfad reproduzierbar bereitgestellten Dependency-Satz
wechseln. Die Prüfung muss fail-closed erfolgen. Diese Maßnahme darf nur die
technische QA-Provenienz betreffen.

### F-02 – Mittleres Risiko: Das v4-Gateway prüft die Repository-Identität und
`AUTOMATIC_PROMOTION` nicht explizit

**Nachweis:** `self-hosted-research-worker-v4.yml` begrenzt auf Actor `DWR-debug`,
`refs/heads/master` und einen gesetzten `GITHUB_SHA`. Es prüft aber nicht
`GITHUB_REPOSITORY` und validiert in seinem Safety-Schritt nur
`PAPER_ONLY`, `LIVE_TRADING_ENABLED` und `ORDERS_ENABLED`. Die Continuous-QA-Lane
prüft dagegen die Repository-Identität und alle vier Sicherheitsinvarianten.

**Auswirkung:** Für den aktuellen `push`-Trigger ist eine Fork-Ausführung praktisch
ausgeschlossen, und die Actor-/Branch-Prüfung ist eine wirksame zusätzliche Schranke.
Die v4-Prüfung ist aber weniger explizit und weniger konsistent als die Matrix-Lane.
Eine spätere Trigger- oder Workflow-Erweiterung könnte diese Lücke versehentlich
wiederverwenden. `AUTOMATIC_PROMOTION=False` bleibt im Worker-Manifest zwar fest
eingetragen, wird dort aber nicht aus der Konfiguration verifiziert.

**Empfehlung:** Im v4-Gateway zusätzlich `GITHUB_REPOSITORY` exakt auf
`DWR-debug/trading-agent-public` prüfen und vor dem Worker-Aufruf alle vier
Sicherheitsinvarianten aus `config.settings` assertieren. Die bestehende
Owner-/Master-/SHA-Schranke und die fehlende `pull_request`-Triggerklasse müssen
erhalten bleiben.

### F-03 – Niedriges Risiko: Temporäre Daten werden nicht zuverlässig bereinigt

**Nachweis:** Beide Workflows legen Snapshot, Archiv, Python-Runtime,
Dependency-Target und Arbeitsverzeichnisse unter `RUNNER_TEMP` an. Es gibt
keinen abschließenden Cleanup-Schritt mit `if: always()`. Die Pfade werden zwar
vor der jeweiligen Ausführung teilweise überschrieben bzw. gelöscht, bleiben bei
Fehlern aber bis zur Runner-Bereinigung bestehen; in der Continuous-Lane gilt das
insbesondere für run-/attempt-spezifische Pfade.

**Auswirkung:** Fehlerläufe können lokalen Speicher belegen und Artefakte länger als
nötig auf dem Runner hinterlassen. Das ist kein Evidence- oder Live-Trading-Bypass,
aber ein Betriebs- und Datenschutzrisiko, falls sich auf dem Runner künftig
unerwartete temporäre Inhalte ansammeln.

**Empfehlung:** Einen fail-safe Cleanup-Schritt mit `if: always()` ergänzen, der
nur die jeweils eindeutig erzeugten Pfade löscht und den primären Jobstatus nicht
überschreibt. Vorher müssen Provenienzdateien und veröffentlichte Artefakte
gesichert sein. Niemals breit oder mit unaufgelösten Wildcards löschen.

### F-04 – Niedrige Provenienzgrenze: Der v4-Einzelpfad veröffentlicht kein
Workflow-Artefakt

**Nachweis:** `self-hosted-research-worker-v4.yml` schreibt die Ausgabe in den
extrahierten Snapshot unter `research/runs/self_hosted/...`, besitzt aber keinen
`actions/upload-artifact`-Schritt. Die Continuous-QA-Lane veröffentlicht ihre
Provenienz dagegen mit `if: always()` und `if-no-files-found: error`.

**Auswirkung:** Der v4-Lauf kann im Job-Log erfolgreich erscheinen, ohne dass
`summary.json` und `run_manifest.json` nach Ende des Laufs als langlebiger
Workflow-Nachweis verfügbar sind. Damit ist dieser Pfad schwächer reproduzierbar
prüfbar als die Matrix-Lane. Er erzeugt dadurch nicht automatisch formale
Research-Evidence.

**Empfehlung:** Entweder einen eindeutig benannten, bei Erfolg und Fehler
veröffentlichten Provenienz-Artifact für den v4-Pfad ergänzen oder den Pfad
ausdrücklich als rein diagnostisch und nicht archiviert dokumentieren. Bei einer
Veröffentlichung müssen `summary.json` und `run_manifest.json` fail-closed
verlangt werden; der Status `formal_research_evidence: false` bleibt zwingend.

### F-05 – Dokumentations-/Architekturgrenze: Bezeichnung „Self-hosted“ ist
operativ nicht überall eindeutig

**Nachweis:** `docs/SELF_HOSTED_RESEARCH_RUNNER.md` beschreibt einen registrierten
Windows-Runner mit Label `trading-agent-research`, während die geprüften Workflows
`runs-on: windows-latest` verwenden. Die Dokumentation erklärt zwar, dass der
registrierte Runner aktuell nicht als Python-Host verwendet wird, die Namen
„Self-hosted Research Runner“, „hosted Python“ und „self-hosted QA“ bleiben
zwischen Dokumentation und Workflow-Oberfläche leicht verwechselbar.

**Auswirkung:** Betreiber können die tatsächliche Ausführungsumgebung und die
Bedeutung des Runner-Labels falsch einschätzen. Das ist kein unmittelbarer
Sicherheitsfehler; die aktuelle Workflow-Ausführung ist durch `windows-latest`
hosted und die statischen Trigger begrenzt.

**Empfehlung:** Die Dokumentation und Workflow-Namen explizit in „hosted
Python QA gateway for self-hosted research operations“ oder eine gleichwertige,
eindeutige Terminologie angleichen. Falls später wirklich `self-hosted` in
`runs-on` eingesetzt wird, müssen Owner-/Fork-/Secret- und Cleanup-Schranken
erneut separat geprüft werden.

## Geprüfte Kontrollen

| Kontrollziel | Bewertung | Begründung |
|---|---|---|
| Snapshot anhand `GITHUB_SHA` | **Bestanden mit Restgrenze** | Beide Workflows laden den festen Commit über `codeload.github.com/.../%GITHUB_SHA%`; die Continuous-Lane prüft zusätzlich den Manifestwert. Eine lokale Git-Objekt-/Hash-Prüfung des heruntergeladenen Archivs fehlt. |
| Windows-kompatibler Bootstrap | **Bestanden mit F-01** | `cmd`, `curl.exe`, `tar.exe`, NuGet-Python und Windows-Pfade sind konsistent; Dependency-Integrität ist nicht festgeschrieben. |
| Safety-Invarianten | **Bestanden mit F-02** | Continuous-QA prüft alle vier Flags. Das v4-Gateway prüft drei Flags direkt; der Worker schreibt alle vier in die Provenienz. |
| Bounded lanes | **Bestanden** | `argparse` verwendet eine feste Lane-Auswahl; Kommandos sind statisch und werden als Argumentlisten ausgeführt, nicht als freie Shell-Eingabe. |
| `run_manifest.json` | **Bestanden mit F-04** | Lane, Python-Version, SHA, Runnername, Flags, Schrittzahl und Returncodes werden erfasst; bei frühem Abbruch vor dem Worker kann kein Manifest entstehen, was die Workflow-Prüfung korrekt fehlschlagen lässt. |
| Kein formales Evidence-Claiming | **Bestanden** | Worker und Dokumentation markieren `formal_evidence_allowed` bzw. `formal_research_evidence` als `false`; die Self-hosted-Ausgabe wird als Arbeitsprovenienz beschrieben. |
| Secrets | **Bestanden nach statischer Prüfung** | Keine Secrets oder Broker-Zugangsdaten werden verwendet; `permissions: contents: read` ist gesetzt. Dependency-Supply-Chain ist separat F-01. |
| Untrusted Forks | **Bestanden für aktuelle Trigger** | Kein `pull_request`; v4 begrenzt Actor und Branch, Continuous-QA Repository und Branch-Kontext über den Workflow. Eine explizite Repository-Prüfung fehlt nur im v4-Pfad (F-02). |
| Concurrency / Boundedness | **Bestanden** | Globale Gruppe ohne Cancel verhindert überlappende Continuous-Läufe; Matrix `max-parallel: 2`, Job-Timeouts und Aggregate-Gate begrenzen die Ausführung. |
| Cleanup / Fehler | **Teilweise bestanden** | Lane-Abbruch stoppt nach dem ersten Fehler, Returncodes und Provenienz werden geschrieben; Cleanup auf Fehlerpfaden fehlt (F-03), und die v4-Provenienz wird nicht archiviert (F-04). |

## Sicherheits- und Scope-Erklärung

Die Review verändert keine Datei außerhalb dieser Review-Datei. Es wurden keine
P&L-/Performanceberechnungen, Forschungsselektionen, Holdout- oder Gate-Änderungen
vorgenommen. Die unveränderten Sicherheitsinvarianten sind:

```text
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
```

Die Self-hosted-Ausgaben bleiben technische Arbeitsartefakte und sind keine
wissenschaftliche Evidenz. Eine Umsetzung der Empfehlungen benötigt eine separate,
ausdrücklich freigegebene Engineering-Aufgabe und darf weder Research-Governance
noch Promotion- oder Live-Pfade verändern.

## Verifikation

Es wurden die sechs im Issue genannten Review-Dateien sowie die zentrale
Sicherheitskonfiguration und die vorhandenen fokussierten Worker-Tests statisch
geprüft. Da der Vertrag ausdrücklich **report-only** ist und Änderungen
ausschließlich in dieser Review-Datei erlaubt, wurden keine Code- oder
Workflow-Regressionstests hinzugefügt und kein deterministischer Research-Lauf
ausgeführt.
