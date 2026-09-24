# Präregistrierung: Trial 014 – Long/Short und Leverage auf US-ETFs

## Forschungsfrage

Erhöht eine symmetrische Long/Short-Variante der fixierten SMA-50/200-Trendfamilie
auf einem vollständig neuen, US-gelisteten ETF-Universum die robuste Ertrags-
und damit potenziell die Einkommenskapazität, und wie verändert moderates
Margin-Leverage das Risiko-/Ertragsprofil?

## Varianten

- Referenz: SMA 50/200 Long/Flat, 1x Margin.
- Long/Short: SMA 50/200, 1x Margin.
- Long/Short: 1,5x Margin.
- Long/Short: 2x Margin.
- Long/Short: 3x Margin.

Alle Varianten verwenden 10 % annualisiertes Volatilitätsziel, 63 Sessions
Volatilitätsfenster, 21-Session-Rebalancing und Point-in-Time:
Close(t) Entscheidung -> Open(t+1) -> Open(t+2).

Keine Parameteroptimierung und keine Holdout-basierte Auswahl.

## Datensatz

VOO, VT, VWO, VEU, IWD, IWF, IWN, IWO

US-gelistete ETFs, vollständig symbol-disjunkt zu allen bereits registrierten
Universen.

3500 gemeinsame Tages-Candles je Asset, 3.498 Return-Perioden, Research/Holdout
2798 / 700.

## Kostenstress

Basis: 0,10 % Gebühr + 0,05 % Slippage.

Realistic stress: 1,5x Trading-Reibung + 5 % p.a. Finanzierung + 5 % p.a. Short-Borrow.

Adverse stress: 2x Trading-Reibung + 10 % p.a. Finanzierung + 10 % p.a. Short-Borrow.

Die Stresswerte sind präregistrierte Modellannahmen, keine Marktquotierungen.

## Auswertung

Für jede Variante: Research Return, Research DD, Research PF, fünf Rolling-Fenster,
Holdout Return, Holdout DD, Holdout PF, Minimum Equity, Ruin-Indikator und
Exposure-Grenzen.

Die Varianten werden vollständig berichtet. Eine Produktionsauswahl findet in
diesem Trial nicht statt.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Trial-ID: T-2026-09-24-014