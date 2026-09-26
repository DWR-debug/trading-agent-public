# Bounded Agent Dispatch

## Zweck

Dieses Modul schließt die bisher offene technische Lücke zwischen unserem
vorbereiteten Agenten-Rollenmodell und der tatsächlichen PR-basierten Delegation.

Der Dispatch-Pfad ist **fail-closed**. Ein Issue muss einen expliziten
maschinenlesbaren Task-Vertrag tragen und das Label `agent-ready` besitzen.
Erst dann darf GitHub versuchen, den nachgeordneten Copilot-Worker zuzuweisen.

## Kontrollkette

`Issue vorbereiten → Vertragsprüfung → Konfidenz-/Concurrency-Prüfung → Copilot-Zuweisung → PR → CI → Review → Merge`

Der Agent erhält nur eine klar begrenzte Aufgabe. Der Dispatch-Vertrag verbietet
explizit deterministische Backtests, Holdout-/Parameter-/Asset-/Threshold-/Horizon-
Selektion, Gate-Änderungen, Promotion und Live-Ausführung.

## Zwei-Slot-Regel

Vor jeder Zuweisung zählt der Workflow offene Issues mit
`copilot-swe-agent[bot]`. Bei zwei aktiven Zuweisungen wird der neue Task
nicht gestartet. Dadurch können zwei unabhängige Sessions parallel laufen,
ohne eine dritte Session zu erzeugen.

## Ressourcenregel

Die technische Dispatch-Schicht kennt **keine** bezahlte Erweiterung.
`paid_usage=false` ist Bestandteil des Task-Vertrags. Die bisherige Projektregel
`paid_agent_budget_usd=0` bleibt unverändert.

Die tatsächliche Agentennutzung wird nicht aus dem Dispatch-Versuch abgeleitet.
Erst ein verifizierter Agent-PR/Run darf später im Usage-Ledger als tatsächliche
Nutzung eingetragen werden.

## Task-Vertrag

Beispiel:

<!-- TRADING_AGENT_TASK_V1
{"schema_version":1,"task_id":"AGENT-EXAMPLE-001","worker_class":"engineering","custom_agent":"trading-agent-engineer","base_branch":"master","scope":"bounded technical task","max_session_minutes":30,"deterministic_compute":false,"holdout_selection":false,"parameter_selection":false,"asset_selection":false,"threshold_selection":false,"horizon_selection":false,"research_gate_changes":false,"promotion_decision":false,"live_execution":false,"paid_usage":false,"research_decision":false,"manual_handoff_required":false}
-->

Die JSON-Struktur ist absichtlich explizit. Ein prose-only Issue kann nicht
versehentlich als agentische Ausführungsfreigabe interpretiert werden.
