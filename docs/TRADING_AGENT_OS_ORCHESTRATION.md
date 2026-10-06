> **KANONISCHES PROJEKTSTATUT:** `docs/TRADING_AGENT_PROJECT_STATUTES.md`. Jede Orchestrierungsentscheidung folgt der dort festgelegten Nutzkapazitäts-, Kontinuitäts- und Anti-Scheinbeschäftigungs-Regel.

# Trading Agent OS — Persistent Orchestration

Stand: 2026-10-06

## Zweck

Dieses Dokument ist der dauerhafte Orchestrierungsvertrag des Trading-Agent-OS. Es hält fest, welche Arbeit ohne offenen Chat selbstständig weiterlaufen soll und welche Fragen im Chat verbleiben.

## 1. Grundarchitektur

Das OS arbeitet nach dem Prinzip: verfügbar + unabhängig + zulässig + sinnvoll ⇒ ausführen.

Bereits laufende Arbeit wird nicht dupliziert. **Nach Abschluss einer Forschungsrunde darf und soll das OS die logisch folgende, durch die Ergebnisse bestimmte Runde automatisch starten**, sofern deren Eingangsgates erfüllt sind und keine identische Runde bereits läuft. Der nächste Lauf muss eine neue, klar abgegrenzte Trial-/Candidate-Identität besitzen und darf keine abgeschlossenen Ergebnisse rückwirkend verändern. Kostenlose Ressourcen werden nicht künstlich verbraucht. Wissenschaftliche Wahrheit entsteht nur über deterministische Forschung, formale Preregistration, PIT-/Coverage-Gates und unveränderliche Receipts.

AI- und Coding-Agenten dürfen Forschung technisch beschleunigen, aber weder Holdouts auswählen noch Parameter, Assets oder Horizonte nachträglich optimieren, Performance autorisieren, Kandidaten promoten oder Live-Trading auslösen.


## 2aa. Permanent capacity-saturation and rolling-wave rule

The OS treats useful compute capacity as a continuously schedulable research resource, not as a one-off burst. Whenever a free, reachable and independent worker exists and a bounded useful backlog exists, the OS routes the highest-priority ready task to it. Ideal utilization means maximum useful occupancy subject to scientific gates, dependency order, runner health and duplicate-work prevention—not artificial quota consumption.

For bounded multi-step research, the standing wave order is: W1 source/PIT/clock closure -> W2 candidate/contracts and information timing -> W3 next-gate compilation and independent reproduction -> W4 discovery/consolidation. The current two-hour activation is declared in research/run_requests/rolling_capacity_window_2026-10-05.json and polled every 10 minutes by .github/workflows/capacity-saturation-rolling-waves.yml.

Each scheduler pulse must skip active duplicate work, skip a phase task already completed successfully in that phase, permit at most one bounded retry after failure/cancellation, prefer the smallest suitable free resource, and preserve downstream fail-closed gates.

Permanent background capacity remains active outside the window: Windows A/B and hosted frontier loops on their existing 10-minute cadence, with event-driven completion replenishment so a successful bounded lane is immediately refilled; Runner C chains its prepared long-workpack dependencies when executable; S10/mobile QA and the free AI fabric remain bounded and entitlement-gated.

**USEFUL-CAPACITY STATUTE:** Es darf keine künstliche Arbeit erzeugt werden. Ausschließlich wertvolle und hilfreiche Rechenarbeit darf ausgeführt werden. Und das so viel wie möglich. A reachable free runner with a real independent bounded backlog must be replenished immediately after completion rather than waiting for the next scheduled pulse. Idle is acceptable only when no useful executable work exists, a dependency is genuinely blocked, a higher-priority run owns the resource, or a hard platform/quota constraint prevents execution.

This capacity rule never creates scientific authority. Performance, holdout selection, ranking, tuning, promotion and live execution remain closed unless the independent existing governance chain authorizes them.

## 2ab. Top-4 automatic capacity routing — 2026-10-06

The automatic research dispatcher for the active four-candidate wave is `.github/workflows/top4-candidate-research-capacity.yml`. It routes bounded workpacks for **Q218/Q219/Q220/Q221** across three self-hosted Windows slots, GitHub-hosted x64 and hosted ARM64. Legacy broad frontier loops remain manual-only and are not used as filler work.

