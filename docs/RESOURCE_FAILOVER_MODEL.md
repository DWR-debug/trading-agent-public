# Resource Failover Model — Trading Agent

Stand: 2026-09-30

## Ziel

Der Trading Agent soll auch dann selbständig Forschungsfortschritt erzeugen, wenn die
beiden vertrauenswürdigen Windows-Self-hosted-Runner vorübergehend nicht erreichbar sind.

Der Fallback ersetzt nur die operative Rechenkapazität. Er ersetzt keine Research-Governance
und erhält dieselben Sicherheitsinvarianten.

## Normalbetrieb

1. Self-hosted Windows: lokale Reproduktion, QA, Frontier-Feasibility und lokale AI-Pfade.
2. GitHub-hosted x64/ARM64: CI, deterministische Reproduktion, formale Gegenprüfungen und parallelisierte Research-Arbeit.
3. Kostenfreie AI-Worker: Hypothesen, adversarial Review und Research-Design.

## Failover-Auslöser

Der Hosted-Failover-Workflow prüft alle 30 Minuten den Heartbeat des
Permanent Self-Hosted Research Loop.

Er schaltet auf Hosted-Failover um, wenn:
- kein Self-hosted-Heartbeat vorhanden ist;
- ein Self-hosted-Workflow länger als 25 Minuten queued/pending ist;
- oder der letzte Self-hosted-Lauf älter als 45 Minuten ist.

Ein frischer oder laufender Self-hosted-Lauf unterdrückt den Fallback. Damit wird
normalerweise keine identische Arbeit doppelt gestartet.

## Failover-Kapazität

Bei aktiviertem Failover werden gleichzeitig verwendet:
- ubuntu-24.04 für Frontier-QA und Feasibility;
- ubuntu-24.04-arm für orthogonale Governance-/Reproduktions-QA.

Der Fallback ist cross-platform und verwendet nur vordefinierte, bounded Kommandos.
Windows-spezifische Forschung bleibt bis zur Wiederkehr der Self-hosted-Runner zurückgestellt.

## Wissenschaftliche Abgrenzung

Jeder Fallback-Lauf erzeugt formal_evidence_allowed=false,
formal_research_evidence=false und fallback_only=true.

Der Fallback darf nicht:
- Performance autorisieren;
- Holdout- oder Kandidatenselektion durchführen;
- Parameter, Assets, Horizons oder Thresholds anhand beobachteter Ergebnisse auswählen;
- Gates verändern;
- Live-Trading auslösen;
- Paid-Ressourcen aktivieren.

Die Artefakte dienen als QA-/Feasibility- und Research-Input und werden nicht als formale
Performance-Evidence ausgegeben.

## Wiederanlauf

Sobald der Self-hosted Heartbeat wieder frisch ist, stoppt der Hosted-Failover automatisch.
Die nächsten regulären Self-hosted Läufe werden wieder normal zugestellt.

## Chat-Unabhängigkeit

Der Failover-Mechanismus ist vollständig workflow-basiert. Ein offener Chat ist weder für
die Aktivierung noch für die Beendigung erforderlich.