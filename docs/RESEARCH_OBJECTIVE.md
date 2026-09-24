# Übergeordnetes Forschungsziel

## 1. Zweck des Projekts

Das Trading-Agent-Projekt dient nicht primär der Maximierung einer Backtest-Rendite.

Das übergeordnete Ziel ist die Entwicklung und belastbare Validierung eines **autonomen, strikt risiko- und evidenzgesteuerten Trading-Systems**, das nach ausreichender wissenschaftlicher Bestätigung in der Lage sein soll, aus einem dauerhaft investierten Grundkapital **wiederkehrendes, entnehmbares Einkommen** zu erzeugen und dabei das eingesetzte Kapital möglichst zuverlässig zu erhalten.

Das Ziel ist damit:

> **Nachhaltig verfügbares Einkommen aus Trading bei möglichst geringer Ruin-, Verlust- und Drawdown-Gefahr, ohne die statistische und praktische Robustheit zugunsten kurzfristig höherer Rendite zu opfern.**

Eine zukünftige Produktionsfreigabe darf nur erfolgen, wenn die dafür erforderliche Evidenz tatsächlich erreicht wurde. Das Projekt darf keinen Erfolg behaupten oder voraussetzen, den die Daten nicht tragen.

## 2. Zielhierarchie

Die Forschungs- und Entwicklungsentscheidungen folgen dieser Reihenfolge:

1. **Kapitalerhalt und Vermeidung ruinöser Verluste**
2. **Kontrollierbares und möglichst kleines Risiko**
3. **Robuste positive Out-of-Sample-Performance**
4. **Regelmäßigkeit und Planbarkeit des erzeugbaren Cashflows**
5. **Effiziente Erzielung von Rendite**
6. **Maximierung des langfristig entnehmbaren Einkommens innerhalb der Sicherheitsgrenzen**

Eine Strategie darf deshalb nicht allein deshalb bevorzugt werden, weil sie eine höhere Gesamtrendite oder einen höheren Sharpe-Wert im Backtest erzeugt.

## 3. Was ein guter Trading Agent leisten muss

Die Qualität des Agenten ist nicht identisch mit der Qualität einer einzelnen Strategie.

Ein hochwertiger Agent muss mindestens fünf Eigenschaften gleichzeitig erfüllen:

### A. Strategiequalität

Er muss aus klar definierten, reproduzierbaren Handelsstrategien Signale und Portfoliogewichte ableiten können.

### B. Robustheit

Die Strategie muss auf ungesehenen Daten, neuen Zeitabschnitten und vollständig disjunkten Märkten bzw. Symboluniversen funktionieren und darf nicht nur auf die Entwicklungsdaten angepasst sein.

### C. Risikokontrolle

Das System muss Verluste, Drawdowns, Positionsgrößen, Konzentration, Hebel und operative Risiken kontrollieren. Sicherheitsmechanismen müssen fail-closed arbeiten.

### D. Einkommensfähigkeit

Die Performance muss perspektivisch nicht nur als kumulierte Rendite, sondern als **nachhaltig entnehmbarer Cashflow** untersucht werden.

Dabei sind insbesondere zu prüfen:

- Entnahmefähigkeit bei laufender Wiederanlage,
- Verhalten unter Verlust- und Drawdown-Phasen,
- Schwankung und Ausfallrisiko der Auszahlungen,
- ausreichender Kapitalpuffer zwischen Grundkapital und Entnahmen,
- Auswirkungen von Gebühren, Slippage und weiteren realistischen Kosten.

### E. Operative Zuverlässigkeit

Der Agent muss reproduzierbar, überwachbar, ausfallsicher, pausierbar und wiederaufnehmbar sein. Forschung, Backtests und späteres Paper Trading müssen sauber von einer möglichen zukünftigen Produktion getrennt bleiben.

## 3.5 Startkapital und Einkommensmodell

Das initiale Forschungs- und Simulationskapital beträgt **500 EUR**.

Dieses Startkapital ist als dauerhaft arbeitendes Grundkapital zu behandeln. Die Forschung optimiert nicht auf einen vollständigen Kapitalverbrauch zugunsten kurzfristiger Entnahmen.

Das Grundprinzip des späteren Einkommensmodells lautet:

**500 EUR Startkapital → Trading-Performance → realisierter Gewinn → prüfbarer ausschüttbarer Überschuss → Auszahlung → verbleibendes Arbeitskapital**

Dabei gilt:

- Auszahlungen dürfen nicht aus notwendigem Grundkapital erfolgen.
- Bei Verlust- oder Drawdown-Phasen besteht kein Anspruch auf eine feste Auszahlung.
- Ein ausreichender Risiko- und Kapitalpuffer muss vor jeder späteren Entnahme berücksichtigt werden.
- Die tatsächliche Auszahlungshöhe ist erfolgsabhängig und wird nicht als feste Renditegarantie vorausgesetzt.
- Zusätzliches Kapital darf später eingezahlt oder erwirtschaftetes Kapital bewusst im System belassen werden.
- Das Modell muss eine spätere Skalierung des Arbeitskapitals ermöglichen, ohne die Strategie logisch zu verändern oder historische Ergebnisse nachträglich umzudeuten.

Die konkrete Ausschüttungsregel, der minimale Kapitalpuffer und die Wiederanlage-/Aufstockungsregeln werden als eigene Research-Frage präregistriert, bevor sie für eine Produktionsfreigabe verwendet werden.

## 4. Formale Forschungsaufgabe

Die Forschung ist als **risikobeschränkte Optimierungsaufgabe** zu verstehen:

> Finde eine oder mehrere Handelsstrategien bzw. Strategie-Kombinationen, die auf ungesehenen Daten robuste und wiederholbare Erträge erzeugen und unter realistischen Kosten sowie klar definierten Risiko- und Kapitalerhaltungsgrenzen den langfristig entnehmbaren Cashflow maximieren.

Dabei ist die Reihenfolge entscheidend:

**Nicht:** maximale Rendite und anschließend Risiko reduzieren.

**Sondern:** ein akzeptables Risikoniveau einhalten und innerhalb dieses Rahmens die bestmögliche robuste Einkommensfähigkeit suchen.


## 4.5 Multi-Strategie als Kernarchitektur

Der Agent soll nicht auf eine einzelne Strategie festgelegt werden.

Die Forschung untersucht deshalb ein **Portfolio komplementärer Strategien**, die unterschiedliche Marktbedingungen adressieren können. Ziel ist nicht, für jede Marktsituation eine vermeintlich perfekte Strategie vorherzusagen, sondern nur solche Strategien zu aktivieren bzw. höher zu gewichten, deren Eignung durch unabhängige Evidenz und den aktuellen Risikokontext unterstützt wird.

Eine zukünftige Multi-Strategie-Architektur soll daher mindestens berücksichtigen:

- unterschiedliche und möglichst orthogonale Quellen des erwarteten Vorteils,
- unterschiedliche Marktregime und deren Unsicherheit,
- Wechselwirkungen zwischen Strategien,
- gemeinsame und individuelle Drawdowns,
- Korrelation und Konzentrationsrisiko,
- Kosten durch Umschichtungen,
- Ausfall einer einzelnen Strategie,
- konservatives Verhalten bei unklarer Regime-Lage.

Wesentlich ist:

> Der Agent soll nicht „immer handeln“, sondern zwischen **geeignetem Handeln, reduzierter Exposition und Nicht-Handeln** unterscheiden können.

Eine Regime-Erkennung darf nicht aufgrund eines nachträglichen Backtest-Fits als zuverlässig angenommen werden. Sie muss selbst Out-of-Sample und unter unabhängigen Validierungen nachweisen, dass die dynamische Auswahl oder Gewichtung einen robusten Mehrwert gegenüber einer festen Kombination erzeugt.

### Zielbild der Agentenlogik

**Marktdaten → Regime-/Zustandsanalyse → Auswahl aus validierten Strategien → Risiko-/Positionsallokation → Portfolio-Risikokontrolle → Ausführung → laufende Überwachung → Kapital-/Gewinnrechnung → ggf. Auszahlung**

Die einzelnen Stufen müssen voneinander getrennt, testbar und fail-closed sein.

## 5. Wissenschaftliche Evidenz

Eine Strategie darf nicht aufgrund eines einzelnen guten Backtests in den Produktionspfad gelangen.

Für die Forschung gelten weiterhin:

