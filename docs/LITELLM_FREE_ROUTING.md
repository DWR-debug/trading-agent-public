# LiteLLM in der Free-Only-Architektur

Stand 4. Oktober 2026.

LiteLLM ist in unserem System ausschließlich Transport-/Interface-Schicht. Es
ist weder Abrechnungs-Gate noch wissenschaftliche Autorität.

## Zielarchitektur

`Task Contract -> Free-Mode-Attestation -> fester Providerpfad -> LiteLLM -> Response-Sanity -> Worker Receipt`

Die Attestation kommt vor LiteLLM. Ein einheitlicher Client darf niemals einen
kostenpflichtigen Fallback oder Providerwechsel ermöglichen.

## Implementierungsstand

Die LiteLLM-Integration ist jetzt als **explizit opt-in** implementiert. Der
bestehende direkte HTTPS-/CLI-Pfad bleibt unverändert der Standard, solange

`TRADING_AGENT_LITELLM_TRANSPORT=true`

nicht gesetzt ist. Damit kann die neue Schicht zunächst deterministisch
kompatibilitätsgeprüft werden, ohne den laufenden Free-only-Betrieb
still zu verändern.

Die optionale Python-Abhängigkeit ist auf `litellm==1.103.2` gepinnt. Das
Projekt-CI installiert sie nur im separaten LiteLLM-Kompatibilitätsworkflow.

## Feste Routen

| Provider | Projektmodell | LiteLLM-Modell | API-Basis |
|---|---|---|---|
| OpenRouter Free | `openrouter/free` | `openrouter/openrouter/free` | `https://openrouter.ai/api/v1` |
| Groq Free | `openai/gpt-oss-20b` | `groq/openai/gpt-oss-20b` | `https://api.groq.com/openai/v1` |
| Mistral | `mistral-small-latest` | `mistral/mistral-small-latest` | `https://api.mistral.ai/v1` |

Bei OpenRouter ist die doppelte `openrouter/`-Struktur absichtlich: Der erste
Prefix wählt in LiteLLM den OpenRouter-Provider; der Rest ist die tatsächliche
OpenRouter-Modell-ID `openrouter/free`.

Gemini bleibt bewusst außerhalb des LiteLLM-Pfads, weil der bestehende CLI-Weg
eine andere Authentifizierungs- und Entitlement-Grenze besitzt.

## Fail-Closed-Regeln

Der LiteLLM-Transport prüft weiterhin die projektinterne Free-Mode-Attestation,
die Provider-Authentifizierung und die feste Route.

Zusätzlich gilt:

- `num_retries=0`
- keine `fallbacks`
- kein Modell-Discovery
- kein Provider-Wechsel
- `paid_usage_allowed=false`
- `paid_fallback_allowed=false`
- Worker-Output bleibt `worker_output_is_scientific_evidence=false`

Fehlt die lokale LiteLLM-Installation bei aktiviertem Transport, wird der
Worker **SKIPPED** und führt keinen externen Request aus.

## Integrations-Gate

Der Commit enthält einen separaten Kompatibilitätsworkflow auf
`ubuntu-24.04` und `ubuntu-24.04-arm`. Er prüft ohne Provider-Inferenz:

- exakte Provider-/Modellstrings,
- Response-Normalisierung,
- Redaction von Secrets in Fehlern,
- keine Retries/Fallbacks,
- Verhalten bei fehlender Free-Attestation.

Erst ein erfolgreicher Kompatibilitätstest rechtfertigt die nächste Stufe:
je Provider genau ein manueller Smoke-Request. Dieser erzeugt ausschließlich
nicht-wissenschaftliche Worker-Telemetrie.

## Groq-Secret

Der korrekte Secret-Name ist exakt:

`GROQ_FREE_MODE_CONFIRMED`

Der Wert ist:

`true`

Keine Leerzeichen im Secret-Namen. Die API-Key-Secret heißt separat:

`GROQ_API_KEY`

Beide Werte werden nur als GitHub Actions Secrets gehalten und niemals in
Git, Issues, Logs oder den Chat geschrieben.

## Warum LiteLLM keine $0-Garantie ersetzt

LiteLLM kann Budgets und Kosteninformationen verwalten, aber diese Funktion
ersetzt keine harte Free-only-Zulassungsgrenze. Unsere $0-Policy bleibt daher
an feste Provider-Routen, explizite Attestations und fail-closed Verhalten
gebunden.

LiteLLM ist damit eine Vereinheitlichung des Transports, nicht eine
Änderung der wissenschaftlichen oder finanziellen Autorität des Trading Agent.
