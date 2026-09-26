# Self-hosted Research Runner — Trading Agent

Stand: 2026-09-26

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
`Self-hosted Research Worker v3`. Der Workflow nutzt den nachweislich funktionierenden
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

Ein einzelner QA-Lauf wird durch einen Commit auf `master` mit dem Commit-Marker
`RUN_SELF_HOSTED_REPO_QA:` ausgelöst. Der Runner führt dann genau die freigegebene
`repo_qa`-Lane aus.

## Betriebsregel

Self-hosted Ergebnisse sind Arbeitsmaterial. Für wissenschaftliche Entscheidungen gilt:

`Quelle -> Scope-Gate -> Worker -> Tests -> Provenienz -> kanonische Reproduktion -> Evidence-Gate`

Damit gewinnen wir zusätzliche Rechenkapazität, ohne die Beweis- und Sicherheitskette zu lockern.
