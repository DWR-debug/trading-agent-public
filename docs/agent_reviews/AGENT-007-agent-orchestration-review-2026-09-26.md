# Technische Review: Agent-Orchestrierung und Actions-Routing

**Task:** AGENT-007 / Issue #279  
**Prüfdatum:** 2026-09-27  
**Prüfmodus:** report-only; keine Workflow-, Research- oder Evidence-Änderung

## 1. Gegenstand und Ergebnis

Geprüft wurden:

- `AGENTS.md`
- `docs/TRADING_AGENT_CHAT_ENTRYPOINT.md`
- `docs/DEVELOPMENT_ORCHESTRATION.md`
- `docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md`
- `automation/agent_dispatch.py`
- `.github/workflows/copilot-cli-engineering-task.yml`
- `.github/workflows/ci.yml`

Die Rollen- und Sicherheitsabsicht ist insgesamt klar: Der Steuer-/Research-Agent
entscheidet, nachgeordnete Worker führen begrenzte Engineering-Aufgaben aus, und
Research-Gates, Holdouts, Promotion sowie Live-Ausführung bleiben außerhalb der
Worker-Zuständigkeit. Die Verträge enthalten mehrere fail-closed Prüfungen und die
vier Sicherheitsinvarianten sind in den geprüften Quellen konsistent.

**Technisches Gesamturteil: bedingt belastbar.** Die Schutzrichtung ist richtig,
aber einige Kontrollen sind nur workflow-lokal oder prüfen nicht den vollständigen
Git-Zustand. Dadurch können Parallelitäts-, Scope-, Credential- und Handoff-
Annahmen auseinanderlaufen. Diese Punkte sollten vor einer Ausweitung der
Automatisierung behoben werden; sie begründen keine Research- oder
Promotionsentscheidung.

## 2. Positiv verifizierte Kontrollen

### Rollen und Hierarchie

`TRADING_AGENT_CHAT_ENTRYPOINT.md`, `DEVELOPMENT_ORCHESTRATION.md` und
`AGENTS.md` trennen Steuer-/Research-Agent, Coding-Agent, Self-hosted Worker und
deterministische Actions nachvollziehbar. Besonders wichtig ist die explizite
Aussage, dass Agentenoutput keine Evidenz ist und nachgeordnete Agenten keine
Entscheidungshoheit über Gates oder Promotion besitzen.

### Fail-closed Task-Vertrag

`automation/agent_dispatch.py` verlangt Schema-Version, `AGENT-*`-Task-ID,
`engineering`/`trading-agent-engineer`, `master` als Basis, eine nichtleere
Scope-Angabe, zulässige Sessiondauer und explizit falsche Research-/Live-Flags.
Ungültige SHA-Formate, fehlende Labels, bereits zugewiesene Copilot-Issues und
eine belegte Parallelitätsgrenze werden abgelehnt. Die Manifest-Fingerprint-
Bildung ist deterministisch.

### Allowed paths und geschützte Pfade

Relative Pfade, `..`, absolute Pfade und geschützte Präfixe werden im Python-
Vertrag abgelehnt. Die CLI-Workflow-Prüfung wiederholt die Pfadvalidierung und
den finalen Scope-Check; `.github/`, `research/evidence/`,
`research/authorizations/` und `gates/` sind ausdrücklich geschützt. Diese
Doppelung ist momentan eine Schutzschicht, erzeugt aber auch ein
Drift-Risiko (siehe Befund R-04).

### CI und Ressourcenrouting

`ci.yml` besitzt nur `contents: read`, nutzt reproduzierbare Standardrunner,
führt Tests und Integritäts-/Freshness-/Governance-Prüfungen aus und lässt die
Matrix mit `fail-fast: false` vollständig laufen. Der Self-hosted-Pfad ist auf
owner-gesteuerte, benannte Refs und das Label `trading-agent-research`
beschränkt; die dokumentierte Trennung von QA/Research-Vorbereitung und
kanonischer Evidence ist sachgerecht. Paid usage und Live-Risiken werden in den
Dokumenten sowie den Laufzeitprüfungen ausgeschlossen.

