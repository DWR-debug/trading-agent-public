# Self-hosted Research Runner — Trading Agent

Stand: 2026-09-26

## Zweck

Der Self-hosted Runner ergänzt die bestehende Research-Architektur als nachgeordneter
Rechen-/QA-Worker. Er entkoppelt deterministische, wiederholbare Arbeit vom Steuer-Agenten
und vom interaktiven Hauptrechner.

Rollen:

\`\`\`
Steuer-/Research-Agent
        |
        +--> Coding Worker -> PR
        |
        +--> GitHub-hosted Actions -> kanonische CI / formale Evidence
        |
        +--> Self-hosted Research Worker -> QA / Reproduktion / vorbereitende Rechenarbeit
\`\`\`

Der Self-hosted Runner entscheidet weder über Hypothesen noch über Promotion und erzeugt
allein keine formale Promotion-Evidence.

## Sicherheitsmodell

Der öffentliche Repository-Kontext verwendet den Runner ausschließlich über den manuellen
Workflow \`.github/workflows/self-hosted-research-worker.yml\`.

Der Workflow akzeptiert nur den Repository-Owner als Actor und nur \`master\` oder
vertrauenswürdige \`research/*\`-Refs. Pull Requests und Fork-Code werden nicht automatisch
auf dem Self-hosted Runner ausgeführt.

Der Worker ist kein beliebiger Shell-Executor. Die Auswahl besteht aus einer festen Lane-
Liste in \`automation/self_hosted_research_worker.py\`.

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

Auf dem Linux-/WSL-Arbeitsrechner im Repository unter
Settings -> Actions -> Runners einen neuen self-hosted runner für dieses Repository
anlegen und als zusätzliches Label exakt \`trading-agent-research\` verwenden.

GitHub zeigt dort die zur Plattform passende Runner-Software und den einmaligen
Registrierungs-Token an. Der Token darf nicht in Git committed oder in Issues/PRs gepostet
werden.

Nach der Registrierung muss der Runner erreichbar sein. Der Workflow startet erst bei
manuellem \`workflow_dispatch\`.

## Betriebsregel

Self-hosted Ergebnisse sind Arbeitsmaterial. Für wissenschaftliche Entscheidungen gilt:

\`Quelle -> Scope-Gate -> Worker -> Tests -> Provenienz -> kanonische Reproduktion -> Evidence-Gate\`

Damit gewinnen wir zusätzliche Rechenkapazität, ohne die Beweis- und Sicherheitskette zu lockern.
