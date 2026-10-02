# Trading Agent OS — Persistent Orchestration

Stand: 2026-10-01

## Zweck

Dieses Dokument ist der dauerhafte Orchestrierungsvertrag des Trading-Agent-OS. Es hält fest, welche Arbeit ohne offenen Chat selbstständig weiterlaufen soll und welche Fragen im Chat verbleiben.

## 1. Grundarchitektur

Das OS arbeitet nach dem Prinzip: verfügbar + unabhängig + zulässig + sinnvoll ⇒ ausführen.

Bereits laufende Arbeit wird nicht dupliziert. Kostenlose Ressourcen werden nicht künstlich verbraucht. Wissenschaftliche Wahrheit entsteht nur über deterministische Forschung, formale Preregistration, PIT-/Coverage-Gates und unveränderliche Receipts.

AI- und Coding-Agenten dürfen Forschung technisch beschleunigen, aber weder Holdouts auswählen noch Parameter, Assets oder Horizonte nachträglich optimieren, Performance autorisieren, Kandidaten promoten oder Live-Trading auslösen.

## 2. Dauerbetrieb ohne Chat

| Lane | Taktung | Zweck | Fallback |
| --- | --- | --- | --- |
| Permanent Self-Hosted Research Loop | alle 30 min | Frontier-QA + lokale Reproduktion | Hosted Research Failover |
| Hosted Research Failover | alle 30 min | nur bei stale Self-Hosted Heartbeat | keiner |
| Unified Research Orchestrator | täglich 03:30 UTC | Beobachtung + bounded Preflight | GitHub-hosted |
| Free AI Worker Fabric | alle 6 h | adversariales Design/Review | Provider fail-closed überspringen |
| Bounded Agent Queue | alle 2 h | begrenztes Engineering | Queue bleibt liegen |
| Self-hosted Capacity Probe | alle 6 h | Runner-/Kapazitätsprüfung | keiner |
| Evidence-Critic Lab | event-/dispatch-basiert | 36-Fälle Evidence-Critic Benchmark | Ressourcen-/Runtime-Gate |

Diese vorhandene Taktung deckt den Nachtbetrieb bereits ab. Eine zusätzliche redundante Nachtpipeline wird deshalb nicht erzeugt.

## 3. Nachtmodus

Die primäre Nachtspur ist der bestehende 30-Minuten-Self-Hosted-Zyklus. Er startet automatisch auf dem Label trading-agent-research, führt ausschließlich bounded QA, Reproduktion und Frontier-Diagnostik aus und schreibt Run-Manifeste sowie SHA-256-Provenienz in die Actions-Artefakte.

Wenn der Self-Hosted-Heartbeat ausbleibt, übernimmt die bestehende Hosted-Failover-Spur automatisch bounded Frontier-/Governance-Diagnostik. Damit entsteht keine Forschungspause allein deshalb, weil der Arbeits-PC ausgeschaltet oder der Runner offline ist.

Das tägliche 03:30-UTC-Fenster vertieft die Beobachtungs-/Preflight-Arbeit. AI-Rotationen laufen separat und dürfen nur als Design-/Review-Hilfsmittel wirken.

## 4. Aktuelle Forschungspriorität

Q116 und Q117 sind als Feasibility-/Population-Spuren abgeschlossen. Als nächstes werden I22 Filing-Arrival sowie ein deterministischer XBRL-Concept-/Coverage-Gate für I19/I20 verfolgt. Parallel wird das Evidence-Critic Lab zur ersten belastbaren Modellmetriken-Auswertung gebracht.

Es bleibt bei keiner Performance-Freigabe, solange die vollständige Coverage/PIT/Authorization-Kette nicht formal erfüllt ist.

## 5. Ressourcenrouting

Die beiden verifizierten Windows-Runner LHT-N133732 und LHT-N133732-2 arbeiten unter dem Label trading-agent-research. Ihr Live-Status ist flüchtig und wird deshalb in jedem neuen trading agent-Chat neu geprüft.

Copilot Free wird geschützt behandelt: höchstens eine tatsächliche parallele Session, begrenztes monatliches Reservierungslimit, keine Paid-Fallbacks. ECL- und deterministische Research-Jobs konkurrieren nicht um Copilot-Credits.

Gemini, Mistral und OpenRouter laufen nur bei nachgewiesener kostenloser Zugänglichkeit. Quota-/Auth-Fehler werden als Ressourcenstatus behandelt, nicht als wissenschaftlicher Fehler.

## 6. Samsung/Android-Ressourcentemplate

Für weitere Samsung-/Android-Telefone wird `docs/ANDROID_SAMSUNG_RUNNER_TEMPLATE.md` zusammen mit `research/devices/android_phone_profile_template.json` und den beiden `scripts/android_samsung_runner_*_template.sh` verwendet. Neue Telefone starten grundsätzlich als unverified; erst Capability- und Utility-Receipt schalten bounded Routing frei. S10 bleibt die Referenzimplementierung.

## 6. Neuer trading agent-Chat

Ein neuer Chat soll diesen Vertrag zuerst lesen und anschließend den Live-Status aktualisieren. Vergangene Runner-, Auth-, Queue- und Workflow-Angaben sind niemals autoritativ.

Der Chat soll danach vor allem die Arbeit übernehmen, die online nicht sinnvoll oder nicht zulässig autonom fortgeführt werden kann: strategische Priorisierung, Interpretation neuer Evidenz, Umgang mit widersprüchlichen Ergebnissen und wichtige Freigabeentscheidungen.

Bereits erteilte technische Freigaben gelten weiter; redundante Bestätigungsfragen sind nicht erforderlich.

## 7. Unveränderliche Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

Diese Invarianten gelten auch im Nachtbetrieb und für jeden Unteragenten.

## 8. Verbindliche Quellen

Die maschinenlesbare Version dieses Zustands ist ops/trading_agent_os_state.json.
Der aktuelle operative Zustand bleibt research/evidence/current_operational_state.json.
Der Chat-Einstiegspunkt bleibt docs/TRADING_AGENT_CHAT_ENTRYPOINT.md.