Each matrix job binds checkout to `github.sha`, records the candidate-specific workpack contract and gate paths, and uses stale-run cancellation so a new source/PIT gate state supersedes obsolete work. Free AI reviews are task-local and non-authorizing.

The candidate routing is deliberately orthogonal:
- Q218: SEC multichannel source/event pairing and acceptance lineage.
- Q219: options source breadth, Q129 PIT and post-filing leakage.
- Q220: as-filed XBRL/FSN schema and narrative-structured mapping.
- Q221: USAspending public-observation clock and agency-specific exceptions.

No automatic Top-4 dispatcher step performs performance, ranking, tuning, holdout selection, promotion or live execution.

## 2ab. Top-candidate development overlay — 2026-10-05
### Q222 design-only extension — 2026-10-05

Q222 — **Technology disclosure–verification credibility gap** — is admitted as an unranked design candidate based on current literature. Its proposed mechanism compares as-filed technology claims with independently observable implementation evidence. It is explicitly merge-or-kill against Q220/Q217/Q211: no separate family survives unless external verification provides an empirically distinct information mechanism and a defensible historical public-observation clock. No performance, holdout selection, ranking, tuning, promotion or live execution is authorized.



The permanent capacity loop now carries an explicit top-candidate overlay so that newly developed mechanisms are not left idle merely because the older frontier rotation has already passed them.

Priority order for the current design-only wave:
1. Q218 — mandatory/voluntary disclosure semantic wedge.
2. Q220 — narrative/structured XBRL representation gap.
3. Q221 — government R&D to procurement-option-value state.
4. Q219 — filing-change × options-response information-processing wedge.

Windows A / Formal Readiness receives inherited-source consistency, PIT-contract and provenance audits for these candidates while continuing current Q121-R6 / Q104 / Q119-Q122 readiness work. Windows B / Frontier Discovery receives deterministic source/census work for SEC/EDGAR, SEC Financial Statement and Notes datasets, historical SEC files and USAspending. Runner C handles long deterministic next-gate and independent-QA work when its long-run slot is free, and advances through the prepared RC-LONG workpack chain without artificial runtime padding.

A top-candidate overlay may advance only source/PIT/structure readiness. It must fail closed when a historical public clock, identity mapping, revision lineage or deterministic feature definition cannot be proven. Literature-derived mechanisms do not become project evidence merely because a paper reports an effect.

This overlay is a routing rule, not a scientific ranking rule. It does not authorize performance, holdout selection, threshold or parameter search, asset selection, promotion or live execution.

## 2ac. Knowledge Relation Plane — 2026-10-06

The OS now maintains a deterministic **Knowledge Relation Plane** in
`research/governance/knowledge_relation_graph_contract_2026_10_06.json`.
It is a metadata/control-plane layer, not a strategy layer.

Its job is to connect reusable structural facts that already exist across the
project: source components, public clocks, entity maps, event anchors, state
transitions, candidate contracts, receipts and negative evidence.

The central rule is: **reuse infrastructure, never inherit conclusions**.

This creates four useful effects:

1. **Shared-component reuse:** one verified SEC clock, identity map, XBRL structure,
   options PIT chain or government-publication clock can feed several independent
   candidates without rerunning identical source work.
2. **Cross-channel alignment:** independently timestamped representations of the
   same public event can be joined for mechanism discovery — e.g. filing channel,
   structured XBRL state and post-filing options response — without treating the
   join as a composite strategy.
3. **Dependency-aware routing:** the scheduler can prioritize unresolved structural
   components that block multiple independent candidates, while remaining blind to
   performance outcomes.
4. **Negative-evidence propagation:** a failed source/clock/identity contract can
   close dependent paths until a new falsifiable route is declared, preventing
   cyclic rediscovery and wasted compute.

The deterministic materialization is
`automation/knowledge_relation_index.py`, with the current metadata snapshot in
`research/evidence/knowledge_relation_index_latest.json`.

The graph may contain explicit discovery motifs such as:
- originator public state -> independent regulatory/structured confirmation;
- public filing -> separately timestamped market/instrument response;
- public administrative state -> frozen issuer exposure;
- narrative -> structured -> market multi-representation consistency.

