# Präregistrierung: Trial T-2026-09-24-039 — Cross-Asset Network Momentum

## Forschungsfrage

Kann ein fest definierter, ausschließlich aus vergangenen Cross-Asset-Lead-Lag-Beziehungen abgeleiteter
Network-Momentum-Zustand den bestehenden eigenpreis-basierten Trend-Signalpfad auf einem neuen,
vollständig symbol-disjunkten Multi-Asset-Datensatz verbessern?

Die Intervention ist eine neue Informationsquelle. Es findet keine Optimierung der bestehenden Trendparameter statt.

## Feste Validierungsbasis

`EIRL`, `ENZL`, `NORW`, `EDEN`, `FXF`, `FXC`, `CEW`, `EIDO`, `SCHO`, `MINT`, `FTGC`, `RWX`

- 3.520 angeforderte Daily-Candles je Symbol im Coverage-Preflight
- mindestens 3.500 gemeinsame Candles erforderlich
- 3.500 Research-Candles
- 700 blinder Holdout
- vollständig symbol-disjunkt zur bisherigen Research-Basis
- ausschließlich `COMT -> FTGC` gegenüber T038 geändert

## Präregistrierte Network-Regel

Die bestehende SMA-50/200-Long/Flat-Trendlogik bildet die Referenz.

Der Challenger verändert ausschließlich die Richtungsinformation:

1. Eigener 252-Session-Cumulative-Return mit 21-Session-Skip.
2. Für jeden Peer wird derselbe Trendreturn um exakt 21 Sessions nach hinten verschoben.
3. Je Ziel/Peer werden aus den vorherigen 252 abgeschlossenen Sessions die lineare Lead-Lag-Korrelationen bestimmt.
4. Nur positive Korrelationen werden als positive Netzwerk-Links verwendet.
5. Der Network-Score ist der mit den positiven Korrelationen gewichtete Mittelwert der Peer-Trend-Signale.
6. Ohne positiven Link ist der Network-Score 0.
7. Die finale Richtung ist ein fixer 50/50-Blend aus eigenem Trend und normalisiertem Network-Score.
8. Inverse Volatilitätsgewichtung, monatliche Rebalancierung, 10%-Volatilitätsbudget sowie Kosten-/Ausführungssemantik bleiben unverändert.

Es gibt keine Suche über Lookbacks, Lags, Korrelationsschwellen, Peer-Anzahl oder Mischungsverhältnis.

## Point-in-Time

Alle Network-Schätzungen verwenden ausschließlich Informationen, die vor dem jeweiligen Rebalancing-Zeitpunkt
vollständig abgeschlossen sind. Der aktuelle Return wird nicht zur Schätzung seines eigenen Netzwerkgewichts verwendet.

## Coverage-Governance

Der Coverage-Preflight wird automatisiert vor jeder Performanceauswertung durchgeführt.

Bei unzureichender Historie oder unvollständigem gemeinsamen Kalender lautet das Ergebnis `DATA_INVALID`.
Es wird dann keine Performance-, OOS- oder Holdout-Auswertung durchgeführt und keine positive oder negative
wissenschaftliche Performanceaussage abgeleitet.

## Evidence-Gates

Zusätzlich zu den regulären Projekt-Gates gelten:

- Research-Rendite positiv
- Research-Max-Drawdown <= 10%
- Research-PF >= 1,10
- Rolling-PF >= 1,10
- mindestens 50% profitable Rolling-Fenster
- durchschnittlicher Rolling-DD <= 10%
- OOS/Research-Ratio >= 0,25
- Holdout-Rendite positiv
- Holdout-PF >= 1,10
- Holdout-DD <= 10%
- Holdout nichtnegativ unter 1,5x und 2x Kostenstress
- keine Verschlechterung der vorgeschriebenen Vergleichsmetriken gegenüber dem Fixed Candidate

## Sicherheit

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`  
Keine Orders und keine automatische Promotion.
