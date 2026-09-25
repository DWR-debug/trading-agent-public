# Copilot-Unteragent in GitHub Codespaces

## Ziel

Der Repository-Setup stellt einen kostenfreien, schreibgeschützten Copilot-Unteragenten für Hypothesenforschung bereit.

Aktuell enthalten persönliche GitHub-Free-Konten 120 kostenlose Codespaces-Stunden pro Monat. Copilot Free enthält Copilot CLI und 50 Chat-/Premium-Anfragen pro Monat.

## Start im Browser

1. GitHub öffnen und DWR-debug/trading-agent-public aufrufen.
2. Code -> Codespaces -> neuen Codespace auf dem aktuellen master öffnen.
3. Im Terminal prüfen: copilot --version
4. Anmeldung: copilot login
5. Im Copilot-CLI-Dialog /agent verwenden und information-hypothesis-researcher auswählen.
6. AGENT-HYPOTHESIS-ROUND-001 aus docs/AGENT_HYPOTHESIS_RESEARCH.md ausführen.

## Rollenmodell

Der Custom Agent ist ausdrücklich nachgeordnet. infer: false verhindert automatische Delegierung an ihn. Seine Tools sind auf read, search und web begrenzt; edit und execute sind nicht freigegeben.

Die eigentliche Forschungsentscheidung bleibt beim primären Agenten. Agentenoutput ist keine Evidenz.

## Kostenkontrolle

Keine bezahlten Budgets aktivieren. Numerische Research-Arbeit bleibt lokal/deterministisch.

## Hinweis

Die Nutzung von GitHub/Copilot in einer Unternehmensumgebung muss mit den geltenden Firmenrichtlinien vereinbar sein.

## Empfohlener erster autonomer Lauf

Nach der Anmeldung im Codespace kann die erste Runde direkt mit begrenztem Autopilot gestartet werden:

    copilot --agent information-hypothesis-researcher --autopilot --max-autopilot-continues 5 -p "Execute AGENT-HYPOTHESIS-ROUND-001. Use frozen T041/T042/T044/T045 and Q011 evidence. Generate multiple orthogonal hypotheses, competing explanations, falsification criteria, required data, point-in-time rules, confounders, and minimal deterministic preflights. Do not modify files, execute commands, select on holdout data, change gates, or trigger performance trials. Return a compact research memo for the primary research agent."

Der Agent kann dadurch mehrere Denkschritte autonom abarbeiten, ohne dass wir ihm Schreib- oder Shell-Rechte geben. Die Begrenzung auf fünf Fortsetzungen verhindert unnötig lange Läufe.
