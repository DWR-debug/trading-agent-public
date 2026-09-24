# Präregistrierung: Trial T-2026-09-24-039 — Cross-Asset Network Momentum

## Forschungsfrage

Kann ein fest definierter, ausschließlich aus vergangenen Cross-Asset-Lead-Lag-Beziehungen abgeleiteter
Network-Momentum-Zustand den bestehenden eigenpreis-basierten Trend-Signalpfad auf einem neuen,
vollständig symbol-disjunkten Multi-Asset-Datensatz verbessern?

## Feste Validierungsbasis

`EIRL`, `ENZL`, `NORW`, `EDEN`, `FXF`, `FXC`, `CEW`, `EIDO`, `SCHO`, `MINT`, `DBO`, `RWX`

- 3.500 Research-Candles je Symbol
- 3.498 gemeinsame PIT-Returnperioden
- 2.798 Research-Returns / 700 blinder Holdout
- vollständig symbol-disjunkt
- keine Auswahl anhand des Holdouts

## Network-Regel

Der bestehende SMA-50/200-Long/Flat-Trend ist die Referenz.

Der Challenger ersetzt ausschließlich die Richtungsinformation:
1. eigener 252-Session-Cumulative-Return mit 21-Session-Skip;
2. jeder Peer-Return um exakt 21 Sessions nach hinten verschoben;
3. lineare Lead-Lag-Korrelation je Ziel/Peer aus den vorherigen 252 abgeschlossenen Sessions;
4. nur positive Korrelationen;
5. korrelationsgewichteter Mittelwert der positiven Peer-Signale;
6. ohne positive Links Network-Score 0;
7. fixe 50/50-Kombination aus Eigen- und Network-Signal;
8. übrige Portfolio-, Volatilitäts-, Rebalance- und Kostenregeln unverändert.

Keine Suche über Lookbacks, Lags, Schwellen, Peeranzahl oder Gewichte.

## PIT / Governance

Alle Netzwerkmessungen nutzen ausschließlich bereits abgeschlossene Informationen.
Keine Holdout-Selektion, kein Tuning, keine Produktionseinbindung.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
