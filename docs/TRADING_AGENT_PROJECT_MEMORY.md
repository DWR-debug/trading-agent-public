> **VERBINDLICHE PROJEKTSTATUTEN:** `docs/TRADING_AGENT_PROJECT_STATUTES.md` ist die kanonische sprachliche Regelung für dauerhafte Prinzipien, Nutzkapazität, Kontinuität und Projektgedächtnis. Maschinenmirror: `research/governance/project_statutes.json`.

## Kanonische Startregel für neue "trading agent"-Chats — 2026-09-28

Diese Datei `docs/TRADING_AGENT_PROJECT_MEMORY.md` ist die **kanonische dauerhafte Gedächtnis- und Betriebsdatei** des Projekts. Bei jedem neuen Chat, dessen erste substanzielle Nutzernachricht den Trigger **"trading agent"** enthält oder eindeutig auf das Trading-Agent-Projekt verweist, muss diese Datei vor der Auswahl oder Ausführung des nächsten Entwicklungsschritts berücksichtigt werden.

Verbindliche Reihenfolge:
1. aktuellen öffentlichen Repository-Stand `DWR-debug/trading-agent-public` prüfen;
2. diese Gedächtnisdatei aus dem aktuellen `master` lesen;
3. aktuelle Runner-/Workflow-/Evidence-Zustände prüfen;
4. erst danach planen, ändern oder Forschung ausführen.

GitHub-/Repository-Zustand hat Vorrang vor veralteten Chatannahmen. Diese Datei ist dabei die dauerhafte Projektbeschreibung für Ziel, Sicherheitsgrenzen, Ressourcenmodell, PC-/Cloud-Betrieb, Dringlichkeit, Forschungsmodus und Arbeitsweise.

# Trading-Agent Projektgedächtnis — Ziel, 30-Tage-Meilenstein und Mutkurve

Stand: 2026-09-28

## Historischer Kontext und Deadline

Aus dem verfügbaren Chat-Kontext ist eine **30-Tage-Kadenz für das erste vorzeigbare Ergebnis** belastbar erkennbar. Ein ursprüngliches absolutes Startdatum bzw. eine historische Deadline konnte in den aktuell gespeicherten Projektdateien jedoch nicht zweifelsfrei rekonstruiert werden.

Deshalb wird ab **2026-09-25** ein neuer, eindeutig überprüfbarer Meilenstein verankert:

**FIRST_PRESENTABLE_RESULT_DEADLINE: 2026-10-25**

Das ist ausdrücklich eine neue, saubere Ausführungsbaseline und keine nachträglich behauptete historische Deadline.

## Definition des ersten vorzeigbaren Ergebnisses

Bis spätestens 2026-10-25 soll mindestens ein reproduzierbarer, präsentierbarer Evidence-Pack abgeschlossen sein. Erfolg bedeutet nicht zwingend ein positives Trading-Ergebnis.

Akzeptable Formen:

1. Ein formal zulässiger Fixed-Rule-Trial erreicht Coverage, formale Evaluation und die unveränderten Robustheits-/Risk-/Control-Gates.
2. Oder: Ein Kandidat wird durch belastbare DATA_INSUFFICIENT-/NO_SUPPORT-Evidence ausgeschlossen und die verbleibende Forschungsfrage wird dadurch messbar enger.
3. In beiden Fällen müssen Provenienz, Kostenvertrag, Fingerprints, Gates und Sicherheitsstatus nachvollziehbar sein.

Nicht akzeptabel als "Ergebnis":
- einzelner schöner Backtest;
- nachträgliche Holdout-Auswahl;
- Parameter-/Asset-/Horizon-Tuning nach Beobachtung;
- Gate-Lockerung;
- implizite Live-Promotion.

## Mutkurve

"Mut" bezeichnet hier **Entscheidungs- und Entwicklungsbereitschaft**, nicht eine Wahrscheinlichkeit künftiger Rendite.

Der Mut steigt bewusst exponentiell, aber nur wenn die entsprechende Evidenzstufe erreicht wurde. Mehr Mut bedeutet daher mehr Exploration, schnellere Umsetzung und breitere Ressourcennutzung — niemals lockerere wissenschaftliche Standards.

