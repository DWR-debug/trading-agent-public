# Präregistrierung: Trial T-2026-09-24-028 — Per-Sleeve Volatility Budget

## Forschungsfrage

Kann der bestehende feste 50/50-Kandidat robuster werden, wenn das bereits
verwendete 63-Sessionen-/10%-Volatilitätsbudget nicht erst auf das aggregierte
Portfolio, sondern separat auf die Trend- und Cross-Sectional-Sleeve angewendet
wird?

## Diagnosebasis

Die Failure-Diagnose des vollständig disjunkten Trial-027-Datensatzes zeigt:

- die Cross-Sectional-Sleeve hatte dort deutlich höhere Einzel-Sleeve-Max-Drawdowns
  als die Trend-Sleeve;
- im letzten Research-Rolling-Fenster waren beide Sleeves schwach;
- im Holdout-Maximum-Drawdown verloren beide Sleeves gleichzeitig, wobei die
  Cross-Sectional-Sleeve den größeren Einzelverlust beitrug;
- die bestehende Portfolio-Volatilitätssteuerung reduziert das aggregierte Risiko,
  begrenzt aber diese Sleeve-Asymmetrie nicht separat.

Diese Diagnose ist rein deskriptiv und wurde nicht zur Auswahl von Parametern
verwendet.

## Externe Motivation

Eine im Juli 2026 veröffentlichte Untersuchung zu mechanischen Trend-Systemen
berichtet, dass volatilitätsbasierte Positionsgrößen in ihrem Sample konsistent
eine bessere risikoadjustierte Ausprägung als alternative getestete Risiko-Overlays
lieferten. Die Untersuchung dient nur als externe Hypothesenmotivation; ihre
Ergebnisse werden nicht als Eigenevidenz des Trials übernommen.

Quelle:
Purvang Gandhi (2026), Regime Sequencing in Trend Following Systems: Evidence
from Four Developed Equity Markets, SSRN 7069978.

## Einzige Intervention

Unverändert:

- 50 % SMA-50/200 inverse-volatility Trend-Sleeve;
- 50 % 12-1 Cross-Sectional-Momentum Top-2;
- gleiche Signale und Rebalancing-Regeln;
- gleiche Point-in-Time-Ausführung;
- gleiche Gebühren/Slippage;
- gleiche 63-Sessionen-/10%-Risk-Basis;
- gleiche Research-Gates.

Einzige Änderung:

1. Trend-Sleeve erhält separat die vorhandene 63-Sessionen-/10%-Volatilitätsbegrenzung.
2. Cross-Sectional-Sleeve erhält separat die vorhandene 63-Sessionen-/10%-Volatilitätsbegrenzung.
3. Erst danach werden die beiden Sleeves unverändert mit 50/50 aggregiert.
4. Jede Sleeve-Skalierung verändert die effektive Exposition nur nach unten; niemals
   oberhalb 100 %.
5. Kein Shorting, kein Leverage, keine Parameter- oder Varianten-Suche.

Damit wird ausschließlich die Reihenfolge der bestehenden Risikosteuerung verändert.

## Neue Validierungsbasis

Trend-Sleeve:
SPLV, SPHQ, SPYG, SPYV, FXI, GDX, PFF, CWB

Cross-Sectional-Sleeve:
XSD, IBB, ITA, XAR, XES

Alle 13 Symbole sind vollständig symbol-disjunkt zu den bereits registrierten
Research-Universen.

Datenvertrag:

- 3.500 Daily-Candles je Asset;
- 3.498 gemeinsame Point-in-Time-Return-Perioden;
- 2.798 Research;
- 700 blinder Holdout;
- keine künstliche Auffüllung;
- keine Auswahl nach beobachteter Performance.

## Präregistrierter Entscheidungsvertrag

Der Challenger muss alle unveränderten absoluten Kriterien erfüllen:

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
