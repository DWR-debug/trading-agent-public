# Free-Mode-Attestation

Stand 4. Oktober 2026.

## Zweck

Die Attestation ist ein Admission Gate, keine Behauptung, dass GitHub den
Abrechnungsstatus des Providers automatisch verifiziert. Vor einem externen
AI-Request müssen drei Dinge gleichzeitig gelten:

1. Der Provider muss explizit als externer Free-Provider erlaubt sein.
2. Es muss der feste Provider-/Modellpfad verwendet werden.
3. Bei Providern mit kontobezogenem Free-Tier muss der Operator den aktuellen
   Free-Tier-Status ausdrücklich bestätigen.

Ein API-Key allein beweist keinen Free-Tier-Status. Besonders bei Groq ist das
wichtig, weil derselbe Modellname auch in einer kostenpflichtigen Developer-
Schiene verwendet werden kann.

## Einmalige Einrichtung in GitHub

Im Repository DWR-debug/trading-agent-public:

Settings -> Secrets and variables -> Actions -> New repository secret

Für Groq:

- Name: GROQ_FREE_MODE_CONFIRMED
- Wert: true

Danach nur dann setzen, wenn im Groq-Konto tatsächlich der Free Plan aktiv ist
und kein bezahlter Fallback genutzt werden soll.

Analog gelten:
- MISTRAL_FREE_MODE_CONFIRMED=true
- GEMINI_FREE_MODE_CONFIRMED=true

für die jeweiligen Provider, nachdem der aktuelle Free-Modus im jeweiligen
Konto überprüft wurde.

Nie API-Keys, Registration Tokens oder Secret-Werte in den Chat schreiben.

## Software-Gate

automation/free_mode_attestation.py prüft Allowlist, Provider-Authentifizierung,
Free-Mode-Bestätigung und den festen Modellpfad. Fehlt eines davon, bleibt der
Worker fail-closed.

OpenRouter ist davon getrennt: Der feste openrouter/free-Router ist laut
aktueller OpenRouter-Dokumentation ein kostenfreier Router mit $0 Prompt- und
Completion-Preis. Deshalb braucht dieser Pfad kein zusätzliches konto-
tierbezogenes Secret.

## Grenzen

Die Attestation ist eine explizite Betreibererklärung. Sie ist keine
automatische Abrechnungsprüfung des Providers. Genau deshalb bleiben feste
Free-Routen, kein paid fallback und fail-closed Verhalten zusätzlich zwingend.
