# AI-to-AI orchestration — Trading Agent

Stand: 2026-09-28

## Verbindung

Ein gemeinsames Google-Konto verbindet ChatGPT und Gemini nicht technisch. Die normalen Chat-Oberflächen können nicht selbstständig einen Dialog im Hintergrund führen.

Für das Trading-Agent-Projekt verwenden wir deshalb eine repository-vermittelte Architektur:

ChatGPT/Orchestrator -> Task Contract -> GitHub -> lokaler oder gehosteter Worker -> Worker Receipt -> deterministische Prüfung

Die externen Modelle sind Worker. Ihre Antworten sind Research-Support und niemals automatisch wissenschaftliche Evidenz.

## Gemini

Googles aktuelle Gemini-CLI-Dokumentation beschreibt lokale Google-Account-Anmeldung und gecachte Credentials für spätere Headless-Aufrufe. Gleichzeitig dokumentiert Google die Ablösung des alten Gemini-Code-Assist-Individual-Zugangs einschließlich dieses CLI-Pfads ab 18. Juni 2026 zugunsten der Antigravity-Produkte. Deshalb unterstützt der lokale Projekt-Worker sowohl eine vorhandene Antigravity-CLI als auch eine verfügbare gemini-Binary und protokolliert den verwendeten Pfad.

Die lokale Einrichtungsroutine deaktiviert den persönlichen G1-Credit-Fallback ausdrücklich. Persönliche Credits dürfen niemals unbemerkt zu kostenpflichtiger Projektverwendung werden.

## Claude

Claude bleibt ein unabhängiger Provider. Eine lokale CLI-Sitzung darf nur teilnehmen, wenn kostenloser Zugriff ausdrücklich attestiert ist. Ein Anthropic-API-Key gilt nicht als Beweis für kostenlose Nutzung.

## ChatGPT-API-Grenze

ChatGPT-Abonnement und OpenAI-API-Plattform werden getrennt abgerechnet. Die Anmeldung bei ChatGPT stellt deshalb nicht automatisch kostenlose API-Nutzung bereit. Das Projekt hält das bezahlte API-Budget bei 0 USD.

## Zulässige AI-Arbeit

- ungewöhnliche und falsifizierbare Hypothesen erzeugen;
- Gegenhypothesen und adversariale Methodenreviews;
- Tests, Invarianten und Architekturideen vorschlagen;
- technische Dokumentation und Research-Design unterstützen.

Nicht delegiert werden Holdout-, Parameter-, Asset- oder Horizon-Auswahl nach Performance, Gate- oder Autorisierungsänderungen, Promotion, Live-Ausführung oder wissenschaftliche Evidenzproduktion.

Jede fachlich relevante Aussage muss anschließend unabhängig durch deterministische Projektprüfungen und die Research-Governance bestätigt werden.