These motifs are hypothesis-discovery aids only. A graph edge never authorizes
performance, selects assets/parameters/holdouts, changes a frozen trial, or
creates a composite candidate. Any composition requires separate candidate
contracts and candidate-specific PIT/coverage/independent-reproduction gates.

When a shared component is refreshed, all dependent candidate lanes inherit only
the deterministic structural artifact and its provenance. Candidate-specific
semantic and scientific gates are evaluated independently.

## 2a. Persistent acceleration policy
## 2b. Permanent literature-research plane

The LITERATURE/DISCOVERY ENGINE is a permanent OS capability and must not depend on a single chat session. Its standing rule is:

SEARCH BROADLY AND CREATIVELY -> VERIFY PRIMARY EVIDENCE -> ISOLATE A GENUINELY NEW MECHANISM -> CHEAP-FALSIFY -> ASSESS PIT/DATA/REPRODUCIBILITY -> ONLY THEN OPEN A BOUNDED DISCOVERY CONTRACT.

Recurring research is mandatory: daily assistant literature radar, weekly deep research, and a free GitHub-hosted public-metadata scout every 6 hours. Search across finance, accounting, economics, market microstructure, information diffusion, corporate disclosures, networks, data revisions/vintages, innovation/patents, unusual public-domain information and forward-risk structure. Prefer mechanisms with high information-orthogonality and high information-gain-per-compute.

The literature plane must retain negative evidence (PRUNED, UNVERIFIED, DATA_INSUFFICIENT) and must not repeatedly reopen the same dead end without a new falsifiable premise. Maximum active shortlist: 4. Literature claims are source claims, not project evidence. The current frontier includes Q214 disclosure-risk, Q215 public-source observability, Q216 macro-vintage revision reliability and Q217 cognitive-processing-friction decomposition; Q217 must merge into Q131 if it is not empirically distinct.

The discovery plane is strictly quarantined from scientific authority: no performance evaluation, holdout selection, ranking, parameter/asset/threshold/horizon search, promotion or live execution may be derived from literature results. Candidate-specific PIT, coverage, independent reproduction and the existing authorization chain remain mandatory.


The acceleration contract is stored in `research/governance/persistent_research_acceleration_contract.json` and is part of the mandatory start logic for every new `trading agent` chat.

The permanent rule is:

**verify current state → snapshot live capacity → parallelize independent work → use the smallest useful free resource → cheap falsify early → expose robustness early → immediately independently replicate a complete formal pass.**

The two Windows self-hosted lanes remain the primary deterministic capacity. The permanent workflow uses lane-scoped concurrency rather than workflow-global serialization; current formal-readiness priorities follow the active registry, while data QA remains independently schedulable. They operate as **Lane A — Formal Readiness** and **Lane B — Frontier Discovery** when both slots are available. Lane A concentrates on advanced Coverage/PIT/compiler/authorization readiness; Lane B on orthogonal source/PIT feasibility, candidate contract development and cheap falsification. Each lane has separate candidate/trial identity, branches/workflows and output/provenance paths. Cross-lane results never retroactively modify a frozen trial. The autonomous hosted frontier lane uses bounded internal concurrency (default 3 workers); local reproduction and other sequential QA/reproduction paths remain serial unless explicitly proven safe to parallelize.

S10 is not a background decoration resource. When its latest successful utility receipt is fresh (currently within 6 hours), that receipt is accepted as the S10 operational-presence signal for routing. A separate phone-runner discovery is not required solely to establish presence. Bounded work remains the only permitted use. Its output remains QA/review support only.

Already-running work is never duplicated. No resource is activated merely to consume quota. Successful completion is an immediate scheduling signal; cron is a recovery path, not the primary source of continuity. Scientific evidence, performance authorization, candidate selection, promotion and live trading are unchanged.

### Mobile capacity decision rule

The existing Samsung fleet registry already provides five uniquely labelled slots. An additional physical phone is therefore **not required now**. A new device should be activated only as a controlled capacity experiment when independent measurable throughput gain is expected; recurring use requires measured benefit sufficient to justify the added operational complexity.

## 2. Permanenter Zwei-Lanes-Forschungsmodus