| Stufe | Mut-Multiplikator | Trigger |
|---|---:|---|
| M0 | 1x | Infrastruktur/Prozess noch nicht verifiziert |
| M1 | 2x | reproduzierbare CI, State-Freshness und Governance |
| M2 | 4x | erste orthogonale Hypothesen vollständig präregistrierbar |
| M3 | 8x | reproduzierbare positive/negative Mechanismusevidence auf disjunkten Daten |
| M4 | 16x | mindestens ein vollständiger Fixed-Rule-Trial besteht die formalen Robustheits-/Risk-Gates |
| M5 | 32x | stabile Paper-Forward-Evidence mit Kosten-/Slippage-Accounting |
| M6 | 64x | separate Real-Capital-Readiness-Governance bestanden |

**Aktuelle operative Mutstufe: M2 / 4x.**

Begründung:
- Die Forschungsinfrastruktur und Governance sind weitgehend reproduzierbar.
- Q017 besitzt drei klar getrennte, präregistrierbare Kandidatenfamilien.
- Es gibt bislang keinen Trial, der den vollständigen Evidence-Vertrag erfüllt.
- Q016 war DATA_INSUFFICIENT.

## Mut-Regel

Der Mut darf bei jedem bestandenen Gate verdoppelt werden. Er darf niemals durch ein positives, aber unvollständiges Backtest-Signal erhöht werden.

Daraus folgt:
**Mut wächst exponentiell; Beweislast wächst mindestens entsprechend.**

## Nächste operative Ziele bis 2026-10-25

- G1: aktuelle CI-/State-Basis stabilisieren.
- G2: Q017-Design vollständig governbar machen.
- G3: Coverage-first für die Q017-Kandidaten durchführen.
- G4: den formal zulässigen Kandidaten anhand der Governance-Regeln bestimmen, ohne Holdout-Selektion.
- G5: mindestens einen vollständigen Fixed-Rule-Evidence-Versuch durchführen, sofern Coverage dies erlaubt.
- G6: resultierendes Ergebnis präsentieren; positiv, neutral, DATA_INSUFFICIENT oder NO_SUPPORT sind wissenschaftlich zulässige Resultatklassen.

## Sicherheitsbindung

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False

2000 EUR ist ab 2026-09-27 das Referenz-/Startkapital für neue Paper-/Shadow-/Income-Simulationen; daraus wird keine Prognose über spätere Rendite oder finanzielle Versorgung abgeleitet. Der bisherige 500-EUR-Operational-Canary bleibt als historische, getrennte Simulation erhalten.

## Kausales Dringlichkeits- und Erfolgsdruckmodell

Die familiäre Dringlichkeit und das aktuell fehlende verfügbare Kapital sind ein **relevanter Projektmotivator und zugleich ein methodischer Risikofaktor**.

Die dauerhaft festgehaltene Kausalkette lautet:

**familiäre Dringlichkeit + kein verfügbares Kapital**
→ **hoher wahrgenommener Erfolgsdruck**
→ erhöhte Gefahr von **Zeitdruck, Risikosuche, Overfitting, vorzeitiger Auswahl und Lockerung wissenschaftlicher Grenzen**
→ deshalb muss das Projekt **schneller und mutiger explorieren, aber wissenschaftlich noch strenger entscheiden**.

Diese Kausalkette ist eine Designannahme über menschlichen Entscheidungsdruck, kein Beweis für eine zukünftige Trading-Rendite und keine Rechtfertigung für höhere finanzielle Risiken.

### Zwingende Gegenmaßnahmen

1. Geschwindigkeit erhöhen: kostenlose Agenten-/Runner-Ressourcen parallel nutzen, Wiederverwendung von Artefakten erzwingen, unnötige manuelle Arbeit vermeiden.
2. Entscheidungen objektivieren: Meilensteine, Gates, Fingerprints und maschinenlesbare Zustände verwenden.
3. Auswahl begrenzen: keine Holdout-, Parameter-, Asset-, Feature-, Horizon- oder Threshold-Selektion nach Beobachtung.
4. Erfolgsdruck neutralisieren: DATA_INSUFFICIENT oder NO_SUPPORT zählt als gültiger Fortschritt, wenn die Forschungsunsicherheit belastbar reduziert wird.
5. Keine riskante Abkürzung: Leverage, größere Exposure, Gate-Lockerung oder Live-Promotion dürfen niemals als Reaktion auf finanziellen Druck eingesetzt werden.
6. Messbarer Output: Jede Entwicklungsphase muss einen überprüfbaren Evidenz- oder Engineering-Gewinn liefern.

### Verbindung zum 30-Tage-Ziel

