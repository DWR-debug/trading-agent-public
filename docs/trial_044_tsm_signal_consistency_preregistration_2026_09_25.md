# Präregistrierung — Trial T-2026-09-25-044
## Repair Successor zu T043 — Unanimous 63/126/252 TSM

T043 wurde ausschließlich wegen des Coverage-Gates als DATA_INVALID geschlossen:
13/13 Symbole erfüllten die Einzelabdeckung, aber der gemeinsame Kalender enthielt
nur 3.499 statt 3.500 benötigte Zeitstempel.

T044 ist ein **reiner Coverage-Repair-Successor**. Die wissenschaftliche Hypothese,
das Signal, die Gates, die Kosten und die Holdout-Regeln bleiben unverändert.
Einziger technischer Eingriff: 3.520 Roh-Candles pro Symbol statt 3.500, damit
3.500 gemeinsame Candles gebildet werden können.

Das universum bleibt exakt:
Trend: WMT, JNJ, PG, KO, PEP, XOM, CVX, CSCO
Cross-sectional: MCD, V, ORCL, MRK, PFE

Vor Performance ist ein bestandenes Coverage-Gate zwingend. Die zusätzlichen Rohdaten
werden nur zur zeitlichen Ausrichtung verwendet; die formale Evaluation arbeitet
auf exakt 3.500 gemeinsamen Candles = 3.498 Return-Perioden = 2.798 Research + 700 Holdout.

Keine Parameter-/Threshold-/Variantensuche, keine Asset-Auswahl nach Performance,
keine Holdout-Selektion und keine Änderung bestehender Gates.

Sicherheitsvertrag: PAPER_ONLY=True; LIVE_TRADING_ENABLED=False; orders_enabled=False;
automatic_promotion=False.
