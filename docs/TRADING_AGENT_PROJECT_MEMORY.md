# Trading-Agent Projektgedächtnis — Ziel, 30-Tage-Meilenstein und Mutkurve

Stand: 2026-09-25

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

500 EUR bleibt das Referenz-/Startkapital für spätere Planung; daraus wird keine Prognose über spätere Rendite oder finanzielle Versorgung abgeleitet.
