# Free-Mode-Attestation — Trading Agent OS

## Zweck

Die Free-Mode-Attestation ist eine zusätzliche **Kosten-/Entitlement-Schranke** für externe AI-Provider. Sie ist keine wissenschaftliche Evidenz und darf keine Research-Gate-Entscheidung treffen.

Ein Provider darf nur ausgeführt werden, wenn

`Provider-Zugang vorhanden` + `Free-Mode ausdrücklich attestiert` + `fester kostenloser Modell-/Routingpfad` + `Paid Usage verboten`

gleichzeitig erfüllt sind.

## Groq

Der aktuelle Groq-Worker ist bereits fail-closed gegen fehlende Attestation. Er verlangt:

- `GROQ_API_KEY`
- `GROQ_FREE_MODE_CONFIRMED` mit einem wahrwertigen Wert
- `ops/groq_free_preflight.json` mit `status=PASS`
- `free_only=true`
- `paid_usage_allowed=false`

Die GitHub-Workflow-Prüfung gibt bei fehlender Attestation **keinen API-Call frei**.

### Was noch fehlt

Die aktuell verifizierte Repository-Datei zeigt:

`status=NOT_CONFIGURED`
`api_key_present=false`
`free_mode_attested=false`
`paid_usage_allowed=false`

Damit ist Groq derzeit korrekt **gesperrt**.

Die fehlende Attestation muss einmal operatorseitig aus der tatsächlichen Groq-Account-Situation bestätigt und als GitHub Actions Secret `GROQ_FREE_MODE_CONFIRMED` hinterlegt werden. Das Repository darf Tokens oder Secrets nicht speichern.

Die vorhandene GitHub-Verbindung kann Repository-Inhalte und Actions prüfen, stellt aber keine GitHub-Secrets-API zum sicheren Setzen dieses Secrets bereit. Dieser einzelne Secret-Schritt muss daher in GitHub selbst erfolgen.

## Empfohlene Attestation

Als Wert reicht ein nicht-sensitives Wahr-Signal wie:

`true`

Die Semantik ist: **Der Betreiber bestätigt, dass dieser Worker ausschließlich das dokumentierte kostenlose Groq-Kontomodell verwendet und keine bezahlte Nutzung autorisiert ist.**

Das Secret ist keine Bezahlung und keine API-Berechtigung. Die eigentliche technische Schranke bleibt im Worker bestehen.

## LiteLLM

LiteLLM eignet sich sehr gut als einheitliche Adapter-/Gateway-Schicht: Die aktuelle LiteLLM-Dokumentation beschreibt eine gemeinsame OpenAI-kompatible Schnittstelle für 100+ Provider; der Proxy unterstützt außerdem Model Groups, Aliase, Routing und Load-Balancing. citeturn473219search0turn473219search1turn473219search6

LiteLLM **ersetzt die Free-Mode-Attestation nicht**. Ein einheitlicher Client kann sonst leicht einen kostenpflichtigen Fallback erreichen. Deshalb muss die Architektur sein:

`Trading-Agent Free Gate -> erlaubter Provider/Modellpfad -> LiteLLM-Adapter -> Inference`

nicht:

`LiteLLM -> beliebiger Provider/Fallback -> erst danach Kostenprüfung`

Für OpenRouter ist `openrouter/free` aktuell ausdrücklich als kostenloser Router dokumentiert; die Free-Plan-Seite nennt API-Zugang und kostenlose Modelle, bei zugleich separaten Rate Limits. citeturn672935search3turn672935search1

Für Groq dokumentieren die aktuellen Unterlagen einen separaten Free Plan mit eigenen Rate Limits; Upgrades auf den Developer Tier führen dagegen in einen kostenpflichtigen Tarif. Deshalb bleibt für unseren OS-Vertrag die explizite Operator-Attestation zusätzlich sinnvoll. citeturn913245search0turn672935search8

## Sicherheitsregel

Keine Attestation -> kein externer AI-Call.

Unklare Abrechnung -> kein externer AI-Call.

Provider-Fallback auf einen möglicherweise kostenpflichtigen Pfad -> verboten.

AI-Ausgabe -> niemals wissenschaftliche Evidenz oder Autorisierung.