Der 30-Tage-Meilenstein bis **2026-10-25** ist bewusst ein **Evidence-Meilenstein**, kein Renditeziel.

Der Projektentscheid lautet:

> Wir reagieren auf hohen äußeren Erfolgsdruck mit mehr Forschungsgeschwindigkeit und mehr methodischer Präzision, nicht mit schlechterer Beweisführung.

Die Mutkurve darf exponentiell steigen, aber nur nach objektiv bestandenem Gate. Der Erfolgsdruck darf die Mutkurve niemals selbst erhöhen.

### Operative Konsequenz

Aktuell bleibt die operative Mutstufe **M2 / 4x**. Die nächste Steigerung auf M3 erfolgt ausschließlich nach reproduzierbarer, disjunkter Mechanismusevidence.

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False

## Arbeits-PC und Cloud als permanente parallele Forschungsinfrastruktur — verbindliche Prioritätsregel

Der betriebsbereite Arbeits-PC mit Self-Hosted-Runner und die verfügbaren Cloud-/GitHub-Runner sind **dauerhafte, parallel zu nutzende Forschungsressourcen**.

Verbindliche Betriebsregel:
1. Der Arbeits-PC soll **möglichst dauerhaft betriebsbereit und als aktiver Research-Worker verfügbar** bleiben. Sobald er verfügbar ist, soll die Queue ihn kontinuierlich mit sinnvollen, freigegebenen Forschungs-, Feasibility-, PIT/Coverage-, QA- und Evidence-Jobs versorgen.
2. Cloud-/GitHub-Runner sollen **parallel** arbeiten und nicht erst auf die Fertigstellung der PC-Läufe warten. Sie übernehmen unabhängige Gegenprüfungen, zusätzliche Tests, Reviews, statische Analysen, alternative Implementierungen und weitere klar abgegrenzte Forschungsjobs.
3. Aufgaben werden so zerlegt, dass PC und Cloud gleichzeitig Fortschritt erzeugen. Wo eine echte Doppelprüfung sinnvoll ist, erhalten beide Pfade denselben Commit und vergleichen ihre Evidence/Fingerprints.
4. Es darf kein stiller Ressourcen-Leerlauf entstehen, wenn eine sinnvolle, bereits freigegebene Forschungsaufgabe verfügbar ist. Nicht belegte Kapazität soll für autonome Feasibility-, QA-, Review- oder Gegenhypothesenarbeit verwendet werden.
5. **Keine künstlichen Dauerläufe nur zum Auslasten der Hardware.** Permanente Nutzung bedeutet kontinuierliche Verfügbarkeit und bevorzugt kontinuierliche sinnvolle Forschung, nicht sinnlose CPU-Last.
6. Ergebnisse aus PC und Cloud werden über Commit-SHA, Testausgaben, Fingerprints und Evidence-Artefakte zusammengeführt. Abweichungen sind ein QA-/Forschungsbefund und werden nicht stillschweigend vereinheitlicht.
7. Bei Nichtverfügbarkeit eines Pfades wird dieser Zustand dokumentiert; der jeweils andere verfügbare Pfad arbeitet weiter. Die Wiederverfügbarkeit des PC-Workers soll anschließend automatisch wieder für die Forschung genutzt werden.
8. Kostenpflichtige externe Ressourcen bleiben ausgeschlossen. Kostenfreie verfügbare Ressourcen werden nach wissenschaftlichem Nutzen, Reproduzierbarkeit und Zeitgewinn eingesetzt.

Diese Regel gilt dauerhaft, ist Teil des Projektgedächtnisses und muss bei der Planung jedes neuen Research-Jobs berücksichtigt werden.

Technische Umsetzung der Dauerzufuhr: Workflow `.github/workflows/permanent-pc-research-loop.yml` startet bei verfügbarem Self-Hosted-Runner alle 30 Minuten einen begrenzten `autonomous_frontier_qa`-Forschungs-/QA-Block mit Latest-Run-Wins, sodass kein unnötiger Rückstau entsteht. Der Loop umfasst RCCSM-Feasibility, Frontier-Feasibility, Q089-Scaffolding/Envelope und Governance-Regressionen sowie einen deterministischen RCCSM-Provenienztest. Er erzeugt ausschließlich Paper-/QA-Evidence und besitzt keine Performance- oder Live-Autorisierung.


## Dauerhafte Zielbindung, familiäre Dringlichkeit und PC-Betrieb — 2026-09-28

