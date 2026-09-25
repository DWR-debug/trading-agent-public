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

## Aktuell verifizierte Tarifpreise

Stand 2026-09-25:
- **Free:** 0 USD/Monat; eingeschränkter Codex-Zugriff.
- **Go:** 8 USD/Monat.
- **Plus:** 20 USD/Monat; erweiterte Codex-Nutzung.
- **Pro:** ab 100 USD/Monat; deutlich höhere Codex-Nutzung.
- **Pro 200 USD:** neue Anmeldungen/Upgrades sind laut OpenAI seit 10. September 2026 vorübergehend ausgesetzt.
- **Credits:** können bei unterstützten Funktionen nach Ausschöpfung des enthaltenen Kontingents verbrauchsabhängig eingesetzt werden; tatsächliche Verfügbarkeit und Preise sind kontospezifisch zu prüfen.
- **GitHub Actions:** Standard-Runner in öffentlichen Repositories sind kostenlos und unbegrenzt; größere Runner sind kostenpflichtig.

OpenAI- und GitHub-Angaben ändern sich. Dieses Dokument hält deshalb nur einen verifizierten Snapshot fest und ersetzt keine Live-Abrechnung.

## Bezugsgröße 500 EUR

Für die Projektplanung dient 500 EUR als Referenzkapital. Die reine Gebühr als Anteil dieser Referenzgröße beträgt:

| Monatlicher Einsatz | Anteil von 500 EUR |
|---:|---:|
| 0 EUR | 0,0 % |
| 20 USD (~18 EUR bei angenommener Parität nur als Näherung) | ~3,6 % |
| 100 USD (~91 EUR bei angenommener Parität nur als Näherung) | ~18,2 % |

Die EUR-Werte sind nur Sensitivitätsrechnungen; tatsächlicher Wechselkurs und ggf. Steuern/Gebühren sind nicht berücksichtigt.

## Break-even-Denken

Bei 500 EUR Referenzkapital entsprechen die oben genannten Monatskosten:

| Monatskosten | Anteil von 500 EUR | notwendiges zusätzliches Nettoergebnis/Monat nur zum Kostenausgleich |
|---:|---:|---:|
| 0 EUR | 0,0 % | 0 EUR |
| 6,96 EUR | 1,4 % | 6,96 EUR |
| 17,41 EUR | 3,5 % | 17,41 EUR |
| 87,03 EUR | 17,4 % | 87,03 EUR |
| 174,06 EUR | 34,8 % | 174,06 EUR |

Für ein Jahresabonnement verändert sich die Perspektive deutlich: Plus entspräche bei diesem illustrativen Kurs rund 209 EUR/Jahr, also rund 41,8 % des Referenzkapitals; Pro rund 1.044 EUR/Jahr bzw. rund 208,9 %.

Das sind reine Kostenschwellen. Sie sind **keine Renditeprognosen** und sagen nicht, dass die erforderlichen Ergebnisse erreichbar sind.

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

## Ledger

Die tatsächliche Agentennutzung wird ausschließlich mit real beobachteten Werten in `research/evidence/agent_usage_ledger.json` protokolliert; das Schema liegt in `research/evidence/agent_usage_ledger.schema.json`. Ein leerer Ledger bedeutet ausdrücklich: **keine behaupteten Nutzungskosten**.

## Operative Regel

Solange kostenlose Ressourcen ausreichen, wird **kein bezahlter Agenteneinsatz benötigt**. Ein Upgrade oder Credit-Einsatz wird erst erwogen, wenn:

1. eine konkrete Engpassaufgabe existiert,
2. die kostenlose Route nachweislich zu langsam/limitiert ist,
3. der erwartete Mehrwert klar beschrieben werden kann,
4. das Budget vorab begrenzt ist,
5. kein Sicherheits-, Holdout- oder Research-Governance-Gate umgangen wird.

## Sicherheitsgrenze

Kein Agentenbudget darf dazu führen, dass ein negativer oder DATA_INSUFFICIENT-Befund durch zusätzliche Suchläufe, Parameter-Sweeps oder Holdout-Selektion in einen positiven Befund umgewandelt wird. Agentische Arbeit erzeugt Design-/Review-Material; formale Evidence entsteht nur über den eingefrorenen Forschungsprozess.
