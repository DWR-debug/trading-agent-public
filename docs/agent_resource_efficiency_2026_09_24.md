# Agenten-/Credit-Effizienz — Arbeitsregeln 2026-09-24

## Ziel

Begrenzte Agenten-/Codex-Nutzung soll nur dort eingesetzt werden, wo sie gegenüber deterministischer Automation einen qualitativen Mehrwert bringt.

## Verbindliche Nutzung

- Datenakquise, Backtests, Walk-Forward, Gate-Prüfung und Artefaktbau: GitHub Actions / deterministische Python-Runner.
- Architektur, Hypothesenbildung, Failure-Synthese, Code-Review und Governance: Agenten-/Codex-Ressourcen.
- Unabhängige Evidence-Abfragen werden gebündelt statt einzeln ausgeführt.
- Coverage-Artefakte werden eingefroren und für Formalruns wiederverwendet; keine unnötige Neunakquise.
- Fail-fast-Contract-Tests müssen vor einem teuren Formalrun laufen.
- Keine automatische kostenpflichtige Nutzung; projektseitiges Budget bleibt `0 USD`.

## Lessons aus T041

Der T041-Ablauf zeigte drei vermeidbare Ressourcenverluste: ein fehlendes Holdout-Feld im Runner, ein fehlender Workflow-Pfadfilter für den geänderten Runner und eine zunächst nicht eingefrorene Coverage-Verwendung. Diese Klassen von Fehlern werden künftig durch Contract-Tests und einen zentralen Frozen-Artifact-Pfad abgefangen.

Das technische Budget und die wissenschaftliche Datenmenge werden damit getrennt: Agentenarbeit erzeugt bessere Entscheidungen und Prüfungen; die eigentliche numerische Ausführung bleibt reproduzierbar und günstig.
