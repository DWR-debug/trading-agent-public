# AGENT-017 — Review des Autonomous Resource Control Plane

**Umfang:** Report-only-Prüfung von `automation/autonomous_control_plane.py`,
`tests/test_autonomous_control_plane.py`, den Workflows
`autonomous-control-plane.yml` und `agent-request-queue.yml` sowie
`docs/AUTONOMOUS_RESOURCE_CONTROL_PLANE.md`.

**Geprüfter Stand:** `HEAD 88b0a587b8a2ae08cffb9cc661955cb21d38dbe4`
auf `agent/AGENT-017-copilot-cli`. Die kanonischen Betriebsdateien weisen
`master` als `e5e06810b60b149a4faeafb17ceda717c69c3084` aus.
Die GitHub-Live-Abfrage war aus dieser Umgebung nicht zugänglich; Aussagen zu
laufenden Runs und Runner-Kapazität sind daher nicht verifiziert.

## Findings

### Hoch — Doppelter `task_id` kann beide CLI-Lanes belegen

In `plan()` werden `indexed` und `active` vor der Issue-Schleife erstellt, aber
bei neu erzeugten Assignments nicht aktualisiert. Zwei offene, gültig
beschriftete Issues mit demselben `task_id` bestehen daher beide die Guards und
werden auf lane0 und lane1 geroutet. Die Contract-Prüfung validiert beide
Assignments separat und erkennt nicht, dass sie dieselbe Task-ID verwenden.
Beide Worker können somit parallel denselben Branch-/Task-Schlüssel ausführen.
Das verletzt den Duplicate-Guard und die Eindeutigkeit der Queue-Zuordnung.

**Betroffene Stellen:** `automation.autonomous_control_plane.plan()`; die
Matrix `[0, 1]` und die lane-spezifischen Concurrency-Gruppen in
`agent-request-queue.yml`.

### Hoch — Branch-Existenzprüfung ist keine atomare Claim-Sperre

Die Queue prüft per `git ls-remote`, ob `agent/<task_id>-copilot-cli`
existiert, und prüft in „Prepare isolated branch“ erneut. Zwischen den Checks
und dem späteren Workflow-Push gibt es jedoch keinen serverseitigen Claim und
keine Sperre über beide Lanes. Die Concurrency-Gruppen sind lane-spezifisch;
die zwei Matrix-Jobs eines Laufs können parallel starten. Bei doppelten
Requests für dieselbe Task-ID können daher beide den Branch zunächst als
nicht vorhanden sehen und beide die Copilot-Sitzung starten. Die spätere
Branch-Erstellung bzw. der Push verhindert nicht die bereits doppelte
Ausführung. Das tritt insbesondere zusammen mit dem vorigen Finding auf.

### Hoch — Fehler beim Lesen einer Lane wird als leere Lane behandelt

Im Control-Plane-Schritt „Collect queue and resource state“ wird jeder Fehler
beim Abruf einer Lane-Dateiliste durch `|| echo '[]'` in eine erfolgreiche
leere Liste umgewandelt. Das umfasst nicht nur eine tatsächlich nicht
existierende Lane, sondern auch API-, Berechtigungs- oder Rate-Limit-Fehler.
Der Planer kann die unbekannte Lane dann als frei behandeln und eine
Request-Datei anlegen, die eine vorhandene, aber nicht gelesene Datei
überschreibt. Damit ist der Ressourcen-Preflight in diesem Fehlerpfad nicht
fail-closed.

### Mittel — Queue validiert den aktuellen Issue-Zustand nicht

„Resolve next queued request“ prüft beim erneuten Laden des Issues nur Owner
und `agent-cli-ready`-Label. Ein Request für ein inzwischen geschlossenes
Issue (oder einen PR-Eintrag mit passendem Body/Label) kann daher noch an
`agent_dispatch` übergeben und ausgeführt werden. `eligible_issues()` filtert
zwar neue Kandidaten auf `state == "open"` und schließt PRs aus, aber diese
Prüfung wird für bereits eingereihte Requests nicht wiederholt. Entfernte
Labels führen stattdessen zu einem fehlgeschlagenen Lane-Lauf; der Control
Plane entfernt solche Requests nicht, solange kein Agent-Branch existiert.
Das kann eine Lane dauerhaft blockieren bzw. wiederholt fehlgeschlagene
Runs auslösen.

### Mittel — Agent kann die nachgelagerten Publikations-Gates umgehen

