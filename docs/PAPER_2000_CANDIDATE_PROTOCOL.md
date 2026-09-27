# Formaler 2.000-EUR-Kandidatenlauf

Ein formaler EUR-2.000-Paperlauf ist ausschließlich für einen bereits Evidence-eligible Kandidaten zulässig.
Die 2.000 EUR sind ausschließlich fiktives Referenzkapital für die Simulation. Sie belegen weder verfügbares
reales Kapital noch Zahlungsfähigkeit, reale Rendite oder Entnahmefähigkeit. Das bestehende 500-EUR-Canary
bleibt eine getrennte historische Betriebssimulation.

Voraussetzungen:
1. frisch symbol-disjunkte Coverage und formale Evaluation,
2. unveränderter Evidence-Vertrag mit `VALIDATED_PASS`,
3. `holdout_used_for_selection == false`,
4. unveränderter Paper-only-Sicherheitsvertrag,
5. genau ein eingefrorenes Kandidatenmanifest.

Der vorhandene 30-Tage-Harness wird mit `--initial-capital-eur 2000` ausgeführt.
Manifest-, Evidenz- und Return-Stream-Pfade sind Repository-relative Pfade des ausgecheckten
Repositorys. Das Manifest liegt unter `research/paper_candidates_2000/`; aufgelöste Symlinks und
Pfadbestandteile dürfen nicht aus dem Checkout herausführen.

Vor dieser Stufe sind 2.000-EUR-Engineering-Shadows möglich. Sie sind reine technische Beobachtung und erzeugen keine Research Evidence.

Die Lane vergleicht keine Kandidaten, wählt nicht automatisch aus, optimiert keine Parameter und verwendet keinen Holdout zur Auswahl.
