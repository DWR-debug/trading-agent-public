# Präregistrierung: achte Validierung – Long/Short und Leverage

## Forschungsfrage

Erhöht eine symmetrische Long/Short-Version einer bereits untersuchten Trendfamilie
die Ertragsfähigkeit auf einem neuen, vollständig symbol-disjunkten Datensatz,
und verändert moderates Konto-Leverage diese Ertrags-/Risikostruktur?

Die Untersuchung ist ein Vergleichstest und keine nachträgliche Kandidatenauswahl.

## Vorab definierte Varianten

1. SMA 50/200 Long/Flat, 1x Margin-Leverage als Referenz.
2. SMA 50/200 Long/Short, 1x Margin-Leverage.
3. SMA 50/200 Long/Short, 1.5x Margin-Leverage.
4. SMA 50/200 Long/Short, 2x Margin-Leverage.
5. SMA 50/200 Long/Short, 3x Margin-Leverage als bestehende technische Obergrenze.

Alle Varianten verwenden:
- 10 % annualisiertes Volatilitätsziel,
- 63 Sessions Volatilitätsfenster,
- 21-Session-Rebalancing,
- Point-in-Time: Close(t) Entscheidung -> Open(t+1) -> Open(t+2),
- 0,10 % Gebühr + 0,05 % Slippage.

## Neuer Validierungsdatensatz

ITOT, IEMG, SCHD, ACWI, EMB, GLTR, FXY, EWQ

Die Symbole müssen gegenüber allen bisherigen registrierten Universen vollständig
disjunkt sein.

Datenmenge:
- 3.500 gemeinsame Tages-Candles je Asset,
- 2.798 Research-Returns,
- 700 Holdout-Returns,
- insgesamt 3.498 gemeinsame Return-Perioden.

## Kosten- und Leverage-Stress

Basis:
- Trading-Reibung wie oben,
- keine zusätzlichen Finanzierungs-/Borrow-Kosten, um den reinen Signal-/Leverage-Effekt zu isolieren.

Realistic stress:
- 1,5x Trading-Reibung,
- 5 % p.a. Finanzierung,
- 5 % p.a. Short-Borrow.

Adverse stress:
- 2x Trading-Reibung,
- 10 % p.a. Finanzierung,
- 10 % p.a. Short-Borrow.

Die 5 %/10 %-Werte sind bewusst definierte Stressannahmen und keine Behauptung
aktueller Marktquotierungen.

## Keine Auswahl

Alle fünf Varianten werden vollständig berichtet. Keine Variante wird aufgrund
dieses Datensatzes automatisch als Produktionskandidat ausgewählt.

## Primäre Auswertung

Pro Variante:
- Research Return,
- Research Maximum Drawdown,
- Research Profit Factor,
- fünf Research-Rolling-Fenster,
- Holdout Return,
- Holdout Maximum Drawdown,
- Holdout Profit Factor,
- Minimum Equity,
- Ruin-Indikator,
- Performance unter den beiden Stressszenarien.

Eine spätere Produktionsauswahl benötigt einen separaten, vorab definierten
Selection-/Confirmation-Prozess.

## Sicherheitsvertrag

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Trial-ID: T-2026-09-24-012
