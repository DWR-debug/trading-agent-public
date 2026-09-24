# T040 Failure-Diagnose — 2026-09-24

## Zweck

Diese Diagnose leitet aus der abgeschlossenen T040-Evidenz eine reproduzierbare Failure-Signatur
ab. Sie führt keine neue Performanceauswertung durch und verändert keine Strategieparameter.

## Festgestellte Failure-Signatur

T040 ist ein breiter negativer Befund:

- Research-Rendite: **-33,96 %**
- Research-Max-Drawdown: **41,45 %**
- Research-PF: **0,907**
- 5/5 Research-Rolling-Fenster nicht profitabel
- minimale Rolling-PF: **0,817**
- durchschnittlicher Rolling-DD: **17,77 %**
- Holdout-Rendite: **-11,99 %**
- Holdout-PF: **0,923**
- Holdout-DD: **17,08 %**
- Holdout bei 1,5x Kosten: **-15,81 %**
- Holdout bei 2x Kosten: **-19,47 %**

Die feste SMA-50/200-Kontrolle war ebenfalls negativ, aber weniger negativ:

- Research-Rendite: **-21,15 %**
- Research-Max-DD: **32,63 %**
- Research-PF: **0,948**
- Holdout-Rendite: **-11,13 %**
- Holdout-PF: **0,926**

## Kontroll-relative Diagnose

Der Challenger verschlechtert gegenüber der fest definierten Kontrolle:

- Research-Rendite um **-12,81 Prozentpunkte**
- Research-Max-DD um **+8,82 Prozentpunkte**
- Research-PF um **-0,041**
- Holdout-Rendite um **-0,88 Prozentpunkte**
- Holdout-PF um **-0,003**

Der Holdout-Max-DD ist beim Challenger geringfügig niedriger. Das reicht nicht aus, um
die übrigen klar verfehlten Gates auszugleichen.

## Was daraus nicht geschlossen werden darf

Der Befund zeigt nicht, dass Cross-Asset-Momentum allgemein unwirksam ist.
Er betrifft den exakt präregistrierten T040-Mechanismus, das festgelegte Universe und
den verwendeten Daten-/Ausführungsvertrag.

Es gibt keinen nachträglichen Parametervergleich und keine Holdout-basierte Auswahl.

## Konsequenz

T040 wird nicht nachoptimiert und nicht in Produktion übernommen.

Der nächste Forschungsblock ist **Adversarial Failure-Diagnose**:
Ursachen und Versagensmuster sollen aus bereits vorhandener Evidenz strukturell untersucht
werden, bevor eine neue Performancehypothese präregistriert wird.

Geeignete Diagnoseachsen sind feste, nicht-selektive Auswertungen von:

- Kontroll-relative Verschlechterung,
- Drawdown-/Rolling-Failure-Muster,
- Kostenempfindlichkeit,
- Exposure-/Konzentrationsverhalten,
- Anteil der negativen Fenster,
- Zusammenspiel von Signal und Risk Layer,
- historische salvageable Beobachtungen im gemeinsamen Evidence-Vertrag.

Keine dieser Diagnosen darf automatisch neue Parameter oder Assets auswählen.

## Provenienz

Quelle:
`research/evidence/trial_040_network_momentum_repair_2026_09_24.json`

Formaler Report-Fingerprint:
`912d51447862ba7118dacde2f8acba6c3cce407adec64ea10cbf3aa48661bb65`

Diagnose ist rein ableitend und hat keinen Promotionscharakter.

## Sicherheit

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `orders_enabled=False`
- `automatic_promotion=False`
- bezahlte Agenten-/API-Nutzung: **0 USD**
