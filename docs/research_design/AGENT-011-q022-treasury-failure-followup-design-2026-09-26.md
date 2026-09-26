# AGENT-011 / Q022 — Treasury Failure Follow-up Design

Stand: 2026-09-26

## Zweck

Q022 übersetzt die abgeschlossene Q021-Diagnose in klar abgegrenzte, später separat
präregistrierbare Folgefragen. Q022 ist **DESIGN_ONLY**. Es erzeugt keine neue
Performance-Evidence und öffnet Q020 nicht erneut.

Die Grundlage ist ausschließlich die kanonische Q019/Q020-Evidence und die
Q021-Diagnose. Q020 bleibt unverändert und wird nicht nachoptimiert.

## Verbindliche Governance

Für jede spätere Folgeuntersuchung gilt:

- neues, vollständig symbol-disjunktes Validierungsuniversum;
- neue, unveränderliche Präregistrierung vor Daten-/Performanceauswahl;
- Coverage-/PIT-Preflight vor jeder Performanceauswertung;
- Holdout bleibt bis zur formalen Evaluierung unberührt;
- keine rückwirkende Auswahl von Parametern, Assets, Schwellen, Varianten oder Horizonten;
- unveränderte Research-/Risk-Gates, sofern eine spätere Präregistrierung nicht ausdrücklich eine
  wissenschaftlich begründete, separate Governance-Studie ist;
- Performance- und Diagnoseergebnisse werden nur anhand verifizierter Workflow-/Artifact-Provenienz
  in die Evidence übernommen;
- kein Live-Trading und keine automatische Promotion.

## Gemeinsamer Ausgangspunkt

Q021 dokumentiert fünf beobachtete Failure-Signaturen und vier noch nicht aufgelöste
Mechanismusklassen:

- breite negative Evidenz statt eines isolierten Holdout-Ausreißers;
- negative Rolling-Eigenschaften;
- Verschlechterung unter realistisch höheren Kosten;
- geringe Ereignisdichte bzw. Event-Aggregation;
- formal erfüllter PIT-Datenvertrag bei weiterhin offener wirtschaftlicher Timingfrage.

Unaufgelöst bleiben Richtung/Signinterpretation, Eventtyp/Konzentration, zeitliche Regimeabhängigkeit
und Signal-Sparsität. Q022 bewertet diese Mechanismen nicht gegeneinander.

## Ungerankte Follow-up-Hypothesen

### H1 — Directional inversion

**Frage:** Ist die ex ante fixierte Vorzeichenkonvention des Q020-Signals möglicherweise invertiert?

**Spätere Prüfregel:** Exakt dieselbe Q019-Signaldefinition, jedoch mit fest invertiertem Handelssignal
(+1 wird -1 und -1 wird +1; 0 bleibt 0). Keine sonstige Änderung der Handelsregel.

**Benötigte Evidenz:** neues symbol-disjunktes Marktuniversum und erneuter Coverage-/PIT-Vertrag.

**Falsifikation:** Der invertierte feste Mechanismus zeigt auf dem neuen Datensatz keinen vorab definierten
inkrementellen Erkenntnisgewinn gegenüber der unveränderten Originalrichtung bzw. verletzt den
festgelegten Nicht-Verschlechterungs-/Evidence-Vertrag.

**Ausgeschlossen:** nachträgliche Wahl zwischen Original und Inversion anhand des Ergebnisses.

### H2 — Release-timing mismatch

**Frage:** Repräsentiert `record_date` den tatsächlich handelbaren Informationszeitpunkt hinreichend?

**Spätere Prüfregel:** Verwendung einer vorab definierten offiziellen Veröffentlichungs-/Zeitstempelquelle.
Die Handelssession wird ausschließlich aus diesem ex ante fixierten PIT-Zeitpunkt abgeleitet.

**Benötigte Evidenz:** deterministisch zugängliche, zeitlich belastbare offizielle Veröffentlichungszeitstempel.
Sind solche Zeitstempel nicht reproduzierbar verfügbar, gilt die Studie als `DATA_INSUFFICIENT`.

**Falsifikation:** Keine relevante PIT-Abweichung gegenüber `record_date` nach der ex ante definierten
Zeitregel oder keine Verbesserung der vorab fixierten Timing-Diagnostik.

**Ausgeschlossen:** Auswahl eines günstigen Zeitpunkts nach Sichtung von Returns.

### H3 — Event concentration / aggregation