Der Zwei-Lanes-Modus ist ein dauerhafter Betriebsstandard und nicht chatabhängig:

| Lane | Primärer Zweck | Aktueller Schwerpunkt | Wissenschaftliche Grenze |
| --- | --- | --- | --- |
| **A — Formal Readiness** | Coverage/PIT/Compiler/Provenienz bis zur nächsten zulässigen formalen Autorisierung | Q104 I19/I20, I22, Q119/Q120/Q122, Q125-F1 | keine Autorisierung durch Kapazität; keine Selektion/Rangfolge |
| **B — Frontier Discovery** | orthogonale Quellen, PIT-Semantik, billige Falsifikation | Q171-Q178, Q126-Q132 und weitere Public-Source-Frontier | keine Performance, keine Selektion/Rangfolge |

Beide Lanes müssen Candidate-/Trial-IDs, Branches/Workflows, Receipt- und Output-Pfade getrennt halten. Ein Ergebnis darf nur als neue, separat eingefrorene Hypothese in die andere Lane einfließen. Zwei Windows-Slots sind Ausführungskapazität; sie erzeugen niemals selbst Performance-Autorisierung.

## 2a. Dauerbetrieb ohne Chat

| Lane | Taktung | Zweck | Fallback |
| --- | --- | --- | --- |
| Permanent Self-Hosted Research Loop | alle 10 min | Lane A: local reproduction / Lane B: data QA | Hosted Research Failover |
| Hosted Research Failover | alle 30 min | nur bei stale Self-Hosted Heartbeat | keiner |
| Unified Research Orchestrator | täglich 03:30 UTC | Beobachtung + bounded Preflight | GitHub-hosted |
| Free AI Worker Fabric | alle 6 h | adversariales Design/Review | Provider fail-closed überspringen |
| Bounded Agent Queue | alle 2 h | begrenztes Engineering | Queue bleibt liegen |
| Self-hosted Capacity Probe | alle 6 h | Runner-/Kapazitätsprüfung | keiner |
| S10 Phone Research Worker | alle 20 min + relevante Master-Pushes | bounded mobile Utility-Review; ECL nur gezielt | receipt-gated, fail-closed |
| S10 Throughput Probe | nur diagnostisch/manuell | isolierte lokale Kapazitätsmessung | kein Scientific Evidence Gate |
| Android Phone Fleet Worker | alle 6 h + manuell | Acceptance neuer Geräte; Utility-Review akzeptierter Geräte | receipt-gated, fail-closed |
| Evidence-Critic Lab | event-/dispatch-basiert | 36-Fälle Evidence-Critic Benchmark | Ressourcen-/Runtime-Gate |

Diese Taktung deckt den Nachtbetrieb bereits ab. Eine zusätzliche redundante Nachtpipeline wird deshalb nicht erzeugt.

## 3. Nachtmodus

Die primäre Nachtspur ist der bestehende 30-Minuten-Self-Hosted-Zyklus. Er startet automatisch auf dem Label trading-agent-research, führt ausschließlich bounded QA, Reproduktion und Frontier-Diagnostik aus und schreibt Run-Manifeste sowie SHA-256-Provenienz in die Actions-Artefakte.

Wenn der Self-Hosted-Heartbeat ausbleibt, übernimmt die bestehende Hosted-Failover-Spur automatisch bounded Frontier-/Governance-Diagnostik. Damit entsteht keine Forschungspause allein deshalb, weil der Arbeits-PC ausgeschaltet oder der Runner offline ist.

S10 ist davon getrennt: das Telefon stellt eigene ARM64/Termux-Compute bereit. Ein erfolgreicher Utility-Lauf im aktuellen Receipt-Fenster von 6 Stunden dient als Presence-Signal für das Routing; bei abgelaufenem Receipt wird fail-closed nicht geroutet.

