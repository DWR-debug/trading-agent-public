# Forschungs-DAG

DAG bedeutet Directed Acyclic Graph, also gerichteter azyklischer Graph.

Im Trading-Agent-OS beschreibt er die Abhängigkeiten zwischen Forschungsstufen.
Ein Knoten ist ein klar definierter Arbeitsschritt bzw. Receipt-Vertrag. Eine
Kante bedeutet: A darf erst starten, wenn B erfolgreich und passend belegt ist.

Beispiel:

Source Feasibility -> PIT Readiness -> Immutable Historical Snapshot ->
Candidate PIT -> Independent Reproduction -> Formal Authorization -> Performance

Unabhängige Zweige können parallel laufen. Sobald ein Schritt abgeschlossen ist,
darf das OS den receipt-definierten Nachfolger automatisch starten.

## Warum azyklisch

Ein späteres Performance-Ergebnis darf eine frühere Voraussetzung nicht
rückwirkend ändern. Dadurch bleiben Provenienz und Entscheidungsgrenzen
nachvollziehbar.

## Aktuelles Beispiel

Q197:
source component ready -> immutable historical award-state snapshot ->
frozen relationship mapping -> PIT compiler -> independent reproduction

Q121-R6:
primary acceptance-time compilation -> successful primary receipt ->
3-shard Windows independent reproduction

Der DAG ist damit kein Forschungsplan auf Zuruf, sondern ein maschinenlesbares
Abhängigkeits- und Beweismodell.