`actions/checkout` persistiert standardmäßig seine Git-Credentials. Der
Copilot-Schritt erhält `shell(git:*)`, während der Job Schreibrechte für
`contents` besitzt. Die Prüfungen für Task-Dateiumfang und Regressionen laufen
erst nach der Agentensitzung. Das Verbot eines eigenen Pushes steht nur im
Prompt; es gibt keine technische Sperre, die einen direkten Push vor diesen
Prüfungen verhindert. Eine solche Veröffentlichung könnte die anschließenden
Workflow-Gates umgehen. Schreibberechtigungen sollten erst für den
Publikationsschritt verfügbar sein oder die Checkout-Credentials während der
Agentensitzung nicht persistieren.

### Niedrig — Bestehender Routing-Test schlägt fehl

`python -m pytest -q tests/test_autonomous_control_plane.py` ergibt **1 failed,
4 passed**. `test_plan_retires_published_branch_and_fills_lane` erwartet nach
Entfernen eines Requests mit vorhandenem Branch nur ein Assignment. Da dadurch
beide Standard-Lanes frei sind und zwei geeignete Issues vorliegen, erzeugt
`plan()` tatsächlich zwei Assignments. Der bestehende Erwartungswert stimmt
nicht mit dem aktuellen Zwei-Lanes-Routing überein; der Testbestand ist damit
nicht grün und bildet die tatsächliche Lane-Freigabe nach Retirement nicht
konsistent ab.

### Niedrig — `workflow_dispatch` kann falsche SHA-Provenienz stempeln

Beide Workflows checken explizit `master` aus, verwenden für die
Control-Plane-Ausgabe bzw. `agent_dispatch` aber `${{ github.sha }}` bzw.
`$GITHUB_SHA`. Bei einem manuellen Dispatch von einer anderen Ref bezeichnet
dieser SHA nicht notwendigerweise den ausgecheckten `master`-Stand.
`validate_task()` prüft nur das SHA-Format, nicht die Übereinstimmung mit dem
ausgecheckten Commit. Plan-Artefakt bzw. Dispatch-Manifest können so einen
falschen `source_master_sha` ausweisen.

## Geprüfte Kontrollen / Einordnung

- **Task-Vertrag:** Ungültige Verträge mit neuer Zuweisung werden vor dem
  „Apply queue mutations“-Schritt durch `validate_assignment_contracts()`
  abgelehnt; die Queue validiert den Issue-Vertrag erneut über
  `automation.agent_dispatch`. In diesem Pfad ist das Verhalten fail-closed.
- **Zwei CLI-Lanes:** Der produktive Control-Plane-Aufruf nutzt die Defaults
  `"0"`/`"1"`; der Workflow liest nur `lane0`/`lane1` und die Queue-Matrix ist
  fest auf `[0, 1]` begrenzt. Die Funktion `plan()` selbst erlaubt jedoch einen
  überschreibbaren `lanes`-Parameter; außerhalb des aktuellen Workflow-Aufrufs
  erzwingt sie nicht eigenständig exakt zwei Lanes.
- **Stale/untracked Requests:** Branch-bekannte Requests werden retiret. Auf
  offenen Requests ohne Branch wird der Issue-Zustand nicht nachgeführt. Die
  Workflow-Checkout-Arbeitsverzeichnisse beginnen sauber; die Queue prüft
  untracked Dateien vor dem Commit gegen `allowed_paths`. Der Control Plane
  staged nur `agent_requests`, aber der fail-open Lane-Abruf bleibt dabei ein
  Überschreibungsrisiko.
- **Trigger/Concurrency:** Pushes auf `agent_requests/**` starten sowohl den
  Control Plane als auch die Queue; ein Control-Plane-Push erzeugt damit einen
  zusätzlichen Control-Plane-Lauf, der normalerweise ohne Änderungen endet.
  Die beiden Workflows haben unterschiedliche globale Concurrency-Gruppen und
  können gleichzeitig laufen. Die Queue serialisiert ihre Workflow-Läufe und
  zusätzlich je Lane; sie synchronisiert sich aber nicht mit dem Control
  Plane.
- **Cloud Agent vs. CLI:** Die geprüften Routingpfade verwenden
  `agent-cli-ready` und Request-Dateien; die Dokumentation benennt
  `cloud-agent-ready` als getrennten Trigger. In den geprüften Dateien wurde
  keine direkte Cloud-Agent-Dispatch-Kopplung gefunden.
- **Permissions:** Der Control Plane benötigt Schreibrechte für den
  Queue-Push; die Queue benötigt Issue-/PR-Schreibrechte für Kommentare und
  PR-Publikation. Die Rechte sind auf Workflow-Ebene statt auf die jeweils
  schreibenden Schritte begrenzt, wodurch sie auch während weniger privilegierter
  Schritte verfügbar sind.

**Scope- und Sicherheitsgrenzen:** Es wurden keine Workflows, Codepfade,
Research-/Evidence-Dateien, Sicherheitsinvarianten oder Queue-Daten geändert.
