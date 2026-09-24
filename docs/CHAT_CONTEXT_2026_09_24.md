# Verfügbare Chat-Kontext-Evidenz — 2026-09-24

Dieses Dokument hält nur den Projektkontext fest, der aus den aktuell verfügbaren
Gesprächszusammenfassungen und der laufenden Unterhaltung belastbar hervorgeht.
Es ist **kein vollständiger Export aller alten Chats**.

## A. Dauerhafte Projektregeln aus den Gesprächen

### A1 — Safety
- Das Projekt bleibt strikt Paper-/Simulations-only.
- Keine Live-Ausführung und keine automatische Echtgeldpromotion.
- Ein späterer Live-Pfad benötigt eine explizite separate Freigabe und eigene technische/
  ökonomische Prüfungen.

### A2 — Arbeitsweise
- Möglichst autonom arbeiten.
- Nicht raten; bei widersprüchlicher oder fehlender Evidenz verifizieren.
- So wenig manuelle Schritte wie möglich.
- Status, Checkpoints, Logs und Resume-Fähigkeit dauerhaft speichern.
- GitHub-zentrierte, reproduzierbare Arbeitsweise bevorzugen.

### A3 — Repository-/Actions-Trennung
- `DWR-debug/trading-agent-public` ist die operative öffentliche Research-/CI-Quelle.
- `DWR-debug/trading-agent` bleibt privat und wird nicht als GitHub-Actions-Ausführungsquelle
  verwendet.
- Diese Trennung ist ausdrücklich Teil der Projekt-Governance.

### A4 — Zusammenarbeit zwischen Chats
Bei einem neuen „trading agent“-Chat soll nicht wieder bei Null begonnen werden.
Der Einstieg soll über dauerhafte Projektdateien plus aktuelle GitHub-Verifikation erfolgen.

Die gewünschte Reihenfolge ist:

`PROJECT_CONTEXT.md`
→ `PROJECT_STATUS.md`
→ Ledger
→ aktuelle Branch-/PR-/Workflow-Lage
→ relevante Checkpoints/Reports
→ nächste Arbeit.

## B. Wichtige Entwicklungsprinzipien aus dem bisherigen Projektverlauf

### B1 — Forschung vor Produktionsintegration
Der Agent soll nicht auf eine einzelne Strategie festgelegt sein.
Neue Returnquellen sollen möglichst orthogonal sein und unabhängig validiert werden.

### B2 — Negative Ergebnisse sind Fortschritt
Verworfene Trials sollen nicht gelöscht werden, wenn sie wichtige Informationen
über Risiko, Robustheit, Datenqualität oder mögliche Bausteine enthalten.

### B3 — Zielkonflikt Rendite vs. Robustheit
Die Gespräche haben wiederholt klargestellt, dass eine hohe historische Rendite
allein nicht genügt. Kosten, Drawdown, Rolling-/Walk-Forward-Stabilität,
Holdout und tatsächliche Ausführbarkeit müssen getrennt betrachtet werden.

### B4 — Exposure nicht mit Edge verwechseln
Leverage und Long/Short dürfen untersucht werden, aber nicht bloß eingesetzt werden,
um Rendite künstlich zu vervielfachen. Ein höheres Exposure braucht selbst belastbare
OOS-/Holdout-/Stress-Evidenz.

### B5 — Daten zuerst
Coverage- oder Kalenderprobleme müssen vor Performanceauswertung erkannt und als
Datenqualitätsereignis archiviert werden.

## C. Entwicklung des gemeinsamen Forschungsstils

Aus den Gesprächen hat sich eine wiederkehrende Präferenz ergeben:

- einzelne Intervention statt großer Suchläufe;
- vorregistrierte, klar isolierte Experimente;
- unabhängige Datensätze;
- keine nachträgliche Auswahl anhand des Holdouts;
- formale Evidenzkette mit Fingerprints und Artefakten;
- negative Resultate explizit dokumentieren;
- danach eine neue, möglichst orthogonale Frage.

## D. Kontext, der nicht als technische Wahrheit behandelt werden darf

Frühere Chatangaben zu Dateipfaden, Commits, Workflow-Zuständen oder Testergebnissen
sind historische Hinweise. Sobald der aktuelle öffentliche `master`, ein Workflow,
ein Artefakt oder ein Report die aktuelle Lage belastbar ausweist, wird diese technische
Gegenwart dort verifiziert.

Der Chat bleibt dabei wichtig für Absicht, Entscheidungen, Prioritäten und Forschungslogik.

## E. Fehlende Alt-Chats

Nicht automatisch zugängliche alte Chatverläufe werden nicht erfunden.

Werden später Exporte oder Transkripte verfügbar, werden sie nach
`docs/PROJECT_CONTEXT_INGESTION.md` klassifiziert und in dauerhafte relevante
Projektentscheidungen/Evidenz überführt.

## F. Status

Diese Datei ist eine Kontextablage, kein Forschungsreport und kein zweiter Ledger.
