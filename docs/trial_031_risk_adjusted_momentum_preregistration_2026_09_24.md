# Präregistrierung: Trial T-2026-09-24-031 — Risk-Adjusted Cross-Sectional Momentum

## Forschungsfrage

Kann die bestehende feste 50/50-Architektur verbessert werden, wenn ausschließlich
das bisherige 12-1-Rohreturn-Ranking der Cross-Sectional-Sleeve durch eine feste
risikoadjustierte Rangfolge ersetzt wird, bei der die 12-1-Rendite durch die
Realized Volatility derselben Formationperiode geteilt wird?

## Evidenzbasierte Motivation

Fan, Kearney, Li und Liu zeigen in der peer-reviewten Arbeit
“Momentum and the Cross-section of Stock Volatility”, dass hohe Realized Volatility
während der Momentum-Formation mit schwächerem Momentum-Effekt verbunden ist und
entwickeln GRJMOM als risikoadjustierte Momentum-Variante. Eine einfache feste
Spezialisierung ist die Rangfolge nach Formationsrendite geteilt durch
Formationsvolatilität (Sharpe-ähnliche Rangfolge). citeturn224424search1turn224424search31

Die Literatur wird ausschließlich als Hypothesenmotivation genutzt. Trial 031
prüft die Regel unabhängig auf einem neuen, vollständig disjunkten Datensatz.

## Einzige Intervention

Unverändert:
- 50 % SMA 50/200 inverse-volatility Trend-Sleeve;
- 50 % Cross-Sectional-Sleeve;
- monatliche Reallokation;
- Top-2 long-only, je 50 % innerhalb der CS-Sleeve;
- bestehendes aggregiertes 63-Session-/10%-Volatilitätsbudget;
- Point-in-Time-Ausführung;
- gleicher Kostenvertrag und Kostenstress.

Einzige Änderung:
- CS-Score = 252-Session kumulierte Rendite / tägliche Realized Volatility über
  genau dieselbe 252-Session Formationperiode, die 21 Sessions vor der Rebalance endet;
- monatlich neu berechnet;
- Top-2 nach diesem festen Score;
- keine Short-Positionen;
- kein Hebel;
- keine Parameter-, Threshold- oder Varianten-Suche.

Die neue Volatilitätskennzahl wird ausschließlich aus bis zum Rebalance-Zeitpunkt
bekannten Daten berechnet.

## Neue Validierungsbasis

Trend:
EIS, EPU, ECH, EWS, EWM, EZA, TUR, THD

Cross-Sectional:
VDC, VCR, VOX, IAT, XTN

Alle 13 Symbole sind vollständig symbol-disjunkt zu den im Projekt registrierten
Research-Universen.

Coverage-Preflight:
- Workflow 36042442309
- Artifact 10827700335
- 13/13 Symbole mit 3.520 Candles
- gemeinsamer Kalender 3.520
- Coverage-Fingerprint:
  cc21adf1e1c12a28932e9eec1e246fa498781e0b583f92a52f85b5af24ca566b
- Performanceauswahl im Preflight: false

Researchdaten:
- 3.500 Candles je Asset;
- 3.498 gemeinsame PIT-Returnperioden;
- 2.798 Research;
- 700 blinder Holdout.

## Präregistrierter Entscheidungsvertrag

Der Challenger muss alle absoluten Research-/Holdout-Gates erfüllen:
- Research-Return > 0;
- Research-Drawdown <= 10 %;
- Research-PF >= 1,10;
- Rolling-PF >= 1,10;
- profitable Rolling-Fensterquote >= 50 %;
- durchschnittlicher Rolling-Drawdown <= 10 %;
- OOS/IS >= 0,25;
- positiver Holdout;
- Holdout-PF >= 1,10;
- Holdout-Drawdown <= 10 %;
- 1,5x-Kostenstress-Holdout nicht negativ;
- 2x-Kostenstress-Holdout nicht negativ;
- positive Total-Return-Sensitivität.

Zusätzlich darf der Challenger gegenüber dem unveränderten 50/50-Kandidaten
auf demselben Datensatz nicht schlechter sein in Research-Return, Research-DD,
Research-PF, Rolling-PF, profitable Rolling-Fensterquote, Rolling-DD,
OOS/IS, Holdout-Return, Holdout-PF oder Holdout-DD.

Ein Bestehen ist ausschließlich VALIDATED_PASS als Research-Befund. Keine
Produktions-, Echtgeld- oder Live-Freigabe.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
Keine Live-Orders und keine automatische Promotion.
