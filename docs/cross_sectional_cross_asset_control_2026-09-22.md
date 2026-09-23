# Cross-Sectional Momentum auf demselben Cross-Asset-Universum

## Fragestellung

Die 12-1-Cross-Sectional-Momentum-Regel wurde bereits auf zwei unabhängigen
Aktienuniversen positiv repliziert. Dieser Control prüft dieselbe Regel nun auf
dem exakt gleichen achtteiligen Cross-Asset-Universum, auf dem die neue
Time-Series-Trendarchitektur untersucht wurde.

Damit werden beide Mechanismen direkt auf derselben Datenbasis vergleichbar.

## Vorregistrierte Regel

- Formation: 252 Handelstage
- Skip: 21 Handelstage
- Rebalance: alle 21 Handelstage
- Top-2
- Long-only
- gleichgewichtete Top-2-Positionen
- Close(t) -> Open(t+1) -> Open(t+2)
- Basis- und 2x-Kostenstress
- keine Optimierung
- keine Selection-Profile
- keine Gate-Änderung

## Universum

SPY, EFA, TLT, GLD, DBC, UUP, QQQ, IWM.

Das Universum umfasst Aktien, internationale Aktien, Fixed Income,
Rohstoffexposure und Währungsexposure.

## Auswertung

- 3.500 gemeinsame Tages-Candles
- 2.800 Research
- 700 Holdout
- fünf Rolling-Fenster innerhalb des Research-Abschnitts
- Buy-and-Hold und SMA 50/200 als feste Referenzen

Das Ergebnis dient ausschließlich der Mechanismusdiagnostik. Eine positive
Cross-Sectional-Auswertung verändert keine Produktionsstrategie.

## Sicherheitszustand

Paper-Only.
Live-Trading deaktiviert.
Keine Orders.
