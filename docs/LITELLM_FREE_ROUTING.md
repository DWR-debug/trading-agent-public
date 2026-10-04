# LiteLLM in der Free-Only-Architektur

Stand 4. Oktober 2026.

LiteLLM ist für uns sinnvoll als Transport-/Interface-Schicht, nicht als
Abrechnungs- oder Wissenschafts-Gate. Die offizielle Dokumentation beschreibt
eine einheitliche completion()-Schnittstelle für 100+ LLMs.

## Zielarchitektur

Task Contract -> Free-Mode-Attestation -> fester Providerpfad -> LiteLLM
(optional) -> Response-Sanity -> Worker Receipt

Die Attestation muss vor LiteLLM passieren. Ein vereinheitlichter SDK-Aufruf
darf niemals bedeuten, dass ein kostenpflichtiger Fallback zugelassen wird.

## Aktuelle Entscheidung

Die bestehenden direkten Adapter bleiben der sichere Standardpfad:

- OpenRouter: fester openrouter/free-Router.
- Mistral und Groq: feste provider-spezifische HTTPS-Adapter.
- Gemini: vorhandener CLI-Pfad.
- LiteLLM zunächst nicht als stiller Ersatzpfad aktivieren.

Damit vermeiden wir eine ungeprüfte Änderung des laufenden Free-only-Pfads.
Insbesondere wird kein unbestätigter LiteLLM-Modellname für openrouter/free
erfunden.

## Warum LiteLLM nicht die $0-Garantie liefert

LiteLLM kann Kosteninformationen und Budgets verwenden. Die aktuelle
Dokumentation weist ausdrücklich darauf hin, dass Budgets auf einem DB-losen
Proxy nicht erzwungen werden; max_budget kann dort fail-open bleiben.

Für eine harte $0-Policy brauchen wir daher weiterhin:
feste Providerroute + Free-Mode-Attestation + fail-closed Routing.

## Integrations-Gate

Erst nach einem deterministischen Kompatibilitätstest pro Provider wird LiteLLM
als gemeinsamer Transport zugeschaltet. Der Test muss mindestens prüfen:

- exakten Provider-Modellstring,
- Response-Normalisierung,
- kein paid fallback,
- kein unkontrolliertes Retry auf einen anderen Provider,
- gleiche Worker-Sicherheitsflags,
- identisches Verhalten bei fehlender Free-Attestation.

Bis dahin ist LiteLLM ein geplanter Transport-Layer und keine neue finanzielle
oder wissenschaftliche Autorität.