Weitere Samsung-/Android-Telefone werden über \`ops/android_phone_resources.json\` und die Fleet-Spur geroutet. Der Planungsjob ermittelt online verfügbare, eindeutig gelabelte Runner; offline Slots erzeugen keine wartenden Forschungsjobs. Nach erfolgreicher \`ANDROID_PHONE_UTILITY_ACCEPTED\`-Acceptance darf die Ressource nur für bounded Unterstützung eingesetzt werden.

## 3a. Universeller Candidate-Robustheits-Gate

Jeder neue Kandidat durchläuft vor dem Eintritt in eine formale Phase einen strukturellen, nicht-performativen Robustheits-Gate. Geprüft werden unter anderem Konstruktionsinvarianz, Eingabereihenfolge, Zukunftsdaten-Mutation, Missingness/Fault Isolation, Revisions-/Amendment-Verhalten, Identitätsfehler, Parameter-/Threshold-/Horizon-Sperren und Quellenreproduzierbarkeit. Das Gate erzeugt einen unveränderlichen Receipt und bleibt rein deskriptiv; es autorisiert weder Performance noch Promotion. Fehlt der Receipt oder weicht sein Fingerprint vom eingefrorenen Kandidatenvertrag ab, bleibt der formale Eintritt fail-closed blockiert.

## 4. Aktuelle Forschungspriorität

Die aktuelle Frontier-Spur umfasst Q185–Q221 mit Schwerpunkt auf orthogonalen öffentlichen Informationskanälen. Q185–Q186 verfolgen Patent-/Litigation-PIT, Q187–Q192 historische Source/PIT-Rekonstruktion, Q193–Q196 die vertiefte Kandidatenentwicklung aus administrativen/regulatorischen Quellen, Q197–Q201 Government-Procurement/Federal-Register/USPTO/Clinical-Trials-Zeitgrenzen, Q202–Q204 Information-Timing, Q205 die NLRB-Quelle und Q211–Q221 die aktuelle Literatur-/Public-Source-Frontier. Der aktive Top-Candidate-Overlay ist Q218/Q220/Q221/Q219 und bleibt strikt design/source/PIT-only.

Die aktuell validierten 17 Kandidaten Q194/Q195/Q196/Q197/Q199/Q201/Q202/Q203/Q204/Q205/Q215/Q216/Q217/Q218/Q219/Q220/Q221 sind in
research/candidates/orthogonal_candidate_specs_2026-10-05.json fixiert und werden durch
.github/workflows/orthogonal-candidate-development.yml rein mechanisch validiert. Der zugehörige Receipt
ist design-/governance-only und autorisiert keinerlei Performance. Für Q218–Q221 ergänzt Windows B den historischen Source-Census durch den deterministischen Candidate-Gate-Compiler.

Lane A verfolgt parallel die bestehenden Formal-Readiness-Gates des aktiven Registers, ohne Holdout-/Asset-/Parameter-/Horizon-Selektion. Lane B verfolgt die Q179–Q201-Orthogonalspur sowie weitere Public-Source-Kandidaten.

Es bleibt bei keiner Performance-Freigabe, solange die vollständige Coverage/PIT/Authorization-Kette nicht formal erfüllt ist.

## 5. Ressourcenrouting

Die drei Windows-Runner LHT-N133732, LHT-N133732-2 und LHT-N133732-3 bilden den Self-Hosted-Pool. A/B bleiben die permanenten Forschungs-Lanes; Runner C ist als dedizierte Long-Run-/Independent-Reproduction-Kapazität mit dem Zusatzlabel trading-agent-long vorgesehen und wird nicht künstlich beschäftigt; ihr Live-Status ist flüchtig und wird bei jedem Start/Materialisierungspunkt neu geprüft. Ihr Live-Status ist flüchtig und wird deshalb in jedem neuen trading agent-Chat neu geprüft.

S10 ist eine separat verifizierte ARM64/Termux-Ressource. Ein erfolgreicher Utility-Lauf im aktuellen Receipt-Fenster von 6 Stunden dient als operatives Presence-Signal für das Routing. Eine zusätzliche Runner-Discovery ist für die bloße Präsenzbestätigung nicht erforderlich; bei abgelaufenem Receipt wird fail-closed nicht geroutet.

Weitere Samsung-/Android-Geräte sind in \`ops/android_phone_resources.json\` als getrennte Slots vorbereitet. Der generische Fleet-Worker und die Receipt-Sync-Spur halten Runner-, Runtime- und Governance-Verträge identisch.

Für weitere Samsung-/Android-Geräte gilt die generische Vorlage \`docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md\` mit dem Runner-Helper \`scripts/samsung_termux_phone_runner_template.sh\`. Neue Geräte müssen das gleiche Utility-Acceptance-Protokoll erfüllen; ein neues Modell darf keinen eigenen wissenschaftlichen Sonderpfad erzeugen.

Copilot Free wird geschützt behandelt: höchstens eine tatsächliche parallele Session, begrenztes monatliches Reservierungslimit, keine Paid-Fallbacks. ECL- und deterministische Research-Jobs konkurrieren nicht um Copilot-Credits.

Gemini, Mistral und OpenRouter laufen nur bei nachgewiesener kostenloser Zugänglichkeit. Quota-/Auth-Fehler werden als Ressourcenstatus behandelt, nicht als wissenschaftlicher Fehler.

## 6. Neuer trading agent-Chat

Jeder neue Chat, der mit `trading agent` beginnt, aktiviert diesen Vertrag als verbindlichen Orchestrierungsstandard: Vertrag und kanonischen Zustand lesen, aktuellen `master` und flüchtige Ressourcen live reconciliieren, danach ohne erneute Freigabefrage die nächstzulässige unabhängige Arbeit ausführen. Vergangene Runner-, Auth-, Queue- und Workflow-Angaben sind niemals autoritativ.

Zusätzlich wird der aktuelle S10-Receipt gegen \`ops/s10_runtime_status.json\` geprüft. Bei einem neuen Samsung-Gerät wird zuerst die generische Vorlage verwendet; erst nach Utility Acceptance darf es in das Routing aufgenommen werden.

Der Chat soll danach vor allem die Arbeit übernehmen, die online nicht sinnvoll oder nicht zulässig autonom fortgeführt werden kann: strategische Priorisierung, Interpretation neuer Evidenz, Umgang mit widersprüchlichen Ergebnissen und wichtige Freigabeentscheidungen.

Bereits erteilte technische Freigaben gelten weiter; redundante Bestätigungsfragen sind nicht erforderlich.

## 7. Unveränderliche Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

Diese Invarianten gelten auch im Nachtbetrieb und für jeden Unteragenten.

## 8. Verbindliche Quellen

Die maschinenlesbare Version dieses Zustands ist ops/trading_agent_os_state.json.\nDie Knowledge-Relation-Regel ist research/governance/knowledge_relation_graph_contract_2026_10_06.json; der aktuelle Metadaten-Index ist research/evidence/knowledge_relation_index_latest.json.
Der aktuelle operative Zustand bleibt research/evidence/current_operational_state.json.
Der Chat-Einstiegspunkt bleibt docs/TRADING_AGENT_CHAT_ENTRYPOINT.md.
Die wiederverwendbare Android-/Samsung-Integrationsvorlage ist docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md.
Die Fleet-Konfiguration ist ops/android_phone_resources.json; die Fleet-Betriebsbeschreibung ist docs/SAMSUNG_ANDROID_PHONE_FLEET.md.


## Dauerhafte Runner-Auslastungsregel — 2026-10-05

Windows Self-Hosted A und B gelten innerhalb der Projektfreigaben als dauerhaft routbare Forschungskapazität. **A = Formal Readiness / lokale Reproduktion; B = Frontier Discovery / Data-QA.** Unabhängige Arbeiten werden parallel vergeben; nach jeder Freigabe eines Slots wird der nächste sinnvolle bounded Task aus der aktuellen Frontier bzw. den formalen Readiness-Gates gezogen.

S10 ist die separate ARM64-Mobile-QA-Lane mit adaptiver mechanischer Research-QA. Der Standardpuls läuft alle 20 Minuten plus bei relevanten Research-/Governance-Änderungen und rotiert zwischen Provenance/Status, Frontier-Governance, PIT/Clock/Lineage, Capacity-Dispatch und Negative-Evidence/Dedup. Semantische Utility-/Evidence-Critic-Arbeit bleibt ausdrücklich receipt-gated.

„Forschung darf nicht stillstehen“ bedeutet: Solange mindestens eine zulässige, unabhängige und sinnvoll begrenzte Aufgabe existiert, wird sie an eine freie geeignete Ressource geroutet. Es bedeutet nicht, künstliche Jobs zu erzeugen oder wissenschaftliche Gates zu überspringen.
