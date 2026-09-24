# Externe Architektur-Inspirationen — 2026-09-24

RD-Agent(Q): geschlossener Zyklus Hypothese -> Experiment -> Ausführung ->
Feedback -> neue Hypothese. Adaptiert in unsere Research-Queue und Evidence-
Struktur.

Qlib: modulare Portfolio-/Risk-Optimierung. Adaptiert als getrennte Risk-Overlay-
Schicht, ohne bestehende Alpha-Gates zu verändern.

FinRL-Trading: Weight-Centric Selection -> Allocation -> Timing -> Risk Overlay.
Adaptiert als Exposure-Vertrag zwischen unseren Modulen.

QuantConnect LEAN: Trennung von Alpha, Portfolio Construction, Execution und Risk.
Adaptiert in strategy_allocator, agent_coordinator und risk_overlay.

Es wird kein fremder Code und keine fremde Performance als eigene Evidenz
übernommen.
