# AI-to-AI Relay Protocol — Trading Agent

Stand: 2026-09-28

## Zweck

ChatGPT und externe Modelle wie Gemini/Antigravity oder Claude können nicht
durch die bloße Anmeldung mit demselben Google-Konto zu einer gemeinsamen
Chat-Sitzung verbunden werden.

Dieses Projekt verwendet deshalb einen expliziten, nachvollziehbaren Relay-
Mechanismus über das öffentliche Repository:

```
ChatGPT / Orchestrator
        |
        | bounded task
        v
ai_requests/<task>.json
        |
        v
Gemini/Antigravity oder Claude Worker
        |
        | worker receipt / handoff
        v
ops/ai_worker_state/<task>__<provider>.json
        |
        v
ChatGPT / Orchestrator
        |
        | deterministic verification / next bounded task
        v
Research / Engineering pipeline
```

## Rollen

**ChatGPT / Orchestrator**

- hält den kanonischen Projektkontext;
- klassifiziert Aufgaben;
- verteilt unabhängige Arbeit;
- bewertet Worker-Ausgaben kritisch;
- darf keine Worker-Ausgabe als Evidence übernehmen;
- steuert wissenschaftliche Gates und Governance.

**Gemini/Antigravity**

- Hypothesen;
- Gegenhypothesen;
- adversarial review;
- Research-Design;
- Architektur-/Testideen;
- technische Analyse.

**Claude**

- unabhängige Gegenprüfung;
- adversarial review;
- alternative Designansätze;
- technische Analyse, sofern der lokale Account-Zugriff ausdrücklich kostenfrei
  und für den Worker freigegeben ist.

**Deterministische Python-/Research-Runner**

- Datenberechnung;
- Backtests;
- PIT-/Coverage-Prüfung;
- statistische Validierung;
- Evidence-Erzeugung.

## Gesprächsschleifen

Eine AI-zu-AI-Schleife besteht aus separaten, identifizierbaren Arbeitsschritten,
nicht aus einer unkontrollierten Endlosschleife.

1. Der Orchestrator erzeugt eine klar begrenzte Task-Datei.
2. Ein Worker liest ausschließlich diese Task und den dafür freigegebenen
   Repository-Kontext.
3. Der Worker schreibt einen Receipt/Handoff mit Task-Fingerprint.
4. Der Orchestrator liest den Handoff.
5. Fachlich relevante Aussagen werden durch deterministische Prüfungen,
   Repository-Code oder unabhängige Quellen überprüft.
6. Erst danach kann daraus eine neue Task entstehen.

## Kein automatisches gegenseitiges Vertrauen

Ein Worker darf niemals:

- einen Holdout auswählen;
- Parameter nach Performance auswählen;
- Research-Gates ändern;
- Promotion autorisieren;
- Live-Ausführung aktivieren;
- bezahlte API-/Agentennutzung aktivieren.

AI-Output ist Arbeitsmaterial. Die wissenschaftliche Beweiskette bleibt:

```
Worker-Idee
 -> reproduzierbare Implementierung
 -> deterministischer Test
 -> PIT/Coverage
 -> formaler Research-Run
 -> Evidence-Gate
```

## Kostenregel

`paid_agent_budget_usd = 0`

`paid_api_budget_usd = 0`

Der Relay-Pfad darf keine kostenpflichtige Fallback-Nutzung aktivieren.

Gemini/Antigravity wird lokal nur mit dem bereits angemeldeten Account verwendet.
Der lokale Runner muss vor der Nutzung einen Free-only-Receipt besitzen.
Claude wird nur ausgeführt, wenn dessen lokale kostenlose Nutzung ausdrücklich
attestiert ist.

## Öffentlicher Repository-Kontext

Das Repository ist öffentlich. Worker-Handoffs dürfen daher keine privaten
Chat-Inhalte, Zugangsdaten, API-Keys, Session-Tokens oder persönlichen Geheimnisse
enthalten. Die Relay-Dateien enthalten ausschließlich projektbezogenes, zur
Veröffentlichung freigegebenes Arbeitsmaterial.

## Sicherheitsinvarianten

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `ORDERS_ENABLED=False`
- `AUTOMATIC_PROMOTION=False`
- keine automatische wissenschaftliche Promotion
- keine kostenpflichtige Nutzung

## Betriebsregel

Parallelisierung ist erwünscht, aber nur bei unabhängigen Aufgaben. Eine
workerseitige Antwort ersetzt keine deterministische Verifikation und darf
nicht direkt in die Evidence-Kette geschrieben werden.
