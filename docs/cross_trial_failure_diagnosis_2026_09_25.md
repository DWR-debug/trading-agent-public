# Q010 — Cross-Trial-Failure-Diagnose

## Status

DIAGNOSTIC_ONLY / COMPLETED

Q010 aggregiert die archivierte Evidence-Kette T041–T045 ohne erneute Backtests, Parameter-/Asset-Selektion oder Gateänderung.

## Provenienz

Workflow: 36119705793
Artefakt: 10856102739
Artefakt-SHA256: 9f10a27ed267870981c8f480e868967e22c4d19a8c3562c37c9690d19dcf01c2
Diagnose-Fingerprint: c11a4a2340bf4f7a9f132f53835465d57d0b12ab97770a24f3fd98492e7f9549

## Evidenzbasis

Performance-valide Trials: 4
DATA_INVALID Trials: 1
Research-Risiko-Gate wiederholt verletzt: 4/4
Control-relative Non-Deterioration verletzt: 4/4
OOS-Stabilitäts-Gate verletzt: 3/4
Holdout-DD-Gate verletzt: 3/4
Positive Holdout-Rendite vorhanden: 4/4

T043 wird wegen DATA_INVALID nicht als Performanceevidenz interpretiert.

## Interpretation

Der wiederkehrende Engpass liegt nicht primär in fehlender positiver aggregierter Rendite, sondern in robuster Risikoqualität und stabiler Nicht-Verschlechterung gegenüber dem eingefrorenen Fixed Control.

Das bedeutet nicht, dass kein Edge existiert. Es bedeutet, dass die bisher untersuchten Control- und Signalvarianten keinen belastbaren Nachweis eines verbesserten Gesamtprofils geliefert haben.

## Konsequenz

Q011 untersucht zunächst eine orthogonale Information-/Alphaquelle statt eine weitere Variante der bisherigen Risiko-, Volatilitäts-, Trendkonsistenz- oder Lifecycle-Control-Familien.

Die nächste formale Hypothese muss genau eine feste Regel enthalten, Point-in-Time-Daten verwenden, vollständig symbol-disjunkt validiert werden, Coverage vor Performance erzwingen, den Holdout blind halten und den bestehenden Evidence-Vertrag unverändert verwenden.

Im Repository ist bereits data/gdelt_events.py als GDELT-Event-Parser vorhanden. Dieser ist zunächst nur eine technische Ressource; eine konkrete formale Hypothese wird erst nach PIT-/Zuordnungsprüfung präregistriert.

## Sicherheitsstatus

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False