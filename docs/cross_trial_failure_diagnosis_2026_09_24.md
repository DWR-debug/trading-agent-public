# Cross-Trial Failure-Diagnose — 2026-09-24

## Quelle und Scope

Diese Diagnose ist rein ableitend. Sie verwendet ausschließlich die archivierten Ledger-Einträge
T022, T023, T025, T027 und T028. Es erfolgt kein Re-Backtest, keine Parameter- oder Asset-Auswahl
und keine Holdout-Auswahl.

## Wiederkehrende Muster

### P1 — Wiederkehrendes Risiko-Gate-Versagen

Alle fünf untersuchten historischen Trials verfehlten mindestens ein hartes Research-Risiko-Gate.
Das ist unabhängig davon relevant, ob einzelne Rendite- oder PF-Kennzahlen attraktiv aussahen.

### P2 — Mechanismus-Edge kann hinter hohen Aggregatrenditen scheitern

T023 und T025 erzielten attraktive absolute Renditemetriken, verfehlten aber mindestens einen
mechanismusbezogenen Edge- oder OOS-Stabilitäts-Gate. Damit bleibt die operative Ursache nicht
mit einer hohen Gesamt-Rendite allein geklärt.

### P3 — Holdout ist kein Rettungsmechanismus

Mehrere Trials hatten positive oder vergleichsweise attraktive Holdout-Kennzahlen und wurden trotzdem
wegen früherer Research-, Rolling-, OOS-, Risiko- oder Mechanismus-Gates verworfen. Das bestätigt die
Reihenfolge des Evidence-Vertrags: Der Holdout bestätigt, er repariert keinen früheren Fehler.

### P4 — Risk-Control kann interessant sein, ohne Alpha zu beweisen

T028 zeigt eine konkrete, kontroll-relative Risikobeobachtung: geringere Drawdowns und leicht bessere
Profit-Factor-Metriken gegenüber der festen Kontrolle. Die harten Research-Risiko-/PF-Gates wurden
jedoch weiterhin verfehlt. T028 ist deshalb Motivation für eine neue Risk-Control-Hypothese, kein
Promotion-Beleg.

## Konsequenz für die Forschung

Die Queue wechselt nicht zurück in Network-Momentum-Tuning.

Der nächste formale Entwicklungsblock lautet:

**Neue, vollständig präregistrierte Portfolio-Risk-Control-/Allocation-Hypothese auf einem frischen,
vollständig symbol-disjunkten Validierungsuniversum.**

Dabei gilt:

- T028 liefert nur die Motivation.
- Asset-Auswahl erfolgt ausschließlich vorab bzw. per Coverage-only Discovery.
- Keine Performance-Selektion.
- Kein Holdout-Selection.
- Bestehende Evidence-Gates bleiben unverändert.
- Keine automatische Promotion.

## Sicherheit

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
orders_enabled=False  
automatic_promotion=False  
bezahlte Agenten-/API-Nutzung: 0 USD

## Provenienz

Quelle:
`research/evidence/trial_ledger.json`

Diagnose-Fingerprint:
`b3c4444f84d75d0dcea6ede834b55f1576732835d5af329bd4cc85a0484612d2`
