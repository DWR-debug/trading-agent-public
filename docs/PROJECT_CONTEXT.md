# Trading Agent — Dauerhafter Projektkontext

Stand: 2026-09-24
Repository: `DWR-debug/trading-agent-public`

Dieses Dokument ergänzt die technische Repository-Historie um den gemeinsamen Projektkontext.
Es soll verhindern, dass bei einem neuen Chat zwar der Codezustand korrekt rekonstruiert wird,
aber Ziele, Prioritäten, Forschungslogik und wichtige gemeinsame Entscheidungen verloren gehen.

## 1. Quellenmodell

Das Projekt arbeitet künftig mit vier getrennten Wahrheitsebenen:

1. **Technische Wahrheit**
   - öffentlicher `master` von `DWR-debug/trading-agent-public`;
   - Code, Konfiguration, Workflows, gemergte Commits, Tests, Branches und formale CI-Zustände.
   - Das private Repository `DWR-debug/trading-agent` ist keine Actions-Ausführungsquelle und keine
     Standardquelle für den aktuellen Projektzustand.

2. **Evidenzwahrheit**
   - `research/evidence/trial_ledger.json`;
   - dauerhafte Research-Checkpoints;
   - unveränderliche Reports und verifizierbare Workflow-/Artifact-Provenienz.
   - Formale Trial-Ergebnisse werden nicht anhand späterer Chats umgeschrieben.

3. **Projektkontext und Absicht**
   - dieses Dokument;
   - importierte, noch verfügbare Chat-Evidenz;
   - ausdrücklich festgehaltene gemeinsame Ziele, Designprinzipien und langfristige Architekturentscheidungen.
   - Der Kontext darf technische Fakten nicht ersetzen, erklärt aber, **warum** wir eine bestimmte Forschung verfolgen.

4. **Aktueller Arbeitszustand**
   - `PROJECT_STATUS.md` und `docs/research_queue_*.md`;
   - sie leiten aus Technik, Evidenz und Kontext den nächsten sinnvollen Arbeitsschritt ab.

### Konfliktregel

Bei einem Widerspruch wird nicht stillschweigend eine Quelle überschrieben.

- Technische Tatsachen werden gegen den aktuellen öffentlichen `master` verifiziert.
- Forschungsergebnisse werden gegen Ledger, Checkpoint, Report und Workflow-Provenienz verifiziert.
- Projektziele/Entscheidungen werden gegen diesen Kontext und die zugehörige Chat-Evidenz geprüft.
- Unaufgelöste Widersprüche werden dokumentiert und erst danach bereinigt.

Damit gilt nicht mehr „GitHub ersetzt den Projektkontext“, sondern:
**GitHub ist technische Referenz; der Projektkontext bleibt eine eigene, dauerhafte Wissensebene.**

## 2. Sicherheitsvertrag

Der Sicherheitsvertrag ist invariant und gilt unabhängig vom Renditeziel:

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- keine Live-Orders;
- keine automatische Echtgeldpromotion;
- Research und spätere Ausführung bleiben getrennte Gateways.

Leverage, Long/Short und andere höhere Exposure-Varianten dürfen nur als Research-Frage untersucht werden.
Ein positives Backtest-/Research-Ergebnis aktiviert keinen Live-Pfad automatisch.

## 3. Übergeordnetes Ziel

Das Projekt soll einen autonomen, risiko- und evidenzgesteuerten Trading Agent entwickeln,
der nach ausreichender wissenschaftlicher Validierung wiederkehrendes, entnehmbares Einkommen
aus Kapital erwirtschaften kann.

Die Forschungspriorität ist:

1. Kapitalerhalt und Vermeidung ruinöser Verluste
2. kontrollierbares Risiko
3. robuste positive Out-of-Sample-/Holdout-Evidenz
4. Regelmäßigkeit und Planbarkeit des Cashflows
5. effiziente Renditeerzielung
6. Maximierung des langfristig entnehmbaren Einkommens innerhalb der Sicherheitsgrenzen