## 3. Konkrete technische Befunde

### R-01 — Hohe Priorität: Die maximale Parallelität 2 ist nicht systemweit beweisbar

`agent_dispatch.py` begrenzt den vom Dispatch-Workflow übermittelten
`active_agent_count` auf zwei. Der CLI-Workflow verwendet zusätzlich zwei
Concurrency-Gruppen anhand von `issue.number % 2`. Diese Gruppen serialisieren
jeweils Issues derselben Parität und erlauben damit höchstens zwei CLI-Läufe.
Der Count im Dispatch-Workflow zählt jedoch offene Issues mit
`copilot-swe-agent[bot]`; er ist kein gemeinsamer Lease-/Run-Zähler und erfasst
nicht zuverlässig laufende CLI-Sessions, stale Assignments oder parallele
Workflowpfade. Cloud-Agent-Dispatch, CLI-Workflow und Queue-Lane können daher
unterschiedliche Vorstellungen von den „aktiven zwei“ haben.

**Risiko:** Eine projektweite Obergrenze kann bei konkurrierenden Events,
unterschiedlichen Dispatchpfaden oder stale Zuständen überschritten werden,
während ein legitimer Auftrag unnötig blockiert wird.

**Robuste Verbesserung:** Einen einzigen atomaren, kurzlebigen Dispatch-Lease
mit genau zwei benannten Slots als autoritative Quelle verwenden. Slot-Erwerb,
Heartbeat/TTL, Freigabe und stale-Lease-Recovery müssen für Cloud-Agent,
CLI-Queue und manuelle Dispatches denselben Pfad nutzen. Die Concurrency-
Gruppen bleiben als zweite Ausführungssperre sinnvoll, dürfen aber nicht als
Kapazitätszähler dienen. Lease-Daten müssen Task-ID, Issue, Manifest-Fingerprint
und Run-ID binden.

### R-02 — Hohe Priorität: Der Scope-Gate prüft nicht den vollständigen Git-Zustand

Der Schritt „Enforce task-scoped file scope“ bildet die Änderungen aus
`git diff --name-only`. Das erfasst typischerweise weder staged Änderungen
(`git diff --cached`) noch untracked Dateien. Der nachfolgende Commit verwendet
aber `git add -A`. Ein staged oder untracked außerhalb von `allowed_paths`
liegender Pfad kann deshalb den Gate passieren und anschließend veröffentlicht
werden.

**Risiko:** Der wichtigste Dateigrenzen-Mechanismus ist in einem für Agenten
relevanten Randfall fail-open; insbesondere können versehentlich erzeugte
Artefakte, Konfigurationsdateien oder Secrets in den Branch gelangen.

**Robuste Verbesserung:** Den Scope ausschließlich aus
`git diff --name-status --cached`, `git diff --name-status` und
`git ls-files --others --exclude-standard` bilden, Pfade deduplizieren und
vor jedem `git add` gegen dieselbe normalisierte Allowlist prüfen. Zusätzlich
den finalen Index nach `git add -A` erneut prüfen und bei jedem Verstoß hart
abbrechen. Die Allowlist-Prüfung sollte eine einzige versionierte
Implementierung nutzen, statt in Python und YAML separat nachgebildet zu
werden.

### R-03 — Hohe Priorität: Token- und Shell-Grenzen sind breiter als der
Arbeitsvertrag

Der CLI-Job fordert `contents: write`, `issues: write` und
`pull-requests: write`. Während der Agentensitzung ist außerdem
`COPILOT_GITHUB_TOKEN` gesetzt; die Tool-Freigabe enthält
`shell(git:*)`. Der Prompt untersagt Push zwar, die technische Freigabe
erzwingt das nicht. Der Token-Format-Check unterscheidet Präfixe, validiert
aber weder konkrete Scopes noch Repository-/Ablaufbindung. Damit hängt die
Sicherheit wesentlich von Agentengehorsam und der Konfiguration eines
personenbezogenen Tokens ab.

