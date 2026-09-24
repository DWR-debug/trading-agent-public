# Präregistrierung: Trial T-2026-09-24-026 — Common-Market-Momentum-Gate

## Forschungsfrage

Kann ein gemeinsames, vorab fest definiertes Markt-Momentum-Signal die bereits
fixierte 50/50-Strategie mit 10%-Volatilitätsbudget so steuern, dass Risiko und
Robustheit verbessert werden, ohne die Holdout-Rendite gegenüber der fixierten
Referenz zu verschlechtern?

## Externe Motivation

Die Motivation ist orthogonal zu den bisher verworfenen Volatilitäts- und
kurzfristigen Reversal-Varianten. Eine im August 2026 veröffentlichte Untersuchung
von Valeriy Zakamulin argumentiert, dass ein gemeinsames Markt-Momentum-Signal
bei Aktienportfolios wirksamer sein kann als portfolio-spezifische Momentum-Signale.
Die Arbeit dient ausschließlich als Hypothesenmotivation und wird nicht als Evidenz
des Trials übernommen.

Quelle:
Zakamulin, V. (2026), Rethinking Time-Series Momentum in Equity Portfolios:
Common Signals, Long-Only Positioning, and No Need for Volatility Timing,
SSRN 7318318.

Ein weiterer aktueller Befund zur Krypto-Forschung berichtet, dass einfache
Cross-Sectional-Momentum- und Funding-Signale in großen Krypto-Perpetuals in einer
netto-kostenbereinigten Replikation 2020-2026 keine robuste Performance zeigen.
Krypto-Long/Short und Hebel werden deshalb nicht als Abkürzung in diesen Trial
aufgenommen.

## Einzige Intervention

Die bestehende feste Strategie bleibt vollständig unverändert:

- 50% Cross-Asset SMA 50/200, inverse-volatility, Long/Flat;
- 50% 12-1 Cross-Sectional Momentum, Top-2 Long-only;
- bestehendes 63-Session / 10%-Volatilitätsbudget;
- gleiche Point-in-Time-Ausführung;
- gleiche Kosten.

Neu ist ausschließlich ein gemeinsames Markt-State-Gate:

- Signal-Proxy: ACWI;
- Signal: Adjusted-Close-Return der letzten 252 abgeschlossenen Sessions;
- Momentum > 0: volle berechnete Kandidaten-Exposition;
- Momentum <= 0: gesamte Exposition auf 0;
- kein Shorting;
- kein Hebel;
- keine weitere Parameter- oder Varianten-Suche;
- vor der ersten berechenbaren 252-Session-Historie bleibt das Gate offen;
- das Gate wird nach dem bestehenden Volatilitätsbudget angewendet;
- Ein- und Ausschaltvorgänge werden als Turnover kostenwirksam erfasst.

## Neue Validierungsbasis

Handelnde Assets:

VBR, VSS, VCIT, BIL, GSG, VPL, EWQ, EWL, EWW, EZU, ILF, SCHD, USMV

Signal-Proxy:

ACWI

Alle 14 Symbole sind gegenüber den bereits registrierten Projektuniversen
symbol-disjunkt. ACWI wird ausschließlich als Signalquelle verwendet und nicht
gehandelt.

Datenvertrag:

- 3.500 Daily-Candles je Symbol;
- 3.498 gemeinsame Point-in-Time-Return-Perioden;
- 2.798 Research;
- 700 blinder Holdout;
- identische Timestamp-/Kalender-Ausrichtung;
- keine fehlenden Candles oder künstliche Auffüllung.

## Präregistrierter Entscheidungsvertrag

Der Challenger muss zunächst alle unveränderten absoluten Research-Gates
erfüllen:

1. Research-Return positiv;
2. Research-Drawdown <= 10%;
3. Research-Profit-Factor >= 1,10;
4. Rolling-Profit-Factor >= 1,10;
5. mindestens 50% profitable Research-Rolling-Fenster;
6. durchschnittlicher Rolling-Drawdown <= 10%;
7. OOS/IS-Return-Verhältnis >= 0,25;
8. positiver Holdout;
9. Holdout-PF >= 1,10;
10. Holdout-Drawdown <= 10%;
11. Holdout bleibt unter 1,5x und 2x Kostenstress nichtnegativ.

Danach müssen fünf Nicht-Verschlechterungsbedingungen gegenüber der fixierten
50/50-Referenz gelten:

- Research-Drawdown nicht schlechter;
- Research-Rolling-PF nicht schlechter;
- Holdout-Rendite nicht schlechter;
- Holdout-Drawdown nicht schlechter;
- Holdout-PF nicht schlechter.

Ein Bestehen wird ausschließlich als VALIDATED_PASS des kontrollierten
Research-Kandidaten verstanden; es ist keine Produktions-, Echtgeld- oder
Live-Freigabe.

## Sicherheitsvertrag

PAPER_ONLY=True

LIVE_TRADING_ENABLED=False

orders_enabled=False

Keine Live-Orders, kein automatisches Promotion-Gateway.
