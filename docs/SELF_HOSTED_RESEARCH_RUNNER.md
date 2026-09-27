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

Der aktuelle Architekturzustand ist bewusst konservativ: ein Runner-Prozess, serielle
Continuous-QA und maximal zwei parallele Copilot-CLI-Agenten auf GitHub-hosted Actions.
Die nächste Kapazitätsstufe ist ein zweiter selbstgehosteter Runner-Prozess auf dem bereits
ständig verfügbaren PC; wissenschaftliche Gates und Sicherheitsinvarianten bleiben davon
unabhängig.

## Betriebsregel

Self-hosted Ergebnisse sind Arbeitsmaterial. Für wissenschaftliche Entscheidungen gilt:

`Quelle -> Scope-Gate -> Worker -> Tests -> Provenienz -> kanonische Reproduktion -> Evidence-Gate`

Damit gewinnen wir zusätzliche Rechenkapazität, ohne die Beweis- und Sicherheitskette zu lockern.

## Kapazitätsprinzip

Mehr Compute wird nur für zulässige, reproduzierbare Arbeit verwendet. Eine zusätzliche Runner-Instanz dient der Parallelisierung unabhängiger Jobs; sie lockert keine Research-Gates und macht Self-hosted-Ausgaben nicht zu formaler Evidence.