Das langfristige Ziel „hoher bzw. schneller Kapitalaufbau“ ist ein Anforderungsparameter,
aber kein Grund für Gate-Lockerung, nachträgliche Auswahl oder Optimierung auf gewünschte Ergebnisse.

## 4. Wissenschaftliche Arbeitsregeln

Kernelemente:

- Research und Holdout strikt trennen.
- Vollständig symbol-disjunkte Validierungen bevorzugen.
- Bestätigende Experimente präregistrieren.
- Keine Holdout-Selektion.
- Keine versteckte Parameter-, Threshold-, Varianten- oder Asset-Suche.
- Realistische Kosten und Stressszenarien.
- Rolling-/Walk-Forward-Robustheit.
- Negative Evidenz dauerhaft archivieren.
- Datenfehler vor Performanceauswertung als `DATA_INVALID` behandeln.
- Keine nachträgliche Lockerung des Datenvertrags.
- Keine Promotion ohne formale Evidence-Gates.
- Deskriptive Beobachtungen nicht als kausale Beweise darstellen.

## 5. Warum verworfene Hypothesen nicht automatisch wertlos sind

Ein formaler `NO_SUPPORT`- oder `archived_rejected`-Status bedeutet:
**Diese präregistrierte Hypothese hat den vorgesehenen Nachweis nicht erbracht.**

Er bedeutet nicht automatisch:
„Jede einzelne Information aus diesem Trial ist nutzlos.“

Deshalb wird vor einer Bereinigung eine eigene Research-Archaeology durchgeführt.

Mögliche Klassen:

- **RETAIN_NEGATIVE** — als wichtige negative Evidenz behalten.
- **SALVAGEABLE_OBSERVATION** — Teilbefund ist für eine spätere, klar neue Hypothese interessant,
  ohne den alten Trial wieder zu öffnen.
- **DIAGNOSTIC_ONLY** — erklärt Verhalten oder Failure Mode, liefert aber keinen neuen Edge-Nachweis.
- **DATA_QUALITY** — technischer Daten-/Coverage-Befund.
- **ADMINISTRATIVE_NOISE** — organisatorisch redundant und nach Abhängigkeitsprüfung lösch-/archivierbar.

Ein historischer Teilbefund darf niemals nachträglich als versteckter Selection-Schritt für denselben
Trial verwendet werden.

## 6. Chat-Kontext: was aufgenommen werden darf

Die aktuell verfügbare, projektbezogene Chat-Kontext-Evidenz ist zusätzlich in
`docs/CHAT_CONTEXT_2026_09_24.md` dokumentiert. Sie enthält bewusst nur belastbare,
dauerhafte Projektinformationen und keinen vollständigen Chat-Export.

Verfügbare Chat-Evidenz ist ein legitimer Bestandteil des Projektkontexts, sofern sie tatsächlich
zugänglich ist.

Mögliche Quellen:

- aktueller Chat;
- in der Unterhaltung verfügbare vorherige Projektkontexte/Zusammenfassungen;
- vom Benutzer bereitgestellte Chat-Exporte;
- eingefügte Transkripte oder relevante Ausschnitte;
- projektbezogene Entscheidungen, die ausdrücklich im Chat dokumentiert wurden.

Es besteht **kein pauschaler Zugriff auf sämtliche alten Chatverläufe** des Kontos.
Fehlende Chats werden daher nicht erfunden oder aus Lücken rekonstruiert.

Für jede importierte Chat-Information sollen möglichst festgehalten werden:

- ungefähres Datum;
- Themenbereich;
- Originalaussage bzw. belastbare Zusammenfassung;
- ob sie eine technische Tatsache, eine Projektentscheidung, eine Hypothese oder nur eine Idee war;
- ob sie später durch Repository-Evidenz bestätigt, widerlegt oder überholt wurde.

## 7. Wiederherstellung bei neuem Chat

Ein neuer „trading agent“-Chat beginnt künftig konzeptionell mit:

