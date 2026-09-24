# Research Archaeology — 2026-09-24

## Zweck

Vor der Bereinigung des Projekts werden verworfene Hypothesen, diagnostische Trials und vorhandene Daten-/Artefaktinformationen
darauf untersucht, ob sie im aktuellen Entwicklungsstand noch einen belastbaren Informationswert haben.

Dies ist eine **read-only Erkenntnisphase**. Sie öffnet keine alten Trials erneut und optimiert keine verworfenen Regeln nachträglich.

## Ergebnisprinzip

Ein verworfener Trial kann gleichzeitig:

- wissenschaftlich **negativ** sein,
- technisch **wertvoll** sein,
- einen diagnostischen Mechanismus-Hinweis liefern,
- oder einen zukünftigen orthogonalen Forschungsansatz motivieren.

Deshalb wird nicht nur nach „Pass/Fail“ bereinigt.

## Bereits überprüfte neuere Evidence

| Trial | Formales Ergebnis | heutige verwertbare Spur | Umgang |
|---|---|---|---|
| T014 Long/Short/Leverage | verworfen | Exposure-Erhöhung ist kein Ersatz für einen nachgewiesenen Edge; Stress kann den Drawdown massiv erhöhen | RETAIN_NEGATIVE |
| T015 Mean Reversion | verworfen | kein stabiler Zusatzbeitrag unter Research/Rolling/Kosten | RETAIN_NEGATIVE |
| T016 Cross-Asset Momentum | verworfen | schwacher Research-Befund trotz positiver Holdout-Phase; kein belastbarer Zusatz-Edge | RETAIN_NEGATIVE / DIAGNOSTIC_ONLY |
| T022 Portfolio Risk-Parity | verworfen | hohe Holdout-PF/Return-Eigenschaften, aber Drawdown deutlich über Gate und Verschlechterungen gegenüber Fixed | SALVAGEABLE_OBSERVATION als Allokationsdiagnostik, nicht als Kandidat |
| T023 MAX Effect | verworfen | starke historische Return/PF-Werte, aber DD/OOS und präregistrierter Edge nicht ausreichend | SALVAGEABLE_OBSERVATION, keine Parameter-/Threshold-Suche |
| T024 Low Volatility | verworfen | positive Return/PF-Serie, aber der spezifische Low-vs-High-Vol-Edge ist negativ und DD hoch | RETAIN_NEGATIVE |
| T025 Marktresiduale Volatilität | verworfen | hohe Gesamtperformance und PF, aber der eigentliche Low-vs-High-Residual-Vol-Edge ist negativ; DD/OOS verfehlt | SALVAGEABLE_OBSERVATION / DIAGNOSTIC_ONLY |
| T026 Common-Market-Momentum-Gate | verworfen | Cash-Gate lieferte keinen replizierten Schutz und verschlechterte mehrere Kernmetriken | RETAIN_NEGATIVE |
| T027 TSM Ensemble | verworfen | Holdout-Return/PF/DD besser als Fixed, Research-Risiko/PF-Gates weiterhin verfehlt | SALVAGEABLE_OBSERVATION; Trend-Ensemble nur als neue unabhängige Frage |
| T028 Per-Sleeve Vol Budget | verworfen | deutlicher und konsistenter Risikobefund: Research-DD/PF und Holdout-DD/PF verbessert, trotz fehlender Gesamt-Gate-Erfüllung | **STÄRKSTE SALVAGEABLE_OBSERVATION**; als Risk-Control-Frage aufbewahren |
| T029 Sleeve Volatility Parity | DATA_INVALID | Coverage-/Kalenderproblem; keinerlei Performanceevidenz | DATA_QUALITY |
| T030 Sleeve Volatility Parity Confirmation | verworfen | Holdout nahezu unverändert, Research schlechter; liefert Kontrolle gegen Parity-These | RETAIN_NEGATIVE / DIAGNOSTIC_ONLY |
| T031 Risk-adjusted CS Momentum | verworfen | Holdout positiv, Research return/PF/DD/rolling/OOS unzureichend | RETAIN_NEGATIVE / DIAGNOSTIC_ONLY |
| T032 Relative-Value | DATA_INVALID | QQQM nur 1.493 statt 3.520 angeforderter Candles; keine Performanceaussage | DATA_QUALITY |
| T033 Relative-Value | DATA_INVALID | IEMG nur 3.496 statt 3.520 angeforderter Candles; keine Performanceaussage | DATA_QUALITY |

