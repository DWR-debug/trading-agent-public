# External AI Worker Setup — Trading Agent

Stand: 2026-09-28

## Gemini

Bevorzugt denselben persönlichen Google-Account verwenden, den der Benutzer auch
für Gemini-Dienste nutzt. Eine direkte Kontoverknüpfung mit ChatGPT besteht jedoch
nicht; die technische Brücke ist das Repository bzw. die jeweilige lokale/CI-
Authentifizierung.

Für lokale Gemini CLI-Nutzung:
1. auf dem persistenten Windows-PC `gemini` starten;
2. `Login with Google` wählen;
3. mit dem gewünschten persönlichen Google-Konto anmelden;
4. die Authentifizierung lokal im Runner-Benutzerprofil bestehen lassen.

Gemini CLI dokumentiert Google-Login und die Nutzung gecachter Credentials für
spätere Headless-Aufrufe.

Für GitHub-hosted Headless-Worker ist der lokale Browser-Login nicht ausreichend.
Dort muss ein separates Gemini-Credential über GitHub Secrets bereitgestellt
werden. Bevorzugt wird ein ausdrücklich kostenfreier Gemini-API-Zugang; das
Projekt akzeptiert einen Provider nur nach dem eigenen Free-Mode-Preflight.

## Claude

Claude wird separat authentifiziert. Das Claude-Konto ist unabhängig vom Google-
Konto. Claude Code unterstützt `claude -p` für nicht-interaktive Ausführung und
maschinenlesbares JSON.

Eine Anthropic-API-Nutzung ist für dieses Projekt wegen `paid_api_budget = 0`
nicht vorgesehen. Claude wird nur genutzt, wenn bereits ein ausdrücklich
kostenfreier Zugang für die CLI vorhanden ist.

## GitHub Secrets

Keine API-Keys oder Session-Credentials in Git, Issue-Texten, AI-Tasks oder
Dokumentationsdateien speichern.

Der aktuelle AI-Worker kann folgende geschützte Werte verwenden:
- `AI_EXTERNAL_PROVIDER_ALLOWLIST`
- `GEMINI_API_KEY` oder `GOOGLE_API_KEY`
- `GEMINI_FREE_MODE_CONFIRMED`
- `CLAUDE_FREE_MODE_CONFIRMED`

Fehlt der Free-Mode-Nachweis, wird der Worker mit `SKIPPED` beendet und es
entsteht kein Paid-Fallback.

## Copilot Free

Copilot Free bleibt separat behandelt. Der monatliche Credit-Zähler wird laut
GitHub am 1. jedes Monats um 00:00 UTC zurückgesetzt.

Projektinterne Schutzkappe:
- Freigabe ab 2026-10-01T00:00:00Z
- 4 Session-Reservierungen pro Monat
- maximal 12 AI credits pro Session
- nur 1 paralleler Copilot-Worker
- keinerlei Overages oder Zukäufe

Die Grenzen sind konservative Projektregeln und keine Behauptung über die exakte
aktuelle Größe des Copilot-Free-Kontingents.