`PROJECT_CONTEXT.md`
→ `PROJECT_STATUS.md`
→ `research/evidence/trial_ledger.json`
→ aktuelle Branch-/PR-/Workflow-Lage
→ relevante Reports/Checkpoints
→ erst danach nächste Forschungsentscheidung.

Der alte Chat muss dafür nicht vollständig verfügbar sein.

## 8. Gemeinsame Entwicklungsphilosophie

Das System soll möglichst autonom arbeiten:

Daten → Datenqualität → Hypothese → Präregistrierung → Preflight → Research →
Gates → Robustheit → Archivierung → nächste orthogonale Frage.

Die jeweils nächste Frage soll aus vorhandener Evidenz abgeleitet werden und nicht aus dem Wunsch,
endlich einen positiven Backtest zu produzieren.

Autonomie bedeutet dabei nicht unkontrollierte Freiheit:
Safety, Datenvertrag, Forschungsgovernance und Evidence-Gates bleiben unverändert.

## 9. Aktueller historischer Forschungsstand

Bis zum Stand 2026-09-24 existiert eine umfangreiche Folge negativer, diagnostischer und technischer
Trials. Besonders relevant für die heutige Architektur sind:

- Leverage/Long-Short: erhöhtes Exposure zeigte keinen belastbaren Vorteil und kann den Risikopfad
  massiv verschärfen.
- einfache Mean-Reversion-/Cross-Asset-Momentum-Erweiterungen: kein hinreichend robuster Zusatzbeitrag.
- Markt-/Cash-Gates: kein replizierter Schutzmechanismus.
- Trend-Ensemble: interessante Holdout-Verbesserungen, aber Research-Gates nicht erreicht.
- Per-Sleeve-Volatility-Budgeting: besonders interessanter Risikocontrol, aber noch kein
  evidence-eligible Kandidat.
- Sleeve-Volatility-Parity: Holdout nahezu unverändert, Research deutlich schwächer.
- risk-adjusted Cross-Sectional Momentum: Holdout positiv, Research klar unzureichend.
- Relative-Value-Versuche T032/T033: vor Performanceauswertung wegen Daten-Coverage invalidiert.

Einzelheiten stehen ausschließlich in den jeweiligen Reports und im Ledger.

## 10. Bereinigungsprinzip

Vor dem Löschen wird immer geprüft:

1. Wird die Datei von einem Ledger-Eintrag, Checkpoint, Workflow oder Test referenziert?
2. Ist sie die einzige Provenienz für einen historischen Befund?
3. Enthält sie unverwechselbare Daten-/Fingerprintinformationen?
4. Ist sie nur eine doppelte Kopie oder tatsächlich redundant?
5. Ist sie ein formaler Teil der Evidence-Kette oder nur ein Scratch-Artefakt?

Formale Evidence-Dateien werden nicht einfach gelöscht, nur weil das zugrunde liegende Research verworfen wurde.

## 11. Änderungsprinzip dieses Dokuments

Dieses Dokument ist bewusst kein zweiter Ledger.

Neue technische Fakten werden in ihren technischen Quellen gepflegt.
Neue Research-Ergebnisse werden im Ledger und in den Result-Checkpoints gepflegt.
Hier werden vor allem gemeinsame Absicht, Entscheidungslogik, dauerhafte Prinzipien
und aus Chats stammende Kontextinformationen festgehalten.

Damit bleibt GitHub die belastbare technische Referenz, ohne unser gemeinsames Projektgedächtnis
zu verlieren.

## 12. Agentenressourcen: Hypothesen zuerst

Kostenfreie Agentencredits werden primär für Hypothesenbildung und Forschungsdesign eingesetzt. Lokale Rechenleistung bleibt für deterministische Berechnung zuständig; bezahlte API-Nutzung bleibt deaktiviert. Copilot fungiert als nachgeordneter, schreibgeschützter Hypothesen-/Review-Agent ohne Holdout-Auswahl oder rückwirkende Optimierung. Die erste Runde ist AGENT-HYPOTHESIS-ROUND-001.
