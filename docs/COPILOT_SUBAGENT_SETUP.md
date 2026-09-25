# Copilot-Unteragent in GitHub Codespaces

## Ziel

Der Repository-Setup stellt einen schreibgeschützten Copilot-Unteragenten für Hypothesenforschung bereit.

Aktuell unterstützt GitHub Copilot Free Copilot CLI und benutzerdefinierte Agents; die kostenlose Stufe hat jedoch nur begrenzte Agent-/Chat-Nutzung. GitHub Free enthält außerdem 120 Codespaces-Kernstunden und 15 GB Speicher pro Monat für persönliche Konten.

## Start im Browser

1. GitHub öffnen und `DWR-debug/trading-agent-public` aufrufen.
2. **Solange PR #186 noch nicht gemerged ist:** `Code -> Codespaces -> ...` und den Branch `research/copilot-hypothesis-subagent` auswählen. **Nach dem Merge:** den aktuellen `master` verwenden.
3. Einmalig anmelden: `copilot login`
4. Danach genügt für die komplette Runde der kurze Start: `bash tools/a`
5. Die Ausgabe wird als nicht-evidenzielle Research-Notiz unter `research/agent_outputs/` gespeichert.

## Rollenmodell

Der Custom Agent ist ausdrücklich nachgeordnet. `disable-model-invocation: true` verhindert automatische Delegierung; `user-invocable: true` erlaubt einen expliziten Aufruf. Seine Tools sind auf `read`, `search` und `web` begrenzt; `edit` und `execute` sind nicht freigegeben.

Die eigentliche Forschungsentscheidung bleibt beim primären Agenten. Agentenoutput ist keine Evidenz.

## Kostenkontrolle

Keine bezahlten Agenten-/API-Ausgaben aktivieren. Die CLI wird im Startskript zusätzlich auf die drei read-only Tools begrenzt und erhält ein begrenztes Autopilot-Fenster. Das Runner-Limit für AI-Credits wird nicht künstlich auf einen ungültigen Kleinwert gesetzt; die Autopilot-Fortsetzungen bleiben fest auf fünf begrenzt. Numerische Research-Arbeit bleibt lokal/deterministisch.

## Unternehmensumgebung

Die Nutzung von GitHub/Copilot/Codespaces muss mit den geltenden Firmenrichtlinien vereinbar sein.

## Empfohlener erster autonomer Lauf

Das Startskript prüft vor dem Agentenlauf:
- korrektes Repository `DWR-debug/trading-agent-public`;
- zulässigen Branch;
- `PAPER_ONLY=True`;
- `LIVE_TRADING_ENABLED=False`;
- vorhandene Copilot-CLI-Anmeldung bzw. ausführbare CLI.

Danach wird `information-hypothesis-researcher` mit begrenztem Autopilot und ausschließlich `read,search,web` gestartet. Der Agent darf weder Dateien ändern noch Shell-Befehle ausführen noch formale Trials auslösen.

Der Auftrag ist `AGENT-HYPOTHESIS-ROUND-001` auf Basis T041/T042/T044/T045 und Q011. Die erzeugte Notiz bleibt Ideenmaterial und darf keinen Holdout zur Auswahl einer Hypothese verwenden.
