# Präregistrierung: Trial T-2026-09-24-029 — Sleeve Volatility Parity

## Forschungsfrage

Kann die bestehende feste 50/50-Aggregation der unveränderten Trend- und
Cross-Sectional-Sleeves durch eine einfache, feste inverse-Volatilitätsbasierte
Kapitalallokation zwischen den beiden Sleeves verbessert werden?

## Motivation und Diagnosebasis

Trial 028 zeigte, dass separate Sleeve-Volatilitätsbudgets den Drawdown deutlich
reduzieren können, aber einen kleinen Renditeverlust erzeugen. Der nächste
kontrollierte Schritt ist deshalb keine Änderung der Signale oder des
Volatilitätsfensters, sondern eine andere feste Kapitalallokation zwischen den
unveränderten Sleeves.

Aktuelle Risk-Parity-Forschung behandelt inverse Volatilitätsallokation als
robuste Risk-Based-Benchmark. Gleichzeitig zeigen neuere Arbeiten, dass
komplexere Tail-Risk-Varianten nicht zuverlässig überlegen sind. Daher wird
bewusst die einfachste feste Variante getestet.

Externe Motivation:
- Bergmeier (2026), "The risk parity zoo": inverse variance kann als robuste
  Referenz dienen; komplexere Risk-Parity-Varianten liefern nicht zuverlässig
  bessere Performance. citeturn768597search0
- Almeida/Farias (2026), "Volatility Scaling in Multi-Asset Portfolios":
  sektor-/portfolio-level volatility scaling verändert realisierte
  Risikostreuung deutlich, mit Regimeabhängigkeiten. citeturn768597search4

Die externen Ergebnisse werden ausschließlich als Hypothesenmotivation genutzt.

## Einzige Intervention

Unverändert:
- 50 % Trend-Sleeve als SMA 50/200 inverse-volatility Long/Flat;
- 50 % 12-1 Cross-Sectional Momentum Top-2;
- monatliche Reallokation der Signale;
- bestehender aggregierter 63-Sessionen-/10%-Volatilitätsbudget;
- Point-in-Time-Ausführung;
- bestehender Kostenvertrag.

Einzige Änderung:
- zu Beginn jedes neuen Monats werden die beiden Sleeves anhand ihrer
  vorherigen 63 vollständig abgeschlossenen täglichen Sleeve-Renditen bewertet;
- Sleeve-Gewicht = inverse Volatilität / Summe der beiden inversen Volatilitäten;
- bis 63 vollständige historische gemeinsame Sleeve-Renditen vorliegen:
  unverändert 50/50;
- Gewichte liegen immer zwischen 0 und 1 und summieren sich auf 1;
- Änderungen der Sleeve-Gewichte erzeugen zusätzlichen, kostenwirksamen
  Turnover;
- danach bleibt das bestehende aggregierte 63-Sessionen-/10%-Volatilitätsbudget
  unverändert;
- kein Shorting, kein Hebel, keine Parameter-/Threshold-/Varianten-Suche.

Die Allokationsentscheidung für eine Periode verwendet ausschließlich Daten
aus Perioden vor dieser Periode.

## Neue Validierungsbasis

Trend-Sleeve:
IWB, IEFA, BIV, BSV, VGIT, JNK, HDV, DBE

Cross-Sectional-Sleeve:
IYF, IYE, IYG, DJP, EPHE

Alle 13 Symbole sind gegenüber den bereits registrierten Projektuniversen
vollständig symbol-disjunkt.

Daten:
- 3.500 Daily-Candles je Asset;
- 3.498 gemeinsame Point-in-Time-Return-Perioden;
- 2.798 Research;
- 700 blinder Holdout;
- keine künstliche Auffüllung;
- keine Auswahl nach beobachteter Performance.

## Entscheidungsvertrag

Der Challenger muss alle unveränderten absoluten Research-Kriterien erfüllen:

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
nicht schlechter sein bei:
- Research-Return;
- Research-Drawdown;
- Research-PF;
- Rolling-PF;
- profitable Rolling-Fensterquote;
- durchschnittlichem Rolling-Drawdown;
- OOS/IS;
- Holdout-Return;
- Holdout-PF;
- Holdout-Drawdown.

Ein Bestehen ist ausschließlich VALIDATED_PASS im Research. Keine Produktions-,
Echtgeld- oder Live-Freigabe.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Keine Live-Orders und keine automatische Promotion.