### Übergeordnetes Ziel

Das übergeordnete wirtschaftliche Ziel des Projekts ist die langfristige Entwicklung eines möglichst robusten Trading-Agenten, der nach ausreichender wissenschaftlicher Validierung einen regelmäßigen, tatsächlich entnehmbaren Cashflow zur finanziellen Absicherung der Familie ermöglichen kann.

Der konkrete Zweck ist ausdrücklich familiäre Sicherheit: Ehefrau und Kind sollen durch verantwortbare finanzielle Entscheidungen geschützt werden. **Ein sicheres monatliches Einkommen kann der Markt nicht garantieren**; deshalb ist das operative Forschungsziel ein belastbares System mit nachvollziehbarem Risiko, Kosten, Drawdown-, Cashflow- und Sequence-of-Returns-Verhalten.

Diese Zielbindung ist dauerhaft. Sie wird nicht durch wechselnde Chatkontexte, einzelne Backtests oder kurzfristigen Erfolgsdruck ersetzt.

### Dringlichkeit

Die familiäre Situation erzeugt einen **hohen zeitlichen und wirtschaftlichen Handlungsdruck**. Dieser Druck ist ab 2026-09-28 ausdrücklich als Projektfaktor festgehalten.

Konsequenz:
- Wir arbeiten so autonom und zielgerichtet wie innerhalb der Freigaben möglich.
- Kostenfreie verfügbare Rechen-, Runner- und Agentenressourcen werden effizient und mutig eingesetzt.
- Neue, orthogonale und auch ungewöhnliche Hypothesen dürfen aktiv gesucht und schnell falsifiziert werden.
- Die wissenschaftliche Beweislast, Sicherheitsgrenzen und Governance werden gerade wegen der Dringlichkeit nicht gelockert.

**Dringlichkeit erhöht Forschungsgeschwindigkeit, niemals finanzielles Risiko.**

### Permanente Nutzung des Arbeits-PCs

Der betriebsbereite Windows-Arbeits-PC mit Self-Hosted-Runner ist ab 2026-09-28 **dauerhafte Projektinfrastruktur** und soll für das Trading-Agent-Projekt kontinuierlich genutzt werden, soweit der PC verfügbar und betriebsbereit ist.

Der Runner ist bevorzugter Ausführungspfad für:
- deterministische Research-/Feasibility-/PIT-/Coverage-Läufe;
- Regressionstests und technische QA;
- reproduzierbare Evidence-Erzeugung;
- Paper-/Shadow-/Forward-Simulation;
- autonome, bereits freigegebene Forschungsjobs.

Die permanente PC-Nutzung dient dazu, Leerlauf zu vermeiden und die Zeit bis zum nächsten evidenzfähigen Ergebnis zu verkürzen. Sie ändert **nicht** die Sicherheitsarchitektur und ersetzt keine formale Forschungsfreigabe.

### Schutzprinzip

Für jede Entscheidung gilt weiterhin:

**Familienziel → hohe Forschungsgeschwindigkeit + hohe wissenschaftliche Strenge → erst bei ausreichender Evidenz weiterer Kapital-/Betriebsschritt.**

Insbesondere sind voreilige Echtgeldnutzung, versteckte Live-Ausführung, übermäßiger Leverage, Gate-Lockerung oder Holdout-/Parameter-Tuning als Reaktion auf familiären Erfolgsdruck ausgeschlossen.

## Arbeitsweise und Darstellung — dauerhaft

Die technische Umsetzung darf innerhalb der erteilten Projektfreigaben möglichst autonom erfolgen. Unabhängige, sicher ausführbare Arbeit wird nicht künstlich auf spätere Chats verschoben; deterministische Berechnung und formale Prüfungen bleiben nachvollziehbar über Repository, Actions und Evidence-Artefakte.

Die Kommunikation des Entwicklungsstands erfolgt auf **Forschungs- und Systemebene** und bewusst weniger granular als die technische Evidence-Schicht. Im Vordergrund stehen Forschungsstand, offene wissenschaftliche Frage, Entscheidungsstand und der nächste große Forschungsschritt. Commit-, Test-, Workflow- und Implementierungsdetails bleiben in den kanonischen Quellen und werden im Chat nur dann hervorgehoben, wenn sie wissenschaftlich, sicherheitsbezogen oder strategisch relevant sind.

Die operative Reihenfolge bleibt:

**Beobachten → Hypothesen bilden → billig falsifizieren → Evidenz verdichten → unabhängig prüfen → erst dann formalisieren → wiederholen.**

Kostenpflichtige externe Agenten-, Copilot- oder API-Ressourcen bleiben ausgeschlossen. Kostenfreie Agentenressourcen werden gezielt für Hypothesenbildung, Gegenhypothesen, Forschungsdesign und Review eingesetzt; deterministische Berechnung bleibt reproduzierbar.


## Dauerhaftes Ressourcenmodell — 2026-09-26

Das monatlich erneuerbare GitHub-Free-Kontingent wird als strategische Infrastrukturreserve behandelt.

Kanonische Policy: docs/GITHUB_FREE_RESOURCE_OPERATING_MODEL.md.

Arbeitsmuster:
Steuer-Agent entscheidet → Cloud/Coding-Worker implementiert → Actions reproduzieren → Reviewer prüft → Evidence entscheidet.

Copilot Cloud Agent ist fachlich besonders geeignet für CI-/Testfehler, Regressionstests, abgegrenzte Refactorings, Dokumentation, technische Schuld und technische PR-Arbeit. Er bleibt nachgeordnet. Holdout-Auswahl, Promotionsentscheidungen, Gate-Änderungen und wissenschaftliche Interpretation bleiben außerhalb des Cloud Agents.

Aktueller GitHub-Planstand: Cloud Agent ist nicht im Copilot Free enthalten. Paid agent budget bleibt deshalb 0 USD. Eine bereits ohne Zusatzkosten vorhandene Berechtigung darf genutzt werden.

Bei jedem neuen Chat mit "trading agent" wird das Ressourcenmodell vor der Auswahl des nächsten Arbeitsschritts eingelesen.

## Permanenter Multi-Model-AI-Worker-Pool — 2026-09-28

Ab 2026-09-28 ist zusätzlich zum PC-/GitHub-/Python-Ressourcenmodell ein
provider-neutraler, kostenfreier AI-Worker-Pool verbindlich vorgesehen und im
Repository implementiert.

### Zweck

Die Engstelle wird nicht durch künstliche Parallelisierung derselben Berechnung,
sondern durch zusätzliche unabhängige Denk-, Review-, Design- und Engineering-
Kapazität erweitert.

Die Ressourcenklassen sollen gleichzeitig arbeiten:

Self-hosted PC-Runner + GitHub-hosted Runner + bounded GitHub Agents + Python +
optionale externe AI-Worker.

Eine freie Ressource wartet nicht auf eine andere, wenn keine echte fachliche
Abhängigkeit besteht.

### Externe AI-Worker

Implementierte Schnittstelle:
- automation/ai_worker_fabric.py
- .github/workflows/ai-worker-fabric.yml
- docs/AI_WORKER_FABRIC.md
- ai_requests/

Primärer opportunistischer Provider: Gemini CLI.
Die offizielle Gemini CLI unterstützt nicht-interaktive Prompt-Ausführung und
maschinenlesbares JSON und ist damit für automatisierte Worker geeignet.
Die aktuelle Gemini Developer API besitzt eine Free Tier für ausgewählte Modelle,
mit jeweils geltenden Limits.

Sekundärer opportunistischer Provider: Claude CLI.
Claude wird nur verwendet, wenn eine bereits vorhandene CLI-/Session-
Berechtigung ausdrücklich als kostenfrei bestätigt wurde. Ein Anthropic-API-Key
gilt niemals als Beweis für kostenlose Nutzung.

### Kosten- und Sicherheitsregel

Externe AI-Worker laufen fail-closed.

Ein Provider darf nur starten, wenn:
1. das externe Provider-Allowlisting ausdrücklich bestätigt wurde;
2. das erforderliche Programm und die Authentifizierung vorhanden sind;
3. der Provider-spezifische Free-Mode ausdrücklich bestätigt ist;
4. der Task selbst deterministische Berechnung, Holdout-/Parameter-/Asset-
   Auswahl, Gateänderung, Promotion, Live-Ausführung und Paid Usage verbietet.

Fehlt irgendeine Voraussetzung, wird SKIPPED statt eines kostenpflichtigen
Fallbacks erzeugt.

Paid agent/API budget bleibt 0 USD.

### Rollen

