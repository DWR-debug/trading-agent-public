# Bounded Agent Dispatch

## Zweck

Dieses Modul schließt die bisher offene technische Lücke zwischen unserem
vorbereiteten Agenten-Rollenmodell und der tatsächlichen PR-basierten Delegation.

Der Dispatch-Pfad ist **fail-closed**. Ein Issue muss einen expliziten
maschinenlesbaren Task-Vertrag tragen und das Label `agent` oder `agent-ready` besitzen.
Erst dann darf GitHub versuchen, den nachgeordneten Copilot-Worker zuzuweisen.

## Kontrollkette

`Issue vorbereiten → Vertragsprüfung → Konfidenz-/Concurrency-Prüfung → Copilot-Zuweisung → PR → CI → Review → Merge`

Der automatische Coding-Dispatch nutzt derzeit ausschließlich den PR-fähigen `trading-agent-engineer`-Worker. Reviewer und Hypothesen-Worker bleiben getrennte, nachgeordnete Review-/Designpfade. Der Agent erhält nur eine klar begrenzte Aufgabe. Der Dispatch-Vertrag verbietet
explizit deterministische Backtests, Holdout-/Parameter-/Asset-/Threshold-/Horizon-
Selektion, Gate-Änderungen, Promotion und Live-Ausführung.

## Zwei-Slot-Lease

Die Kapazitätsgrenze wird als gemeinsamer Lease-Zustand mit genau zwei
benannten Slots modelliert. Die normative Lease-Bindung enthält `task_id`,
Issue-Nummer, Manifest-Fingerprint und Run-ID. Ein abgelaufener Lease wird
beim nächsten Zugriff entfernt und kann seinen Slot zurückgeben.

Die Lease-Zustandsmaschine ist idempotent nur für exakt dieselbe Bindung.
Dieselbe Task-ID mit einem anderen Manifest-Fingerprint oder einer anderen
Run-ID wird fail-closed abgelehnt. Ein Lease darf nur von genau derselben
Bindung erneuert oder freigegeben werden.

Die technische Obergrenze beträgt zwei Slots. Das ist unabhängig von der
separaten Ressourcengrenze für Copilot Free: tatsächlich parallele Copilot-
Sessions bleiben auf **eine** begrenzt. Der alte Issue-/Bot-Assignment-Count
darf daher nicht mehr als gemeinsamer Kapazitätszähler interpretiert werden;
Branch-, Issue- und PR-Zustände sind abgeleitete Prüfungen.

## Ressourcenregel

Die technische Dispatch-Schicht kennt **keine** bezahlte Erweiterung.
`paid_usage=false` ist Bestandteil des Task-Vertrags. Die bisherige Projektregel
`paid_agent_budget_usd=0` bleibt unverändert.

Die tatsächliche Agentennutzung wird nicht aus dem Dispatch-Versuch abgeleitet.
Ein Lease bedeutet nur reservierte technische Kapazität. Erst ein verifizierter
Agent-PR/Run darf später im Usage-Ledger als tatsächliche Nutzung eingetragen
werden.

Die Lease-Datei bzw. der verwendete gemeinsame Zustandsdienst muss atomare
Schreibzugriffe unterstützen. Das versionierte Python-Modul stellt dafür ein
plattformübergreifendes Lock-/Atomic-Replace-Primitive bereit. Die Queue-,
Cloud-Agent- und manuelle Dispatch-Schicht müssen denselben Zustand verwenden;
ein rein lokaler, pro Runner getrennter Zähler ist **kein** Ersatz für den
gemeinsamen Lease.

## Task-Vertrag

Beispiel:

<!-- TRADING_AGENT_TASK_V1
{"schema_version":1,"task_id":"AGENT-EXAMPLE-001","worker_class":"engineering","custom_agent":"trading-agent-engineer","base_branch":"master","scope":"bounded technical task","max_session_minutes":30,"deterministic_compute":false,"holdout_selection":false,"parameter_selection":false,"asset_selection":false,"threshold_selection":false,"horizon_selection":false,"research_gate_changes":false,"promotion_decision":false,"live_execution":false,"paid_usage":false,"research_decision":false,"manual_handoff_required":false}
-->

Der Manifest-Fingerprint bindet zusätzlich den vollständigen Issue-Inhalt. Die JSON-Struktur ist absichtlich explizit. Ein prose-only Issue kann nicht
versehentlich als agentische Ausführungsfreigabe interpretiert werden.

## Normative Scope-Prüfung

`automation.agent_dispatch.normalize_allowed_paths` normalisiert die
Allowlist beim Auflösen des Vertrags. `automation.agent_dispatch.validate_scope_paths`
ist die normative Prüfung für geänderte Pfade; der Resolve- und
Publikationspfad darf keine zweite Wildcard- oder Protected-Prefix-Implementierung
führen. `automation.agent_scope_guard` bezieht unstaged, staged und nicht
ignorierte untracked Dateien ein, einschließlich beider Seiten erkannter
Umbenennungen, und verwendet diese gemeinsame Prüfung. Der Guard muss vor dem
Staging und nach `git add -A` laufen, damit beide Zustände fail-closed geprüft
werden.

Die geschützten Präfixe bleiben `.github/`, `research/evidence/`,
`research/authorizations/` und `gates/`. Die ältere Workflow-Datei
`.github/workflows/copilot-cli-engineering-task.yml` enthält weiterhin eine
inline Scope-Prüfung; sie liegt außerhalb des für AGENT-025 freigegebenen
Änderungsumfangs und muss separat auf den gemeinsamen Python-Validator
umgestellt werden. Bis dahin gilt diese Workflow-Integration als bekanntes
Drift-Risiko und nicht als durch diese Änderung zentralisiert.
