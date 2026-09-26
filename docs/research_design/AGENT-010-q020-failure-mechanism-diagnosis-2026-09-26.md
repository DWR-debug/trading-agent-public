# AGENT-010 / Q021 — Q020 Treasury Auction Failure-Mechanism Diagnosis
Stand: 2026-09-26
Status: DIAGNOSTIC_ONLY / NOT A NEW PERFORMANCE TRIAL

## Scope

Diese Diagnose verwendet ausschließlich bereits kanonisch gespeicherte Q019-/Q020-Evidence. Sie führt keine neue P&L-Berechnung, kein Retuning, keine Parameter-, Asset-, Threshold-, Horizon- oder Variantensuche und keine Holdout-Auswahl durch.

Ziel ist die Trennung von:
1. beobachteten Failure-Signaturen,
2. noch offenen mechanistischen Erklärungen,
3. später separat präregistrierbaren, ungerankten Folgehypothesen.

## Provenienz

Q020:
- Trial: `T-2026-09-26-046R1-PERFORMANCE`
- Workflow: `36243099900`
- Artifact: `10905988662`
- Artifact SHA256: `sha256:d219a32546752d62b09a9cf17fde147f620efe3a3ae524c840b4a79495d2cfc1`
- Result fingerprint: `0ee05b7933572b6f5e9307436e87844ff6ca92180d00e4139da0814e231b9952`
- Frozen snapshot fingerprint: `70cff5df1b92f4f7db2ea09bdc9999abff93dd4230ad4ea5df6e5da204076ef8`

Q019:
- Workflow: `36238205065`
- Artifact: `10905325799`
- Contract fingerprint: `13072dbed7d60684f4a4fb8a3de69555cae83c66f3cfdfb603b9ed2a4b1c225b`
- Signal fingerprint: `8af45e4eb7267266da10eb28cf5287eea1ff3572f38736382f1b004abf86c208`

## Beobachtete Befunde

### B1 — Die negative Evidenz ist breit, nicht nur ein Holdout-Ausreißer

Q020 erzielte im Basis-Szenario:
- Research Return: -18.896%
- Research Max Drawdown: 21.019%
- Research Profit Factor: 0.294
- Holdout Return: -1.571%
- Holdout Max Drawdown: 2.752%
- Holdout Profit Factor: 0.679

Damit liegt die Schwäche sowohl in der Research- als auch in der Holdout-Periode. Der Holdout ist weniger negativ als die Research-Periode, aber kein positiver Gegenbefund.

### B2 — Alle fünf Rolling-Fenster sind negativ

Die fünf Research-Rolling-Fenster haben Returns von:
- -0.385%
- -1.865%
- -5.762%
- -6.494%
- -5.849%

Die zugehörigen Profit Factors sind sämtlich unter 1.0: 0.900, 0.640, 0.051, 0.108 und 0.143.

Das ist ein klarer zeitlicher Failure-Befund innerhalb des bereits autorisierten festen Laufs. Es beweist für sich allein noch keine konkrete Marktregimeursache. Auffällig ist aber, dass die schlechteren Verluste in den späteren drei Research-Fenstern liegen.

### B3 — Die Kosten-Sensitivität verschlechtert einen bereits negativen Befund systematisch

Von Basis zu 1.5x und 2x Stress verschlechtert sich die Research-Performance weiter:
- Return: -18.896% → -26.680% → -33.726%
- Max Drawdown: 21.019% → 28.063% → 34.489%
- Profit Factor: 0.294 → 0.166 → 0.092

Im Holdout wird ebenfalls jede zusätzliche Kostenstufe negativer.

Der Befund zeigt Kostenfragilität. Er isoliert jedoch nicht, welcher Anteil der negativen Brutto-Wirkung durch Kosten versus Signalrichtung verursacht wird.

### B4 — Das Signal ist ereignisarm und aggregiert an mindestens einer Sitzung

Q019 weist 88 signal-bearing Events aus. Q020 verwendet 87 aktive Signal-Sessions und 83 Trade-Days.

Q020 erlaubt bei mehreren Events am selben Handelstag die feste Regel “summe der Event-Signale, danach Vorzeichen”. Die Differenz zwischen 88 Signal-Events und 87 aktiven Signal-Sessions ist deshalb mechanistisch relevant und muss in einer späteren Replikation explizit kontrolliert werden. Aus den aktuellen Summary-Artefakten lässt sich nicht ableiten, ob diese Aggregation einen materiellen Beitrag zur Performance verursacht.

### B5 — Der Point-in-Time-Datenvertrag ist technisch erfüllt, aber die wirtschaftliche Timingfrage bleibt offen

Q019:
- 89/89 Rohzeilen valide
- 89/89 Events auf die erste XNYS-Session nach `record_date` gemappt
- 0 terminal events
- 0 Fehler

Die technische PIT-Abbildung ist damit validiert. Das löst aber nicht die ökonomische Intraday-Timingfrage: `record_date` enthält keine exakte Veröffentlichungsuhrzeit. Deshalb ist aus der vorhandenen Evidence nicht beweisbar, dass der Markt die Information zum angenommenen Entry-Zeitpunkt noch nicht eingepreist hatte oder dass die Richtung bereits bekannt war.

## Nicht beobachtete / nicht ausreichend identifizierte Failure Modes

### U1 — Richtung / Signinterpretation

Die feste Regel ist:
positive Veränderung des 10Y Bid-to-Cover → +1,
negative Veränderung → -1.

Die aktuelle Evidence zeigt, dass diese feste Richtungszuordnung nicht funktioniert hat. Sie zeigt aber nicht, ob die entgegengesetzte wirtschaftliche Interpretation korrekt wäre.

### U2 — Eventtyp-/Konzentrationsproblem

