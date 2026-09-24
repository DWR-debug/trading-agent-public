# Präregistrierung: Trial T-2026-09-24-038 — Cross-Asset Network Momentum

## Forschungsfrage

Kann ein fest definierter, ausschließlich aus vergangenen Cross-Asset-Lead-Lag-Beziehungen abgeleiteter
Network-Momentum-Zustand den bestehenden eigenpreis-basierten Trend-Signalpfad auf einem neuen,
vollständig symbol-disjunkten Multi-Asset-Datensatz verbessern?

Die Intervention ist eine neue Informationsquelle, nicht eine Suche über bestehende Trendparameter.

## Feste Validierungsbasis

`EIRL`, `ENZL`, `NORW`, `EDEN`, `FXF`, `FXC`, `CEW`, `EIDO`, `SCHO`, `MINT`, `COMT`, `RWX`

- 3.500 Research-Candles je Symbol
- 3.498 gemeinsame PIT-Returnperioden
- 2.798 Research-Returns / 700 blinder Holdout
- vollständig symbol-disjunkt
- keine Auswahl anhand des Holdouts

## Präregistrierte Network-Regel

Die bestehende SMA-50/200-Long/Flat-Trendlogik bildet die Referenz.

Der Challenger verändert ausschließlich die Richtungsinformation:

1. Für jedes Asset wird der eigene 252-Session-Cumulative-Return mit 21-Session-Skip bestimmt.
2. Für jeden Peer wird derselbe Trendreturn um exakt 21 Sessions nach hinten verschoben.
3. Für jede Ziel-/Peer-Kombination wird aus den vorherigen 252 abgeschlossenen Sessions die lineare
   Korrelation zwischen Zieltrend und verzögertem Peer-Trend bestimmt.
4. Nur positive Korrelationen werden als positive Netzwerk-Links berücksichtigt.
5. Der Network-Score des Zielassets ist der mit diesen positiven Korrelationen gewichtete Mittelwert
   der Peer-Trend-Signale.
6. Ohne positiven Link ist der Network-Score 0.
7. Die finale Richtung ist ein fixer 50/50-Blend aus eigenem 252/21-Trend und Network-Score.
8. Inverse Volatilitätsgewichtung, monatliche Rebalancierung, 10%-Volatilitätsbudget sowie Kosten-
   und Ausführungssemantik der Referenz bleiben unverändert.

Keine Suche über Lookbacks, Lags, Korrelationsschwellen, Peer-Anzahl oder Mischungsverhältnis.

## Point-in-Time

Alle Network-Schätzungen verwenden ausschließlich Informationen vor dem jeweiligen
Rebalancing-Zeitpunkt. Der aktuelle Return wird nicht für seine eigene Netzwerkkorrelation verwendet.

## Gates

Es gelten die regulären Projekt-Gates plus der Nicht-Verschlechterungsvertrag gegenüber dem Fixed Candidate:
positive Research-Rendite, Research-DD <=10%, PF >=1,10, Rolling-PF >=1,10,
>=50% profitable Rolling-Fenster, durchschnittlicher Rolling-DD <=10%, OOS/Research >=0,25,
positive Holdout-Rendite, Holdout-PF >=1,10, Holdout-DD <=10% sowie nichtnegative 1,5x/2x Kostenstress-
Holdout-Rendite.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Keine Orders und keine automatische Promotion.
