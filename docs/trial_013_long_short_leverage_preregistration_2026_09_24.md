# Präregistrierung: Trial 013 – Long/Short und Leverage

## Forschungsfrage

Kann eine symmetrische Long/Short-Variante der fixierten SMA-50/200-Trendfamilie
auf einem vollständig neuen US-ETF-Universum robuste Erträge erzeugen, und welche
der vorab festgelegten Hebelstufen verändert Ertrag und Risiko unter realistischen
Finanzierungs-/Borrow-Stressannahmen?

## Varianten

- Referenz: SMA 50/200 Long/Flat, 1x.
- Long/Short: SMA 50/200, 1x.
- Long/Short: 1,5x.
- Long/Short: 2x.
- Long/Short: 3x (bestehende technische Obergrenze).

Alle Varianten nutzen 10 % annualisiertes Volatilitätsziel, 63 Sessions
Volatilitätsfenster, 21-Session-Rebalancing und Point-in-Time-Ausführung:
Close(t) -> Open(t+1) -> Open(t+2).

Keine Optimierung. Keine Auswahl anhand des Holdouts.

## Datensatz

ITOT, IEMG, SCHD, ACWI, EMB, GLTR, PFF, FEZ

Exakt 3.500 gemeinsame Tages-Candles je Asset und exakt 3.498 Return-Perioden.
Research/Holdout: 2.798 / 700.

Die Symbole müssen vollständig disjunkt gegenüber allen bisher registrierten
Research-Universen sein.

## Kosten

Basis: 0,10 % Gebühr + 0,05 % Slippage.

Realistic stress: 1,5x Trading-Reibung + 5 % p.a. Finanzierung + 5 % p.a. Short-Borrow.

Adverse stress: 2x Trading-Reibung + 10 % p.a. Finanzierung + 10 % p.a. Short-Borrow.

Die 5 %/10 % sind bewusst definierte Stressannahmen und keine aktuellen
Marktquotierungen.

## Auswertung

Je Variante werden Research, fünf Rolling-Fenster und Holdout ausgewertet:
Rendite, Maximum Drawdown, Profit Factor, Mindest-Equity, Ruin-Indikator und
Stresssensitivität.

Die Varianten werden vollständig berichtet. Eine automatische Produktionsauswahl
ist ausgeschlossen.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Trial-ID: T-2026-09-24-013