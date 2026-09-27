# Self-hosted Research Runner — Trading Agent

Stand: 2026-09-27

## Zweck

Der Self-hosted Runner ergänzt die bestehende Research-Architektur als nachgeordneter
Rechen-/QA-Worker. Er entkoppelt deterministische, wiederholbare Arbeit vom Steuer-Agenten
und vom interaktiven Hauptrechner.

Rollen:

```
Steuer-/Research-Agent
        |
        +--> Coding Worker -> PR
        |
        +--> GitHub-hosted Actions -> kanonische CI / formale Evidence
        |
        +--> Self-hosted Research Worker -> QA / Reproduktion / vorbereitende Rechenarbeit
```

Der Self-hosted Runner entscheidet weder über Hypothesen noch über Promotion und erzeugt
allein keine formale Promotion-Evidence.

## Sicherheitsmodell

Der öffentliche Repository-Kontext verwendet den Runner über den neuen
`Self-hosted Research Worker v4`. Der Workflow nutzt den nachweislich funktionierenden
`push`-Mechanismus auf `master`, ist aber zusätzlich durch einen eindeutigen Commit-Marker
`RUN_SELF_HOSTED_REPO_QA:` gegen unbeabsichtigte Ausführung geschützt.

Der Workflow akzeptiert nur den Repository-Owner als Actor. Der Worker ist kein beliebiger
Shell-Executor und führt ausschließlich die fest definierte `repo_qa`-Lane aus.

Keine Trading-Secrets, API-Schlüssel oder produktiven Zugangsdaten auf dem Runner hinterlegen.

## Ressourcennutzung

Geeignete Aufgaben:

- Regressionstests;
- Daten-/Snapshot-QA;
- lokale Reproduktion technischer Probleme;
- vorbereitende diagnostische Berechnungen;
- große, nicht kanonische Forschungsbatches, deren Ergebnis anschließend auf einem
  kanonischen Runner reproduziert werden soll.

Nicht auf den Self-hosted Runner verlagern:

- Live-Ausführung;
- automatische Promotion;
- unkontrollierte PR-Ausführung;
- finale Evidence-Läufe ohne reproduzierbaren kanonischen Gegenlauf;
- beliebige Shell-Kommandos aus Issue-/PR-Inhalten.

## Einmalige Einrichtung des PCs

Der registrierte Runner muss das Label `trading-agent-research` tragen und erreichbar sein.
Auf dem Firmenrechner ist keine systemweite Python-Installation erforderlich: Der Workflow
bootstrappt eine fest gepinnte Python-3.13.15-NuGet-Laufzeit temporär. Damit sind weder
Administratorrechte noch `actions/setup-python` erforderlich.

Die autonome Continuous-QA-Lane läuft jetzt alle 15 Minuten. Jeder Lauf erfasst zusätzlich
Runnername, Betriebssystem, Architektur, logische Prozessoren und Arbeitsspeicher als
nicht-kanonische Kapazitätstelemetrie. So kann die tatsächliche Auslastung des PCs über die
Zeit beurteilt werden, statt nur nach dem Vorhandensein eines erfolgreichen Jobs zu gehen.

Ein einzelner QA-Lauf wird durch eine Änderung an der dedizierten Trigger-Datei
`research/run_requests/self_hosted_repo_qa.trigger` auf `master` ausgelöst. Der Runner prüft
zusätzlich den Repository-Owner und führt dann genau die freigegebene `repo_qa`-Lane aus.

## Laufmanifest

Jede begrenzte Lane schreibt neben `summary.json` ein `run_manifest.json` mit Lane,
Python-Executable und -Version, Quell-Commit (`GITHUB_SHA`, sofern gesetzt), Runnername
(`RUNNER_NAME`, sofern gesetzt), den Paper-only-Sicherheitsflags sowie Schrittanzahl und
Schritt-Rückgabecodes. Bei lokalen Läufen ohne GitHub-Metadaten sind Commit und Runnername
`null`. Das Manifest kennzeichnet ausdrücklich, dass es keine formale Research-Evidence ist.

Das Manifest ist nicht-kanonische Arbeitsprovenienz und allein kein Research-Befund. Vor
jeder wissenschaftlichen Verwendung müssen Quelle und Laufumfang geprüft sowie Ergebnisse
auf dem kanonischen Pfad reproduziert werden; unveränderte Evidence-Gates bleiben maßgeblich.

## Runner-Pool und Parallelisierung

Alle Self-hosted Research-Jobs verwenden bewusst das gemeinsame Label
`[self-hosted, trading-agent-research]`. Ein zweiter Runner-Prozess auf demselben PC kann
daher mit genau demselben Label registriert werden und übernimmt automatisch Jobs, sobald
der erste Prozess belegt ist. Die Workflow-Dateien benötigen dafür keine Änderung. Das
ist die bevorzugte Skalierung, bevor wir zusätzliche Maschinen oder kostenpflichtige
Compute-Ressourcen einsetzen.

