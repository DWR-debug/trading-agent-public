# Regime-/Meta-Layer – Phase 2

Die erste Regime-Komponente ist bewusst nur ein Beobachtungs- und Feature-Layer.
Sie berechnet aus bereits verfügbaren Renditen:

- annualisierte realisierte Volatilität;
- positive Asset-Breite;
- Downside-Breite;
- Cross-Sectional-Dispersion;
- mittlere paarweise Korrelation.

Es gibt bewusst noch keine automatische Regimeklassifikation. Damit kann eine
heuristische oder statistisch ungeprüfte State-Erkennung nicht versehentlich
den bestehenden Allocator beeinflussen.

## Architektur

Der sichere Pfad lautet:

historische, zeitlich verfügbare Daten -> RegimeFeatureSnapshot -> später
separat validierter MarketState -> Evidence-Gate -> Allocator.

Bis ein MarketState-Modell unabhängig validiert wurde, bleibt der vorhandene
UnknownMarketStateObserver der sichere Default und erzwingt HOLD_CASH.

## Methodische Regeln

- ausschließlich lagged/observed returns;
- keine Holdout-Nutzung zur Entwicklung des Feature-Sets;
- keine Schwellenwertsuche im Feature-Extractor;
- keine Strategie- oder Parameteränderung;
- keine Order- oder Broker-Integration.

Die Features sind damit ein reproduzierbarer Messlayer, aber noch kein Alpha-
oder Regime-Signal.