Externe AI-Worker dürfen:
- ungewöhnliche Alpha-Hypothesen erzeugen;
- Gegenhypothesen und adversarial Reviews liefern;
- Research-Designs und Testideen entwickeln;
- Architektur-/Code-Reviews unterstützen;
- Dokumentations- und QA-Vorschläge erzeugen.

Externe AI-Worker dürfen niemals:
- wissenschaftliche Evidenz selbst erzeugen oder behaupten;
- Holdout- oder Kandidatenselektion entscheiden;
- Research-Gates ändern;
- Promotion oder Live-Trading autorisieren.

Worker-Output ist immer nur Inputmaterial für die nachgelagerte deterministische
und unabhängige Prüfung.

### Persistente Parallelitätsregel

Der neue AI-Worker-Workflow ist bewusst getrennt vom Self-hosted Research Loop und
von der bestehenden bounded Agent Queue. Dadurch kann AI-Worker-Arbeit auf
GitHub-hosted Runnern laufen, während der lokale PC-Runner sowie deterministische
Python-/Research-Läufe unabhängig weiterarbeiten.

Diese Architektur ist Bestandteil der dauerhaften Startregeln für neue Chats mit
dem Trigger trading agent.

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False

## Authentifizierung und Copilot-Free-Reserve — verbindliche Regel ab 2026-09-28

### Gemini

Für den persistenten lokalen Windows-PC ist der bevorzugte kostenlose Weg
die interaktive Gemini-CLI-Anmeldung mit dem persönlichen Google-Konto. Gemini
CLI dokumentiert Google-Login als unterstützte lokale Authentifizierung und
cached credentials für nachfolgende Sessions.

Für GitHub-hosted Headless-Jobs wird ein separat hinterlegtes, ausdrücklich
kostenfreies Gemini-Credential benötigt. Der lokale Google-Browser-Login wird
nicht automatisch auf GitHub-hosted Runner übertragen.

Das Google-Konto darf dasselbe Konto sein, das der Benutzer für andere Google-
Dienste verwendet. Daraus folgt jedoch keine automatische Verbindung zu diesem
Chat oder zu OpenAI-Konten. Credentials werden niemals in den Chat oder ins
Repository eingecheckt.

### Claude

Claude bleibt ein separat authentifizierter Provider. Eine Claude-Web-/App-
Anmeldung wird nicht automatisch auf GitHub-hosted Runner übertragen.
Automatisierung erfolgt nur über eine vorhandene, ausdrücklich kostenfreie
CLI-/Account-Berechtigung. Anthropic API-Billing bleibt ausgeschlossen.

### Copilot Free als knappe Monatsreserve

GitHub setzt das enthaltene Monatskontingent am ersten Tag jedes Monats
um 00:00 UTC zurück. Die Projektarchitektur behandelt dieses Kontingent als
knappe Spezialreserve und nicht als normalen Dauer-Worker.

Verbindliche interne Schutzkappe:
- ab 2026-10-01T00:00:00Z wieder freigabefähig;
- maximal 4 gebundene Copilot-Session-Reservierungen pro Kalendermonat;
- maximal 30 AI credits pro reservierter Session;
- maximal 1 paralleler Copilot-Worker;
- kein Überziehen, kein Kauf zusätzlicher Credits, kein Paid Fallback.

Die 4/12-Grenzen sind bewusst selbst auferlegte Konservativgrenzen und stellen
nicht die von GitHub garantierte Größe des Free-Kontingents dar.

Deterministische Python-/Research-Läufe, Self-hosted PC und externe AI-Worker
bleiben von dieser Copilot-Reserve unabhängig und dürfen parallel weiterarbeiten.
## Betriebsmodell-Verankerung und Live-Preflight — 2026-09-30

Diese Regel konkretisiert die kanonische Startregel für neue Chats mit dem Trigger **"trading agent"** und gilt unabhängig davon, ob gleichzeitig ein aktiver Chat besteht.

### Chat-Einstieg

Bei neuem Chat mit "trading agent" ist die Reihenfolge zwingend:

**aktuelles `master` → kanonisches Projektgedächtnis → Live-Ressourcen-/Runner-Preflight → aktueller Evidence-/Research-Status → nächste autonome Aufgabe.**

Nicht der Chatverlauf, sondern das aktuelle öffentliche Repository ist die technische Source of Truth.

### Chat-unabhängiger Betrieb

Die dauerhafte Forschungsinfrastruktur muss ohne offenen Chat weiterarbeiten können:

- GitHub Actions Schedule/Workflow-Dispatch für hosted Forschung, CI, Status-Synchronisation und AI-Worker.
- Self-hosted Windows-Runner für lokale QA, Reproduktion und freigegebene bounded Research-Jobs, solange der PC und die Runner-Prozesse online sind.
- Externe kostenlose AI-Pfade fail-closed und unabhängig von deterministischer Forschung.
- Eine Ressource wartet nicht auf den Chat, solange eine bereits zulässige und fachlich unabhängige Aufgabe vorhanden ist.

Ein aktiver Chat dient damit der Steuerung, Interpretation und Freigabeentscheidung — nicht als technischer Dauerbetriebsschalter.

### GitHub-hosted Runner Reaktivierung

Für das öffentliche Repository `DWR-debug/trading-agent-public` werden Standard-GitHub-hosted Runner wieder als regulärer Primärpfad genutzt. Eine Live-Prüfung am **2026-09-30** bestätigte:

- `CI` auf `ubuntu-24.04` erfolgreich;
- `CI` auf `ubuntu-24.04-arm` erfolgreich;
- `T052 Exact Master CI Gate` erfolgreich;
- der vorherige Zero-Job-/Queue-Engpass war für diese aktuellen Läufe nicht reproduziert;
- der `Free AI Worker Fabric` lief auf hosted Runnern tatsächlich an, wobei einzelne Provider-Lanes weiterhin providerbedingt scheitern oder übersprungen werden können;
- der `Permanent Self-Hosted Research Loop` lief parallel erfolgreich mit `local_reproduction` und `autonomous_frontier_qa`.

Die fachliche Konsequenz: **GitHub-hosted und Self-hosted werden ab jetzt bewusst als parallele, komplementäre Worker-Pools betrieben.** Hosted Runner sind nicht mehr nur Fallback.

### Ressourcen-Routing ab 2026-09-30

1. **Hosted Linux x64/ARM64:** primär für CI, deterministische Reproduktion, Coverage/PIT, formale Gates und unabhängige Gegenprüfungen.
2. **Self-hosted Windows:** primär für lokale Reproduktion, QA, bounded Frontier-Feasibility und lokale AI-Smoke/Worker-Pfade.
3. **Kostenfreie externe AI-Worker:** Hypothesen, Gegenhypothesen, Research-Design, adversarial Review und technische Analyse; niemals Evidence oder Promotion.
4. **Copilot-Free-Reserve:** nur ab dem verifizierten Monats-Reset und nur für hochwirksame, klar begrenzte Engineering-/QA-Aufgaben.
5. **Paid budget:** dauerhaft 0 USD.

### Forschungs-Governance bleibt unverändert

Die Reaktivierung hosted Runner ändert keine wissenschaftliche Freigabe:

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
orders_enabled=False  
automatic_promotion=False

Performance bleibt erst nach gültiger Coverage/PIT/Input-Provenienz, Preregistration und einmaliger formaler Autorisierung zulässig.

## Dauerhafter Self-hosted-Failover — 2026-09-30

Der Self-hosted-Windows-Pool bleibt bevorzugter lokaler Worker, darf aber nie zum Single Point of Failure werden.

Der Workflow `.github/workflows/hosted-research-failover.yml` überwacht den Heartbeat des permanenten Self-hosted Research Loop. Bei fehlendem, zu altem oder zu lange wartendem Self-hosted-Signal startet er automatisch bounded Forschung auf GitHub-hosted `ubuntu-24.04` und `ubuntu-24.04-arm`.

Der Failover ist:
- chat-unabhängig;
- kostenfrei;
- cross-platform;
- fail-closed gegenüber Performance/Premotion/Live-Trading;
- ausschließlich für QA, Reproduktion und Frontier-Feasibility vorgesehen.

Das Failover stellt keine wissenschaftliche Abkürzung dar. Seine Artefakte bleiben `formal_evidence_allowed=false` und `formal_research_evidence=false`.

Rückkehrregel: Sobald der Self-hosted Heartbeat wieder frisch ist, wird der Hosted-Fallback automatisch nicht mehr ausgeführt; der normale parallele Worker-Pool übernimmt.

Falls beide Self-hosted Runner gleichzeitig ausfallen, soll die Hosted x64/ARM-Fallbackschicht den Forschungsbetrieb aufrechterhalten. Damit ist Self-hosted Kapazität ein Beschleuniger, aber kein notwendiger Betriebsbestandteil.