## Wichtigste historische Bausteine für den heutigen Entwicklungsstand

### 1. Risk-Control statt Rendite-Tuning

T028 ist ein besonders nützlicher historischer Hinweis, weil der Eingriff mehrere Risiko-/PF-Metriken
verbessert, ohne einen positiven Holdout lediglich durch Rendite-Tuning zu erzeugen.

Das Ergebnis bleibt trotzdem **nicht promotion-ready**.
Es motiviert höchstens eine spätere, neu präregistrierte Risk-/Allocation-Frage.

### 2. Exposure ist kein Ersatz für Edge

T014 ist als Negativbeweis wichtig. Das Einkommensziel darf nicht dazu führen, dass Leverage oder Shorting
als bloßer Multiplikator einer unzureichenden Strategie behandelt werden.

### 3. Positive Holdout-Befunde dürfen Forschung nicht rückwärts steuern

T027 und T031 zeigen, warum ein positiver Holdout allein nicht reicht.
Die Research-/Rolling-Evidenz entscheidet mit und schützt vor nachträglicher Auswahl.

### 4. Starke Gesamtrendite kann den behaupteten Mechanismus trotzdem nicht beweisen

T023 und T025 sind dafür besonders lehrreich:
hohe Gesamtreturns/PF können vorhanden sein, während der eigentliche präregistrierte Faktor-/Edge-Kontrast
nicht trägt und harte Risiko-/Robustheitsgates scheitern.

## Daten-/Artefaktbefunde vor Bereinigung

Die aktuelle Repository-Lage zeigt bereits mehrere Dinge, die **vor** einer Löschung erhalten bzw. geprüft werden müssen:

- T029/T032/T033 dokumentieren reale Coverage-Probleme und dürfen nicht mit Performance-Failures vermischt werden.
- Der offene T034-PR ist technisch eine Fortsetzung der Relative-Value-Linie mit EEMV als Ersatz für IEMG.
- Auf T034 werden aktuell zahlreiche ältere/unabhängige Actions-Workflows parallel ausgelöst. Das erzeugt CI-Fan-out und kann scheinbare Branch-Fehler erzeugen, obwohl die Änderung fachlich nur T034 betrifft. Dieses Governance-/Workflow-Thema sollte vor einer späteren Bereinigung verbessert werden.
- Formale Reports, Checkpoints, Ledger-Einträge, Dataset-Fingerprints und Workflow-Provenienz dürfen erst nach einer Abhängigkeitsprüfung entfernt werden.
- Scratch-/Preflight-Branches wie frühere Residual-Momentum-Versuche sind organisatorisch bereinigbar, aber ihre Erkenntnisse müssen vor Löschung als „nicht formal integriert“ dokumentiert sein.

## Was ausdrücklich nicht gemacht wird

- Keine Wiedereröffnung eines verworfenen Trials.
- Keine Parameteroptimierung aus historischen Befunden.
- Keine nachträgliche Holdout-Auswahl.
- Keine Lockerung des Datenvertrags.
- Keine Promotion des Fixed Candidate.
- Keine Live-Ausführung.

## Nächster methodischer Schritt nach der Archaeology

Erst nach Abschluss der Bestandsaufnahme:

1. Kontext-/Evidenzindex aktualisieren.
2. Formale Evidence-Dateien auf Abhängigkeiten prüfen.
3. Redundante Dokumente/Branches eindeutig klassifizieren.
4. Workflow-CI so begrenzen, dass fachfremde Workflows keine Research-Branches verschmutzen.
5. Erst danach technische Bereinigung durchführen.
6. Danach aus den **salvageable observations** neue, strikt unabhängige Forschungsfragen ableiten.

## Status

Die Archaeology ist eine Erkenntnis- und Governance-Schicht.
Die formalen Trial-Ergebnisse bleiben unverändert.
