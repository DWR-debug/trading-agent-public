# Agent-/Compute-Ressourcen: Kosten-Nutzen-Modell

Stand: 2026-09-25

## Ziel

Agentische Ressourcen werden als begrenztes Forschungsbudget behandelt. Bezahlt wird nur dann, wenn der erwartete Erkenntnis-, Entwicklungs- oder Zeitgewinn die Kosten plausibel rechtfertigt. Die wissenschaftlichen Gates und die Paper-only-Sicherheitsgrenzen bleiben unabhängig davon bindend.

## Priorität der Ressourcen

1. **Kostenlos:** ChatGPT Free / enthaltene Codex-Nutzung, sofern im Konto verfügbar.
2. **Kostenlos:** öffentliche GitHub-Actions-Ressourcen für dieses öffentliche Repository, soweit GitHub-Limits und Verfügbarkeit dies zulassen.
3. **Kostenlos:** lokale/benutzerseitige Rechenzeit und vorhandene Daten-/Artifact-Caches.
4. **Optional bezahlt:** ChatGPT Plus/Pro nur für deutlich höheren Agent-Durchsatz.
5. **Optional bezahlt:** API-/Credits-Nutzung nur für klar abgegrenzte, messbare Aufgaben.

## Bekannte Tarifpreise

Die offiziellen OpenAI-Preise nennen aktuell:
- Free: 0 USD/Monat.
- Plus: 20 USD/Monat.
- Pro: ab 100 USD/Monat.
- API-/nutzungsbasierte Nutzung wird separat nach Modell und Tokenverbrauch berechnet.

Diese Preise sind keine Renditeversprechen. Sie beschreiben ausschließlich den Ressourceneinsatz.

## Bezugsgröße 500 EUR

Für die Projektplanung dient 500 EUR als Referenzkapital. Die reine Gebühr als Anteil dieser Referenzgröße beträgt:

| Monatlicher Einsatz | Anteil von 500 EUR |
|---:|---:|
| 0 EUR | 0,0 % |
| 20 USD (~18 EUR bei angenommener Parität nur als Näherung) | ~3,6 % |
| 100 USD (~91 EUR bei angenommener Parität nur als Näherung) | ~18,2 % |

Die EUR-Werte sind nur Sensitivitätsrechnungen; tatsächlicher Wechselkurs und ggf. Steuern/Gebühren sind nicht berücksichtigt.

## Break-even-Denken

Für einen bezahlten Dienst ist der relevante Mindestnutzen zunächst nicht eine erwartete Trading-Rendite, sondern vermiedene Arbeitszeit, zusätzliche reproduzierbare Forschung, schnellere Fehlererkennung oder zusätzliche belastbare Evidence.

Bei einem Monatsbudget von C EUR muss der Dienst mindestens C EUR an wirtschaftlich verwertbarem Nutzen erzeugen, damit der Einsatz nominal kostendeckend ist.

Wenn man stattdessen nur betrachtet, wie viel zusätzliches realisiertes Nettoergebnis auf 500 EUR Kapital erforderlich wäre, um die Gebühr zu decken:

- 20 EUR Kosten -> 4,0 % des Referenzkapitals pro Monat.
- 50 EUR Kosten -> 10,0 %.
- 100 EUR Kosten -> 20,0 %.

Das ist **keine** Aussage darüber, dass solche Renditen erreichbar oder wahrscheinlich sind. Es ist lediglich die mathematische Kostenschwelle.

## Forschungs-ROI

Jede bezahlte Agent-/API-Nutzung soll nach Möglichkeit protokollieren:

- Aufgabe / Hypothese
- eingesetzte Ressource
- tatsächliche Kosten
- Laufzeit
- akzeptierte Änderung oder verwertbares Review-Ergebnis
- verworfene Vorschläge
- vermiedene Runner-/Entwicklungszeit
- Einfluss auf Evidence oder Fehlererkennung

Damit kann später gemessen werden, ob bezahlte Nutzung gegenüber kostenlosen Alternativen tatsächlich einen Mehrwert erzeugt.

## Operative Regel

Solange kostenlose Ressourcen ausreichen, wird **kein bezahlter Agenteneinsatz benötigt**. Ein Upgrade oder Credit-Einsatz wird erst erwogen, wenn:

1. eine konkrete Engpassaufgabe existiert,
2. die kostenlose Route nachweislich zu langsam/limitiert ist,
3. der erwartete Mehrwert klar beschrieben werden kann,
4. das Budget vorab begrenzt ist,
5. kein Sicherheits-, Holdout- oder Research-Governance-Gate umgangen wird.

## Sicherheitsgrenze

Kein Agentenbudget darf dazu führen, dass ein negativer oder DATA_INSUFFICIENT-Befund durch zusätzliche Suchläufe, Parameter-Sweeps oder Holdout-Selektion in einen positiven Befund umgewandelt wird. Agentische Arbeit erzeugt Design-/Review-Material; formale Evidence entsteht nur über den eingefrorenen Forschungsprozess.