**Frage:** Wird ein großer Teil der beobachteten Wirkung von wenigen Events oder aggregierten Event-Tagen getragen?

**Spätere Prüfregel:** Rein diagnostische Attribution auf Event-/Session-Ebene mit vollständig erhaltener
Mapping- und Aggregationsprovenienz. Zu messen sind mindestens Beitragskonzentration, Eventhäufigkeit,
Anteil der besten/schlechtesten Einzelereignisse und der Anteil aggregierter Sessions.

**Benötigte Evidenz:** reproduzierbare Event-Level-Zuordnung einschließlich aller gleichzeitig gemappten Events.

**Falsifikation:** Beitragsstruktur bleibt über die vorab definierte Eventpopulation breit verteilt und
aggregierte Sessions zeigen kein vorab definiertes Konzentrationsmuster.

**Charakter:** Primär diagnostisch; ein auffälliger Konzentrationsbefund ist kein Profitabilitätsnachweis.

### H4 — Temporal regime dependence

**Frage:** Verändert sich die Signalrelation zwischen ex ante definierten Marktphasen?

**Spätere Prüfregel:** Nur externe bzw. vor dem Return-Sample definierte Regimevariablen; keine
nachträglich aus Q020-Returns konstruierten Klassen.

**Benötigte Evidenz:** reproduzierbare, PIT-kompatible Regimequelle und vorab festgelegte Klassengrenzen.

**Falsifikation:** Keine reproduzierbare Differenz zwischen den festgelegten Regimeklassen oder fehlende
Daten-/PIT-Basis.

**Ausgeschlossen:** Regimegrenzen nachträglich so wählen, dass eine gewünschte Performance entsteht.

### H5 — Cost fragility

**Frage:** Wie empfindlich ist der Mechanismus gegenüber Transaktionskosten?

**Spätere Prüfregel:** Fixes Kostenraster aus dem bestehenden Vertrag: Base, 1.5x und 2x der bereits
definierten Fee-/Slippage-Annahmen. Keine zusätzliche Auswahl des günstigsten Szenarios.

**Benötigte Evidenz:** identische feste Handelsregel und reproduzierbare Kostenrechnung.

**Falsifikation:** Der Befund bleibt qualitativ unverändert oder zeigt keine klar definierte ex ante
Kostenabhängigkeit.

**Ausgeschlossen:** Auswahl oder Präsentation nur des kostengünstigsten Szenarios als Hauptbefund.

### H6 — Sparse-signal identifiability

**Frage:** Reicht die Ereignisdichte aus, um den Mechanismus statistisch sinnvoll zu identifizieren?

**Spätere Prüfregel:** Vorab definierte Coverage-/Ereignis-Mindestanforderungen und getrennte Betrachtung
von Gesamtdichte, Verteilung über Zeitabschnitte und Beitragskonzentration.

**Benötigte Evidenz:** neues unabhängiges Eventsample sowie vollständige Mapping-/Coverage-Provenienz.

**Falsifikation:** Ereignisdichte oder zeitliche Verteilung unterschreiten die ex ante definierten
Mindestanforderungen oder die beobachtete Wirkung bleibt von wenigen Ereignissen dominiert.

**Ausgeschlossen:** nachträgliche Ausweitung oder Auswahl des Ereignisfensters nach günstigen Ergebnissen.

## Auswahl- und Übergaberegel

Q022 selbst rankt H1–H6 nicht. Keine der sechs Hypothesen erhält hier einen Selektionsstatus.

Der Übergang zu einem formalen Test erfolgt erst über eine **separate Präregistrierung**, die genau
eine dieser Fragen fixiert und vor Ausführung einen neuen Coverage-/PIT-Vertrag sowie ein neues
symbol-disjunktes Universum festlegt.

## Definition of Done

Q022 ist abgeschlossen, wenn:

1. alle sechs Mechanismen reproduzierbar beschrieben sind;
2. jede Folgefrage eine explizite Daten-/PIT-Anforderung und Falsifikationsregel besitzt;
3. keine Hypothese gerankt oder selektiert wurde;
4. Q020-Evidence unverändert bleibt;
5. keine Performance- oder Holdout-Ausführung durch Q022 autorisiert wird;
6. die maschinenlesbare Designfassung und Regressionstests den gleichen Governance-Status ausdrücken.

Sicherheitsinvarianten:

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`  
`automatic_promotion=False`
