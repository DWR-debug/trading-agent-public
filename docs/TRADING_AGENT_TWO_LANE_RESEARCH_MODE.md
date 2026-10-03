# Trading Agent — Permanenter Zwei-Lanes-Forschungsmodus

Stand: 2026-10-03

## Verbindlicher Betriebsstandard

Der Trading Agent arbeitet mit zwei logisch getrennten Forschungsbahnen, wenn die zwei Windows-Self-Hosted-Slots verfügbar sind:

- **Lane A — Formal Readiness:** fortgeschrittene Coverage-, PIT-, Compiler-, Provenienz- und Autorisierungsreife für vollständig präregistrierte Forschungsobjekte.
- **Lane B — Frontier Discovery:** orthogonale Informationsquellen, öffentliche Quellen, PIT-/Revisionssemantik und billige Falsifikation neuer Mechanismen.

## Isolationsregeln

Jede Lane verwendet eigene Candidate-/Trial-Identität sowie getrennte Branches, Workflows, Receipt- und Output-Pfade. Gemeinsam veränderlicher Research-State ist unzulässig.

Ergebnisse der anderen Lane dürfen nur eine neue, separat eingefrorene Hypothese begründen. Ein bereits eingefrorener Trial darf wegen Ergebnissen der anderen Lane nicht rückwirkend verändert werden.

## Performance-Grenze

Die zwei Slots sind ausschließlich Kapazität. Sie erzeugen keine wissenschaftliche oder operative Performance-Autorisierung.

Eine Performance-Ausführung ist nur zulässig, wenn für genau diesen unabhängigen, eingefrorenen Trial eine aktuelle formale Autorisierung vorliegt. Fehlt sie, bleibt der Performance-Pfad fail-closed.

## Routing

Lane A wird auf den kleinsten geeigneten Windows-Slot für Readiness-/Governance-Arbeit geroutet; Lane B auf den zweiten Slot für Frontier-/Feasibility-Arbeit. Bereits laufende Arbeit wird nicht dupliziert.

Die parallel laufende GitHub-hosted Frontier-Fabrik bleibt davon getrennt und darf ihre interne bounded concurrency verwenden.

## Sicherheitsinvarianten

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