**Risiko:** Ein Prompt-/Tool-Fehler könnte vor dem Scope-Gate Pushes,
Issue-/PR-Mutationen oder Credential-Abfluss ermöglichen. Das ist besonders
problematisch, weil der Job auf `master` auscheckt und Schreibrechte besitzt.

**Robuste Verbesserung:** Agentensitzung und Publikationsphase strikt trennen:
kein Schreib-`GITHUB_TOKEN` und kein personenbezogenes Token im Agentenprozess,
`git`-Tool-Allowlist ohne Push/Remote-Konfigurationsänderung und nur minimal
erforderliche Read-Rechte. Commit, Push und Issue-/PR-Kommentare sollen in
einem separaten, nachgelagerten Job mit expliziten Outputs und erneutem
Scope-/Safety-Gate erfolgen. Falls ein User-Token für die Copilot-API
unvermeidbar ist, muss sein erforderlicher Scope, Repository-Bindung und
Rotation/TTL außerhalb des Prompts technisch dokumentiert und geprüft werden.

### R-04 — Mittlere Priorität: Doppelte Vertragslogik kann auseinanderdriften

`automation/agent_dispatch.py` und der „Resolve task contract“-Schritt im
CLI-Workflow implementieren jeweils Schema-, Flag-, Path- und Wildcard-
Validierung. Zusätzlich gibt es einen weiteren finalen Scope-Checker.
Der Python-Dispatcher lehnt bereits zugewiesene Copilot-Issues ab; der CLI-
Workflow verlässt sich für die Ausführung auf Label-/Owner-Prüfung und eine
Branch-Existenzprüfung. Die Regeln sind damit nicht aus einer einzigen
Vertragsimplementierung abgeleitet.

**Risiko:** Eine spätere Korrektur kann nur eine Schicht erreichen. Dann werden
Manifest, tatsächliche Agentenausführung und Publikationsgate unterschiedlich
bewertet; Auditierbarkeit und Fail-Closed-Verhalten werden unklar.

**Robuste Verbesserung:** Den Python-Validator als einzige normative
Implementierung verwenden. Der Workflow soll nur JSON laden, den Validator
aufrufen und dessen normalisiertes Manifest/Fingerprint weiterreichen.
Vertrags- und Scope-Tests müssen alle drei Phasen (Resolve, Agentenlauf,
Publikation) mit denselben adversarialen Fällen prüfen.

### R-05 — Mittlere Priorität: Duplicate-Dispatch-Schutz ist nicht vollständig

Der Dispatcher blockiert eine bestehende Copilot-Zuweisung. Der CLI-Workflow
blockiert eine bereits existierende Branch mit dem Task-ID-Namen, aber nur nach
Checkout und ohne atomare Reservierung. Der globale Dispatch-Concurrency-
Lock schützt den Cloud-Agent-Dispatch, nicht notwendigerweise ein bereits
laufendes CLI-Ereignis. Außerdem wird die Eindeutigkeit der `task_id` nicht
gegen bereits laufende oder veröffentlichte Manifeste geprüft.

**Risiko:** Wiederholte Labels, manuelle Wiederholung und zwei Issues mit
derselben Task-ID können zu konkurrierenden oder schwer zuzuordnenden Branches,
Kommentaren und Artefakten führen. Die Branch-Prüfung ist bei getrennten
Runners kein allgemeiner Idempotenzschlüssel.

**Robuste Verbesserung:** Vor Ausführung eine atomare Task-ID-/Manifest-
Reservierung anlegen (z. B. ein unveränderliches Queue-Manifest oder
GitHub-Concurrency-Key aus Task-ID plus Fingerprint). Wiederholung desselben
Fingerprints soll idempotent als „already dispatched“ enden; abweichender
Fingerprint unter derselben Task-ID muss fail-closed eskalieren. Branch- und
PR-Zustand sind danach nur noch abgeleitete Prüfungen.

