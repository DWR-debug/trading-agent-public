# Forschungs-DAG — Trading Agent OS

## Begriff

DAG = **Directed Acyclic Graph**, auf Deutsch ein gerichteter azyklischer Graph.

Im Trading-Agent-OS beschreibt der Forschungs-DAG die zulässige Reihenfolge von Forschungsrunden. Ein Knoten ist eine klar abgegrenzte Arbeitseinheit bzw. ein Receipt; eine Kante bedeutet: **Das Ergebnis der vorherigen Runde erfüllt die definierten Voraussetzungen für genau die nächste Runde.**

Beispiel:

`Quelle entdeckt -> Source-Feasibility -> historische Snapshot-Prüfung -> PIT-Rekonstruktion -> unabhängige PIT-Reproduktion -> formale Autorisierung`

Nicht jede Kante ist automatisch offen. Jede Runde prüft ihren Eingangszustand. Fehlt ein historisches Artefakt, stoppt der Pfad fail-closed; das OS darf dann eine andere unabhängige Frontier-Runde bearbeiten.

## Warum DAG statt einfache Warteschlange?

Eine reine Warteschlange würde nur `A -> B -> C` abarbeiten. Der Forschungsprozess hat aber mehrere voneinander unabhängige Zweige.

Beispiel:

`Q199 -> historische USPTO-Rekonstruktion`
und gleichzeitig
`Q201 -> historische ClinicalTrials-Rekonstruktion`
und gleichzeitig
`Q186 -> Citation/Publications-PIT`

Diese Zweige können parallel laufen. Erst wenn ihre eigenen Voraussetzungen erfüllt sind, dürfen sie in spätere Phasen übergehen.

## Regeln im OS

1. **Nur receipt-definierte Kanten.** Ein abgeschlossenes Ergebnis darf die nächste Runde nur dann starten, wenn deren Eingangsgate formal erfüllt ist.
2. **Keine rückwirkende Mutation.** Eine neue Runde erhält eine eigene Trial-/Candidate-Identität und verändert kein eingefrorenes Ergebnis.
3. **Keine künstliche Beschäftigung.** Ist kein sinnvoller nächster Knoten bereit, bleibt die Ressource frei.
4. **Parallelität nur bei Unabhängigkeit.** Verschiedene DAG-Zweige dürfen parallel laufen, wenn sie keine gemeinsame mutable Scientific State teilen.
5. **Fail-closed.** Fehlende Coverage-, PIT-, Snapshot-, Revision- oder Authorization-Artefakte blockieren den jeweiligen Zweig.
6. **AI ist kein Autorisierungsknoten.** AI-Reviews liefern nur zusätzliche Handoff-/Gegenargumente; sie erzeugen weder Performance-Evidenz noch Freigaben.
7. **Performance ist ein separater formaler Zweig.** Kapazität, Frontier-Ergebnisse oder AI-Ausgaben können diesen Zweig nicht selbst öffnen.

## Aktueller Beispielpfad

Für Q195/Q196/Q197/Q199/Q201 ist der aktuelle sichere Pfad:

`Source component ready -> immutable historical snapshot required -> candidate-specific PIT -> independent PIT reproduction -> formal authorization review`

Der Schritt `immutable historical snapshot required` ist absichtlich vor PIT platziert. Ein aktueller Live-API-Test oder ein aktueller Content-Hash gilt nicht als historisch dauerhaft gebunden.

## Nachtbetrieb

Runner C arbeitet nur an Knoten, deren Eingangsgates bereits erfüllt sind. Die Nachtplanung stellt daher keine Liste von garantiert ausführbaren Runs dar, sondern eine priorisierte Menge möglicher DAG-Knoten.

