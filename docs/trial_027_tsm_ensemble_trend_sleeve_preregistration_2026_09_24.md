# Präregistrierung: Trial T-2026-09-24-027 — Fixed TSM Ensemble Trend Sleeve

## Forschungsfrage

Kann die bestehende feste 50/50-Architektur verbessert werden, wenn ausschließlich das SMA-50/200-Trend-Signal durch ein festes, long-only Time-Series-Momentum-Ensemble mit 63/126/252 Sessions ersetzt wird?

## Motivation

Der bestehende Literatur-Strategie-Laborkontrolllauf des Projekts dokumentiert das TSM-Ensemble 63/126/252 als feste Referenzfamilie. Trial 027 verwendet einen neuen, vollständig symbol-disjunkten Datensatz. Fremde Forschungsresultate werden nicht als Eigenevidenz übernommen.

Die allgemeine Forschung zu Time-Series Momentum und Trend Following dient nur als Hypothesenmotivation; die bestehende Projekt-Governance mit blinden Holdouts, Kostenstress und Point-in-Time-Ausführung bleibt unverändert.

## Einzige Intervention

Unverändert:
- 50 % Trend-Sleeve;
- 50 % 12-1 Cross-Sectional-Momentum Top-2;
- monatliche Reallokation;
- inverse Volatilitätsgewichtung mit 25 %-Asset-Cap;
- bestehendes 63-Session-/10%-Volatilitätsbudget;
- Point-in-Time Close(t) -> nächstes Open -> folgende Open-Periode;
- bestehender Kostenvertrag und Kostenstress;
- Research-Gates.

Einzige Änderung:
- Trend-Signal je Asset = Mehrheit der Eigenrenditen über 63, 126 und 252 abgeschlossene Sessions;
- mindestens zwei positive Horizonte -> long;
- sonst flat;
- niemals short, kein Hebel;
- keine Parameter-, Threshold- oder Varianten-Suche.

## Neue Validierungsbasis

Trend: IVV, ITOT, SCHX, SCHF, SPAB, IEI, MBB, VCSH
Cross-Sectional: IYJ, IYC, IYM, IYK, IYW

Alle 13 Symbole sind vollständig symbol-disjunkt zu den im Projekt registrierten Research-Universen.

Daten:
- 3.500 Daily-Candles je Asset;
- 3.498 gemeinsame Point-in-Time-Return-Perioden;
- 2.798 Research;
- 700 blinder Holdout;
- keine künstliche Auffüllung.

## Entscheidungsvertrag

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
- 1,5x- und 2x-Stress-Holdout nicht negativ;
- positive Total-Return-Sensitivität.

Zusätzlich darf der TSM-Challenger gegenüber dem unveränderten 50/50-Kandidaten auf demselben Datensatz in Return, PF und OOS/IS nicht schlechter sowie in Drawdown- und Rolling-Risiko nicht schlechter sein.

Ein Bestehen ist ausschließlich VALIDATED_PASS im Research. Es ist keine Produktions-, Echtgeld- oder Live-Freigabe.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Keine Live-Orders und keine automatische Promotion.