Der aktuelle Workflow verwendet einen Runner-Prozess und führt Continuous QA seriell aus.
Eine spätere Workflow-Änderung kann die vier QA-Lanes unabhängig dispatchen und mit
`max-parallel: 2` begrenzen. Das setzt keine zweite Runner-Instanz voraus: Mit nur einem
registrierten Runner können passende Jobs weiterhin nacheinander laufen. Ein zweiter
Prozess mit demselben Label kann die tatsächlich verfügbare Parallelität erhöhen, ist aber
keine Voraussetzung für Korrektheit.

## Vertrag für parallele Continuous-QA-Lanes

Die Umstellung erfolgt separat in der Workflow-Datei; dieser Abschnitt beschreibt den
Zielvertrag und behauptet nicht, dass der aktuelle serielle Workflow ihn bereits
implementiert. Die vier erlaubten Lane-Namen bleiben exakt `repo_qa`, `data_qa`,
`design_qa` und `local_reproduction`; die Worker-CLI akzeptiert keine beliebigen Kommandos.

Der spätere Workflow sollte einen statischen Matrix-Eintrag pro Lane mit
`strategy.max-parallel: 2` verwenden und `strategy.fail-fast: false` setzen. Damit bleiben
die vier Lanes unabhängig dispatchbar, eine fehlgeschlagene Lane beendet nicht vorzeitig
die anderen erwarteten Prüfungen, und höchstens zwei Lane-Jobs werden gleichzeitig an den
Runner-Pool gegeben. Jeder Job muss trotzdem fail-closed enden: fehlgeschlagene Schritte,
fehlende Metadaten oder fehlende Provenienz dürfen nicht in einen erfolgreichen Lane-Status
umgewandelt werden.

Jede Lane benötigt einen isolierten Arbeits-/Ausgabepfad, der mindestens Lane,
`GITHUB_RUN_ID` und `GITHUB_RUN_ATTEMPT` unterscheidet. Der Job ruft ausschließlich die
feste Worker-Lane auf, prüft deren Exit-Code und lädt `summary.json` sowie
`run_manifest.json` auch bei Fehlern mit `if: always()` hoch; fehlende Dateien sind ein
Fehler (`if-no-files-found: error`). Artifact-Namen müssen ebenfalls Lane, Run-ID und
Attempt enthalten. Summary und Manifest müssen die konkrete Lane und den unveränderten
`GITHUB_SHA` erkennen lassen; das Manifest muss die unveränderten Paper-only-Sicherheitsflags
sowie `formal_research_evidence: false` ausweisen.

Ein abschließender Aggregate-Gate-Job muss mit `if: always()` laufen und von der Matrix
abhängen. Er darf nicht bloß die vorhandenen Artifacts als hinreichenden Erfolg behandeln:
Er verlangt exakt die vier erwarteten Lane-Identitäten, prüft für jede Lane Summary und
Manifest samt Lane-/SHA-Zuordnung und schlägt fehl, wenn eine Lane fehlgeschlagen,
abgebrochen, übersprungen oder nicht nachgewiesen wurde. So kann ein fehlendes
Matrix-Ergebnis nicht als Erfolg durchrutschen.

Bei der Workflow-Umsetzung unverändert erhalten: globale `concurrency`-Gruppe und
`cancel-in-progress: false`, `workflow_dispatch`, der 15-Minuten-Schedule, Ausführung
ausschließlich aus dem vertrauenswürdigen Repository-Kontext, Download des exakten
`GITHUB_SHA`-Snapshots und die isolierte Python-3.13.15-NuGet-Bootstrap-Logik. Keine Lane
darf untrusted Fork-Code ausführen oder in Research-Evidence schreiben. Die Workflow-Datei
wird erst in einem getrennten Orchestrator-Schritt geändert und geprüft; die
Worker-Regressionstests sichern bis dahin Lane-Isolation, fail-closed Rückgabecodes und
eindeutige Lane-Provenienz ab.

## Betriebsregel

Self-hosted Ergebnisse sind Arbeitsmaterial. Für wissenschaftliche Entscheidungen gilt:

`Quelle -> Scope-Gate -> Worker -> Tests -> Provenienz -> kanonische Reproduktion -> Evidence-Gate`

Damit gewinnen wir zusätzliche Rechenkapazität, ohne die Beweis- und Sicherheitskette zu lockern.

## Kapazitätsprinzip

Mehr Compute wird nur für zulässige, reproduzierbare Arbeit verwendet. Eine zusätzliche Runner-Instanz dient der Parallelisierung unabhängiger Jobs; sie lockert keine Research-Gates und macht Self-hosted-Ausgaben nicht zu formaler Evidence.
