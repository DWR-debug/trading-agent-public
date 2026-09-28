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