### R-06 — Mittlere Priorität: Der PR-Erzeugungs-Fallback ist kein
vollständiger Handoff

Der Publikationsschritt versucht `gh pr create` und kommentiert bei einem
Fehler lediglich, dass der Orchestrator den PR aus dem Branch erstellen müsse.
Das bewahrt zwar den Branch, garantiert aber keinen PR-Handoff, keine
strukturierte Fehlerklassifikation und keine erneute Review-/CI-Verknüpfung.
Der Workflow besitzt zudem weitreichende `pull-requests: write`-Rechte,
obwohl die Erstellung bei Repository-Policies oder Token-Einschränkungen
scheitern kann. Ein Branch kann dadurch erfolgreich publiziert erscheinen,
obwohl die erwartete Reviewkette nicht zustande kommt.

**Risiko:** Arbeit bleibt verwaist oder wird als abgeschlossen interpretiert,
obwohl kein PR und damit kein normaler Review-Gate existiert. Der Rückfall
ist beobachtbar, aber nicht automatisch nachverfolgbar.

**Robuste Verbesserung:** Den Fallback als maschinenlesbaren, fehlgeschlagenen
Handoff markieren: Task-/Manifest-Fingerprint, Branch, Commit-SHA und exakte
Fehlerklasse als Issue-Kommentar und Artifact ausgeben; den Job trotz Branch-
Erhalt nicht erfolgreich abschließen. Ein separater, owner-gesteuerter
Handoff-Job oder eine klar begrenzte Folgeaktion darf den PR erzeugen und muss
danach CI/Review abwarten. Keine automatische Merge- oder Promotionaktion
daran koppeln.

### R-07 — Mittlere Priorität: Eskalation bei CLI-Fehlern ist schwächer als beim
Dispatcher

`agent-dispatch.yml` kommentiert bei Fehlern explizit, dass kein Research-
Ergebnis oder Agent-Usage-Eintrag abgeleitet werden darf. Der CLI-Workflow
besitzt dagegen keinen gleichwertigen `if: failure()`-Eskalationsschritt für
Agentenabbruch, Scope-Verstoß oder Regression-Gate. Ein Branch-Existenzfall
kommentiert und beendet den Job erfolgreich; ein fehlgeschlagener PR-Versuch
wird als Fallback behandelt, ohne zwingende Eskalationsmetadaten.

**Risiko:** Operatoren müssen Workflow-Logs durchsuchen, und externe Queue-
Überwachung kann zwischen „nicht gestartet“, „abgebrochen“, „Scope verletzt“
und „Branch ohne PR“ nicht zuverlässig unterscheiden.

**Robuste Verbesserung:** Für jede terminale Klasse einen strukturierten Status
(`DISPATCHED`, `RUNNING`, `SCOPE_REJECTED`, `TEST_FAILED`,
`PUBLISHED_NO_PR`, `COMPLETED`) mit Task-ID/Fingerprint/Run-ID schreiben und
bei `failure()` einen deduplizierten Issue-Kommentar erzeugen. Ein
Statuswechsel darf keine wissenschaftliche Evidence oder Research-Autorisierung
erzeugen.

### R-08 — Niedrige Priorität: Master-Provenienz und Action-Abhängigkeiten
brauchen stärkere Bindung

`automation/agent_dispatch.py` nimmt `GITHUB_SHA` als `current_master_sha`
entgegen. Bei `workflow_dispatch` ist nicht allein aus dem Argument ersichtlich,
dass dieser SHA tatsächlich der aktuelle `master`-Tip ist; der Workflow
validiert die Beziehung nicht ausdrücklich. Die CLI-Ausführung checkt `master`
aus, bindet aber den erzeugten Branch nicht an einen im Manifest gespeicherten
Commitvergleich. Zudem installiert der CLI-Job Testabhängigkeiten teilweise
unpinnt, während CI und Agenten unterschiedliche Testausschnitte ausführen.

