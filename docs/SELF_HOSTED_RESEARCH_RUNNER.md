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

Der registrierte Windows-Runner ist ein echter Self-hosted-Ausführungspfad für owner-gesteuerte Projektläufe. Für Q067 wird er als kanonischer Forschungsrunner verwendet, wenn GitHub-hosted Actions von der dokumentierten Zero-Job-Anomalie betroffen sind. Der Workflow nutzt den nachweislich funktionierenden
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

Die autonome Continuous-QA-Lane läuft jetzt stündlich auf dem registrierten Self-hosted-Runner. Jeder Lauf erfasst zusätzlich
Runnername, Betriebssystem, Architektur, logische Prozessoren und physischen Arbeitsspeicher (in Bytes) als
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
`null`. Das Manifest kennzeichnet den Ausführungspfad und die Provenienz. Für normale QA bleibt es Arbeitsprovenienz; Q067 darf auf dem vertrauenswürdigen Owner-Runner formal ausgeführt werden, weil Snapshot, Commit, Safety, Preregistration und Evidence-Gates im Repository weiterhin unverändert und maschinengeprüft sind.

## Runner-Pool und Parallelisierung

Alle Self-hosted Research-Jobs verwenden bewusst das gemeinsame Label
`[self-hosted, trading-agent-research]`. Die Continuous QA ist in vier statische
Matrix-Lanes aufgeteilt: `repo_qa`, `data_qa`, `design_qa` und `local_reproduction`.
`strategy.max-parallel: 2` begrenzt die gleichzeitig gestarteten Lane-Jobs; mit einem
registrierten Runner werden sie entsprechend der verfügbaren Kapazität nacheinander
ausgeführt, mit zwei identisch gelabelten Runner-Prozessen können bis zu zwei Lanes
gleichzeitig laufen. `fail-fast: false` stellt sicher, dass der Ausfall einer Lane die
anderen erwarteten Prüfungen nicht vorzeitig abbricht.

Jede Lane arbeitet mit demselben unveränderten `GITHUB_SHA`-Snapshot, einer isolierten
temporären Python-3.13.15-NuGet-Laufzeit und einem lane-/run-/attempt-spezifischen
Arbeits- und Provenienzpfad. Die Ausgabedateien `summary.json` und `run_manifest.json`
enthalten die Lane, den Quell-Commit und die unveränderten Paper-only-Sicherheitsflags;
`formal_research_evidence: false` bleibt für QA zwingend; Q067 nutzt einen separaten formalen Research-Workflow mit eigener Provenienz. Artifact-Namen enthalten Lane,
Run-ID und Attempt und werden auch bei Fehlern mit `if: always()` veröffentlicht;
fehlende Provenienzdateien sind ein harter Fehler.

Nach den vier Matrix-Lanes läuft ein separater Aggregate-Gate-Job mit `if: always()`.
Er ist von der Matrix abhängig und verlangt, dass der gesamte statische Vier-Lane-Satz als
erfolgreich abgeschlossen gilt. Ein übersprungener, fehlgeschlagener oder fehlender Lane-Job
führt damit zu einem fehlgeschlagenen Gesamtstatus.

Die globale Concurrency-Gruppe `trading-agent-self-hosted-continuous-qa` nutzt
`cancel-in-progress: true`. Die Continuous QA ist auf eine essentielle `repo_qa`-Heartbeat-Lane
reduziert und läuft planmäßig alle sechs Stunden; die permanente Frontier-Forschung bleibt
der primäre Self-hosted-Arbeitspfad. Ausgeführt wird ausschließlich der vertrauenswürdige öffentliche
Repository-Kontext; untrusted Fork-Code wird nicht ausgeführt. Der Self-hosted Runner
schreibt weiterhin keine Research-Evidence und besitzt keine Live-/Broker-Funktion.

## Betriebsregel

Self-hosted Ergebnisse sind Arbeitsmaterial. Für wissenschaftliche Entscheidungen gilt:

`Quelle -> Scope-Gate -> Worker -> Tests -> Provenienz -> kanonische Reproduktion -> Evidence-Gate`

Damit gewinnen wir zusätzliche Rechenkapazität, ohne die Beweis- und Sicherheitskette zu lockern.

## Kapazitätsprinzip

Mehr Compute wird nur für zulässige, reproduzierbare Arbeit verwendet. Eine zusätzliche Runner-Instanz dient der Parallelisierung unabhängiger Jobs; sie lockert keine Research-Gates und macht Self-hosted-Ausgaben nicht zu formaler Evidence.


## Wiederherstellung des vorhandenen Windows-Runners

Der bereits eingerichtete Runner unter `C:\Users\u419680\actions-runner` muss nicht neu registriert werden, solange seine bestehende GitHub-Runner-Konfiguration noch vorhanden ist.

Minimaler Wiederanlauf auf dem bekannten Rechner:

```powershell
Set-Location C:\Users\u419680\actions-runner
$svc = Get-Service | Where-Object { $_.Name -like "actions.runner*" }
if ($svc) {
  $svc | ForEach-Object {
    if ($_.Status -ne "Running") { try { Start-Service -Name $_.Name -ErrorAction Stop } catch {} }
  }
}
if (-not (Get-Process Runner.Listener -ErrorAction SilentlyContinue)) {
  .\run.cmd
}
```

Die frühere Prüfung zeigte genau diesen Pfad; bei der letzten Kontrolle war `Runner.Listener` nicht aktiv. Deshalb ist ein erneuter Download oder eine neue Runner-Registrierung nicht der erste Schritt.

Nach dem Start sollte der Prozess `Runner.Listener` sichtbar sein. Die Repo-Seite wartet bereits mit dem Label `trading-agent-research` auf den Runner; Q067 Coverage/PIT und der Runner-Probe sind entsprechend konfiguriert.

Falls `run.cmd` wegen Firmenrichtlinien nicht dauerhaft laufen darf, ist die alternative Wiederherstellung der bereits installierten Windows-Service-Variante über `svc.cmd start`. Eine neue Runner-Registrierung ist nur erforderlich, wenn die lokale Konfiguration verloren gegangen oder ungültig ist.
