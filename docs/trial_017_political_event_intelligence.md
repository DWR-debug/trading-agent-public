# Trial 017 — Political Event Intelligence

Der erste Trial prüft ausschließlich, ob politische/geopolitische Ereignisse
punktgenau strukturiert und ohne Same-Day-Leakage mit späteren Marktrenditen
verbunden werden können. Er ist ein deskriptiver Control, kein
Produktionskandidat.

GDELT 2.0 Event Exports liefern EventCode, EventBaseCode, EventRootCode,
QuadClass, GoldsteinScale sowie Medienaufmerksamkeitsfelder. Für zeitkritische
Verarbeitung wird DATEADDED in UTC verwendet.

Feste Features:
event_count, material_conflict_count, verbal_conflict_count,
material_cooperation_count, negative_goldstein_sum,
mention_weighted_conflict, source_count, mean_tone, conflict_flag.

Markt-Basis: SPY, TLT und GLD adjusted close. Tag D wird ausschließlich mit
der nächsten verfügbaren Marktrendite und einem festen Fünf-Tage-Horizont
verbunden.

Keine Parameter-, Schwellenwert- oder Holdout-Selektion im Baseline-Trial.
