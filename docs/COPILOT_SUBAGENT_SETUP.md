# Copilot-Unteragent in GitHub Codespaces

## Zweck

Diese Umgebung ist für einen schreibgeschützten, nachgeordneten Forschungsspezialisten vorbereitet.
GitHub Free bietet für persönliche Konten aktuell 120 kostenlose Codespaces-Stunden pro Monat. Copilot Free bietet aktuell 50 Chat-/Premium-Anfragen pro Monat; Copilot CLI ist im Free-Tarif enthalten.

## Start

1. Im Repository DWR-debug/trading-agent-public einen Codespace öffnen.
2. Im Codespace-Terminal prüfen: copilot --version
3. Copilot mit copilot login anmelden. In Codespaces wird der Device-Code-Flow verwendet.
4. Den Agenten mit /agent auswählen: information-hypothesis-researcher.
5. Als Arbeitsauftrag die Spezifikation aus docs/AGENT_HYPOTHESIS_RESEARCH.md und die konkrete Aufgabe AGENT-HYPOTHESIS-ROUND-001 verwenden.

## Rollenmodell

Copilot ist ein nachgeordneter Hypothesen-/Review-Agent. Er darf lesen, suchen und recherchieren, aber die projektspezifische Agentdefinition hat keine Edit-/Execute-Berechtigung und infer: false verhindert automatische Delegierung an ihn.
Der übergeordnete Forschungsagent entscheidet über Präregistrierung und weitere Forschung. Agentenoutput ist keine Evidenz.

## Kostenkontrolle

Keine bezahlte API aktivieren. Keine zusätzlichen Budgets konfigurieren. Die numerische Forschung bleibt lokal und deterministisch.