**Risiko:** Ein formal gültiges Manifest kann auf einer anderen Ref-Basis
entstehen, und eine Agentensitzung kann trotz grüner Teiltests von einer
abweichenden Dependency-/Commitgrundlage ausgehen.

**Robuste Verbesserung:** Vor Manifest-Erzeugung den SHA von `refs/heads/master`
serverseitig auflösen und exakt als Source-SHA verwenden; vor Branch-Erzeugung
erneut vergleichen oder bei Drift abbrechen. Dependency-Versionen und der
kleinste zulässige Regressionstest sollten als versionierter, gemeinsamer
Vertrag referenziert werden. Diese Verbesserung betrifft Reproduzierbarkeit,
nicht Forschungslogik.

## 4. Bewertung der angeforderten Prüfpunkte

| Prüfpunk | Bewertung |
|---|---|
| Rollen-/Hierarchieklarheit | Dokumentarisch klar; technische Statusrückgabe zwischen Cloud-Agent und CLI noch uneinheitlich (R-07). |
| Fail-closed Task-Verträge | Stark im Python-Validator; parallele YAML-Nachbildung und unterschiedliche Einstiegspfade schwächen Einheitlichkeit (R-04). |
| `allowed_paths` | Relative-/Protected-Path-Regeln vorhanden; vollständiger Git-Zustand nicht erfasst (R-02). |
| Geschützte Pfade | In Validator und Workflow vorhanden; Drift- und staged/untracked-Risiko bleibt (R-02, R-04). |
| Maximale Parallelität 2 | CLI-Parität ergibt zwei Lanes; kein gemeinsamer projektweiter Lease über alle Agentenpfade (R-01). |
| Duplicate-Dispatch-Schutz | Assignment- und Branch-Prüfung vorhanden; nicht atomar und nicht task-ID-global (R-05). |
| Token-/Permission-Grenzen | CI read-only und Owner-Gates sind gut; CLI-Agentenprozess erhält zu breite Schreib-/Shell-Nähe (R-03). |
| PR-Erzeugungslücke | Fallback benennt die Lücke, schließt sie aber nicht mit einem verfolgbaren Handoff-Gate (R-06). |
| Eskalationsverhalten | Dispatcher explizit; CLI-Fehlerklassen und Statusübergänge nicht gleichwertig (R-07). |
| Ressourcenrouting | Kostenfreie Standardrunner, Self-hosted-Sicherheitsgrenze und keine Paid-Nutzung sind klar; Kapazitätszählung bleibt routinglokal (R-01). |

## 5. Empfohlene Reihenfolge für technische Härtung

1. Vollständigen staged/unstaged/untracked Scope-Check vor und nach dem
   Commit herstellen (R-02).
2. Einen gemeinsamen, atomaren Zwei-Slot-Lease und idempotente Task-ID-
   Reservierung für alle Agentenpfade einführen (R-01, R-05).
3. Agentenprozess von Publikationsrechten und personenbezogenen Tokens trennen
   und die minimale Tool-Allowlist erzwingen (R-03).
4. Validator-/Scope-Logik zentralisieren und strukturierte Terminalstatus/
   Eskalation einschließlich `PUBLISHED_NO_PR` ergänzen (R-04, R-06, R-07).
5. Master-SHA und Dependency-/Testgrundlage explizit pinnen und vor Ausführung
   erneut verifizieren (R-08).

Diese Empfehlungen verändern weder Research-Entscheidungen noch
Evidence-Gates, Holdout-Logik, Strategieparameter, Asset-Universen,
Promotionregeln oder Live-Ausführung.

## 6. Sicherheits- und Ressourcenabschluss

Die Review hat keine Änderung an Sicherheitsinvarianten vorgenommen. Der
geprüfte Zielzustand bleibt:

```text
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
```

Es wurden keine deterministischen Research-Berechnungen, keine wissenschaftliche
Selektion und keine Änderungen an historischen Evidence-/Autorisierungsdaten
durchgeführt. Die Review selbst ist ausschließlich technischem Handoff- und
Risikomaterial zuzuordnen.