Der Q019-Vertrag bestätigt die 10Y-Auktionsserie, aber das Q020-Summary-Artefakt enthält keine ausreichende event-level Attribution nach Auktionstyp, Kalenderposition oder einzelnen Event-Clustern.

Eine Konzentration auf wenige Events kann daher aktuell nicht quantifiziert werden, ohne über den zugelassenen Diagnoseumfang hinaus neue Auswertungen vorzunehmen.

### U3 — Regimeabhängigkeit

Die Rolling-Signatur ist zeitlich asymmetrisch, aber die aktuellen Artefakte enthalten keine formal vorab definierten Regimeklassen. Deshalb darf aus den Rolling-Fenstern nicht rückwirkend ein bevorzugtes Regime konstruiert werden.

### U4 — Signal-Sparsität / Stichprobengröße

88 signalisierte Events über rund 3.500 Handelstage bedeuten eine sehr geringe Signalaktivität. Die aktuelle Evidenz kann daher ein strukturelles Problem der Signalrichtung, der Informationsqualität und der statistischen Identifizierbarkeit nicht vollständig auseinanderhalten.

## Ungerankte Folgehypothesen für spätere Präregistrierungen

### H1 — Directional inversion

**Mechanismus:** Die wirtschaftliche Reaktion auf eine Veränderung des Bid-to-Cover könnte der aktuell fixierten Vorzeichenkonvention entgegengesetzt sein.

**Messbare Vorhersage:** Eine später vorab fixierte Replikation mit exakt invertiertem Vorzeichen zeigt gegenüber der Originalregel eine konsistente Verbesserung auf einem vollständig neuen, symbol-disjunkten Universum.

**Falsifikation:** Kein vorab definierter Verbesserungstatbestand auf dem neuen unabhängigen Datensatz.

**Benötigt:** identischer Q019-Datenvertrag, neue unabhängige Marktgeometrie, separate Preregistration.

### H2 — Release-timing mismatch

**Mechanismus:** Das Datum des offiziellen Records ist nicht hinreichend, um den tatsächlich handelbaren Informationszeitpunkt im Tagesverlauf abzubilden.

**Messbare Vorhersage:** Eine spätere, vorab fixierte Intraday-PIT-Zeitregel verändert die Signalverfügbarkeit in einer systematischen, ex ante definierten Weise.

**Falsifikation:** Keine relevante PIT-Differenz oder keine Verbesserung der vorab fixierten Timing-Metriken.

**Benötigt:** belastbare Veröffentlichungszeitstempel oder eine alternative offizielle PIT-Zeitquelle.

### H3 — Event concentration / aggregation

**Mechanismus:** Die Gesamtwirkung könnte von wenigen Events bzw. Event-Clustern oder der Mehrfach-Event-Aggregation auf einzelnen Handelstagen dominiert werden.

**Messbare Vorhersage:** Eine spätere, vorab definierte Event-level Attribution zeigt eine klar abgegrenzte Konzentrationssignatur.

**Falsifikation:** Wirkung bleibt über die gesamte Eventpopulation hinreichend verteilt; Aggregations-Tage tragen keinen vorab definierten dominanten Anteil.

**Benötigt:** vollständige Event-Level-Provenienz mit eindeutiger Mapping- und Aggregationshistorie.

### H4 — Temporal regime dependence

**Mechanismus:** Die Signalrelation könnte zwischen Marktphasen instabil sein.

**Messbare Vorhersage:** Vorab definierte, nicht datengetriebene Regimeklassen zeigen unterschiedliche, reproduzierbare Signalreaktionen.

**Falsifikation:** Keine reproduzierbare Differenz zwischen den vorab festgelegten Regimeklassen.

**Benötigt:** externe oder ex ante definierte Regimevariablen; keine nachträgliche Klassengenerierung aus Q020-Returns.

### H5 — Cost fragility

**Mechanismus:** Ein kleiner oder nicht vorhandener ökonomischer Rohvorteil kann durch realistische Kosten vollständig zerstört werden.

**Messbare Vorhersage:** Eine spätere feste Kosten-Sensitivitätsmatrix zeigt eine scharfe, vorab definierte Abhängigkeit der Signifikanz vom Kostenband.

**Falsifikation:** Der Befund bleibt bei einem vorab definierten sehr niedrigen Kostenband qualitativ unverändert.

**Benötigt:** ex ante fixiertes Kostenraster; keine Auswahl des günstigsten Szenarios.

### H6 — Sparse-signal identifiability

**Mechanismus:** Die Ereignisdichte ist möglicherweise zu gering, um aus dem festen Signal eine stabile, breit diversifizierte Beziehung abzuleiten.

**Messbare Vorhersage:** In einer späteren unabhängigen Replikation bleiben Frequenz, Event-Abdeckung und Fehlerstruktur außerhalb eines vorab definierten Mindestbereichs oder die Performance bleibt von wenigen Einzelereignissen dominiert.

**Falsifikation:** Ausreichende Event-Dichte und breite Beitragsverteilung bei reproduzierbarer Wirkung.

**Benötigt:** neue unabhängige Events und eine ex ante definierte Mindest-Coverage.

## Research-Governance

Keine der H1–H6 wird hier ausgewählt, gerankt oder formal getestet.

Die nächste zulässige Aktion ist eine separate Präregistrierung mit:
- neuem unabhängigen Datensatz/Universum,
- exakt fixierter Regel,
- unverändertem Safety-/Evidence-Vertrag,
- klarer Falsifikationsregel,
- unberührtem Holdout bis zur formalen Evaluierung.

Q020 selbst wird auf der bestehenden Evidence nicht nachoptimiert.

Safety:
`PAPER_ONLY=True`
`LIVE_TRADING_ENABLED=False`
`orders_enabled=False`
`automatic_promotion=False`