- strikte Trennung von Research und Holdout,
- vollständig symbol-disjunkte Validierungssätze,
- präregistrierte Hypothesen bei bestätigenden Experimenten,
- keine nachträgliche Optimierung auf Holdout-Daten,
- dokumentierte Trial- und Selection-Historie,
- realistische Kostenannahmen,
- Analyse von Gesamtertrag **und** zeitlicher Stabilität,
- explizite Failure-Diagnose und Archivierung negativer Ergebnisse,
- statistische Selection-/Overfitting-Governance, sobald die erforderlichen Eingaben belastbar verfügbar sind.

Die bisherige Praxis, fehlende statistische Evidenz nicht künstlich zu rekonstruieren, bleibt bestehen.

## 6. Zukünftige Freigabestufe

Die Produktion ist ein **separater Freigabestatus**, kein automatisches Ergebnis eines erfolgreichen Research-Trials.

Vor einer späteren Produktionsfreigabe müssen mindestens folgende Fragen positiv beantwortbar sein:

1. Erzeugt der Ansatz robuste positive Out-of-Sample-Erträge?
2. Bleiben Drawdown und Verlustrisiko innerhalb der vorab definierten Grenzen?
3. Ist die Performance über unabhängige Validierungen stabil?
4. Bleibt die Performance unter realistischen Kosten und Stressannahmen tragfähig?
5. Ist der erwartete Cashflow mit einer dauerhaften Entnahmestrategie vereinbar?
6. Ist ausreichend Kapitalpuffer vorhanden, damit notwendige Entnahmen nicht zu einer Destabilisierung des Systems führen?
7. Sind technische, operative und Sicherheitsmechanismen vollständig verifiziert?

Die konkreten numerischen Mindestgrenzen für Einkommen, Drawdown, Kapitalpuffer und Entnahmequote werden **separat und vor zukünftigen Bestätigungstests** festgelegt. Sie dürfen nicht rückwirkend aus bereits beobachteten Resultaten abgeleitet werden.

## 7. Zentrale Forschungsfragen

Die weitere Forschung wird sich damit auf vier miteinander verbundene Fragen konzentrieren:

### Frage 1 – Edge

Welche Marktstrukturen und Signalmechanismen erzeugen einen robusten, wiederholbaren Vorteil?

### Frage 2 – Robustheit

Welche dieser Mechanismen überleben neue Märkte, neue Zeiträume, Kostenstress und unabhängige Validierung?

### Frage 3 – Risiko

Wie lässt sich das Risiko so weit reduzieren, dass Kapitalerhalt und langfristige Handlungsfähigkeit gewährleistet werden, ohne den nachgewiesenen Edge zu zerstören?

### Frage 4 – Einkommen

Wie wird robuste Strategie-Performance in einen **nachhaltigen und kontrollierbaren Auszahlungsstrom** aus einem dauerhaft arbeitenden Grundkapital überführt?

## 8. Konsequenz für die aktuelle Entwicklung

Der aktuelle Kandidat bleibt BLOCKED.

Die bisherigen negativen Hypothesen werden nicht nachträglich so verändert, dass sie das neue Ziel erfüllen. Stattdessen wird das neue Ziel ab jetzt als übergeordneter Rahmen für die Auswahl zukünftiger Forschungshypothesen verwendet.

Insbesondere bedeutet das:

- Ein höherer Ertrag allein ist kein ausreichender Erfolg.
- Ein geringerer Drawdown allein ist kein ausreichender Erfolg.
- Ein gutes Holdout-Ergebnis allein ist kein ausreichender Erfolg.
- Eine einzelne Strategie ist nicht automatisch der optimale Agent.
- Mehrere komplementäre Strategien können gemeinsam sinnvoller sein als eine Einzelstrategie, **wenn** ihre Kombination unabhängig dieselben Robustheits- und Risikokriterien erfüllt.
- Kapitalerhalt und Vermeidung eines ruinösen Pfads haben Vorrang vor aggressiver Renditeoptimierung.

## 9. Sicherheitsstatus

Dieses Forschungsziel ändert nichts an den bestehenden Sicherheitsregeln:

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- keine Live-Orders
- keine automatische Produktionsfreigabe

Das übergeordnete Ziel des Projekts ist damit die **wissenschaftlich belegte Entwicklung eines robusten, risikoarmen und später auszahlungsfähigen autonomen Trading-Agenten** – nicht die Optimierung eines möglichst eindrucksvollen Backtests.
