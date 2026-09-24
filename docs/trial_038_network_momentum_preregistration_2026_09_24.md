# Präregistrierung: Trial T-2026-09-24-038 — Cross-Asset Network Momentum

## Forschungsfrage

Kann ein fest definierter, ausschließlich aus vergangenen Cross-Asset-Lead-Lag-Beziehungen abgeleiteter
Network-Momentum-Zustand den bestehenden eigenpreis-basierten Trend-Signalpfad auf einem neuen,
vollständig symbol-disjunkten Multi-Asset-Datensatz verbessern?

Die Intervention ist bewusst eine **Informationsquelle**, keine Suche über vorhandene Trendparameter.

## Motivation

Li & Ferreira (2025) untersuchen Network Momentum als Ergänzung zu univariaten Trendindikatoren und
berichten Verbesserungen gegenüber rein univariaten Trend-Signalen. Das ist Motivation für eine
eigenständige Prüfung, nicht Evidenz für unsere ETF-Implementierung.

## Feste Validierungsbasis

`EIRL`, `ENZL`, `NORW`, `EDEN`, `FXF`, `FXC`, `CEW`, `MINT`, `SCHO`, `MINT`, `COMT`, `RWX`

- 3.500 Research-Candles je Symbol
- 700 blinder Holdout
- 3.498 gemeinsame PIT-Returnperioden nach dem bestehenden 2-Candle-Warm-up
- vollständig symbol-disjunkt zu den bestehenden formalen Universen
- keine Auswahl anhand des Holdouts

## Fest definierte Network-Regel

Die bestehende SMA-50/200-Long/Flat-Trendlogik bleibt die Referenz.

Der Network-Momentum-Challenger ersetzt **nur** die Trendrichtung:

1. Für jedes Asset wird der eigene 252-Session-Cumulative-Return mit 21-Session-Skip berechnet.
2. Für jedes andere Asset wird derselbe Trendreturn um exakt 21 Sessions nach hinten verschoben.
3. Über die vorherigen 252 abgeschlossenen Sessions wird für jedes Paar eine lineare Lead-Lag-Korrelation
   zwischen Zieltrend und um 21 Sessions verschobenem Peer-Trend berechnet.
4. Nur positive Korrelationen werden verwendet.
5. Das Network-Signal des Zielassets ist der gleichgewichtete Mittelwert der positiven Peer-Signale,
   wobei jedes positive Pair mit seiner vorher geschätzten positiven Korrelation gewichtet wird.
6. Die Netzwerkkomponente wird nur dann richtungswirksam, wenn mindestens ein positiver Peer-Link existiert.
7. Die finale Richtung ist ein fixer 50/50-Blend aus:
   - eigenem 252/21-Trend-Signal
   - normalisiertem Network-Momentum-Signal.
8. Inverse Volatilitätsgewichtung, monatliche Rebalancierung, 10%-Volatilitätsbudget und alle übrigen
   Portfolioelemente bleiben unverändert.

Es gibt keine Suche über Lookbacks, Lags, Gewichtungen, Schwellen oder Peer-Anzahl.

## Point-in-Time-Regel

Jede Network-Schätzung darf ausschließlich Informationen verwenden, die vor dem jeweiligen
Rebalancing-Zeitpunkt vollständig abgeschlossen sind.

Der aktuelle Return wird niemals zur Schätzung seines eigenen Lead-Lag-Gewichts verwendet.

## Vergleich

Primärer Vergleich:
- unveränderter eigenpreis-basierter SMA-50/200-Trendpfad
- gegen den Network-Momentum-Challenger

Der Challenger muss gegenüber dem bestehenden Fixed Candidate nach den regulären Projekt-Gates
und dem Nicht-Verschlechterungs-Vertrag bewertet werden.

## Research-/Robustheitsvertrag

Neben den bestehenden harten Candidate-Gates werden mindestens dieselben Anforderungen verlangt:

- positive Research-Rendite
- Research-Max-Drawdown <= 10%
- Research-PF >= 1,10
- Rolling-PF >= 1,10
- mindestens 50% profitable Research-Rolling-Fenster
- durchschnittlicher Rolling-DD <= 10%
- OOS/Research-Ratio >= 0,25
- positive Holdout-Rendite
- Holdout-PF >= 1,10
- Holdout-DD <= 10%
- Holdout nichtnegativ unter 1,5x und 2x Kosten
- keine Verschlechterung der vorgeschriebenen Vergleichsmetriken gegenüber dem Fixed Candidate

## Sicherheitsstatus

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Keine Orders und keine Produktionsintegration.

## Status

Coverage-Preflight ist die erste Stufe. Keine Performanceauswertung findet statt,
bevor die Datenbasis vollständig bestätigt wurde.
