# Risk-Layer-Window 31 vs 63 — Pre-Registration 2026-09-23

## Forschungsfrage

Prüft die eng begrenzte Hypothese, ob ein schnelleres 31-Session-Volatilitätsfenster
die replizierte Rapid-Drawdown-Onset-Latenz gegenüber dem bestehenden 63-Session-
Fenster reduziert.

## Feste Intervention

- Variante A: 31 Sessions
- Control B: 63 Sessions
- identisches annualisiertes Volatilitätsziel: 10%
- identisches De-Risk-only-Verhalten
- identische Signale, Sleeve-Gewichte, PIT-Semantik, Kosten und Daten
- keine weiteren Fenster

## Datenbasis und Auswertungsgrenze

Die vier bereits abgeschlossenen, vollständig symbol-disjunkten Validierungen
werden ausschließlich im Research-Teil verwendet: 2.798 Returns je Satz und
fünf feste Rolling-Fenster je Satz.

Der 700-Return-Holdout wird weder berichtet noch zur Auswahl oder Entscheidung
verwendet.

## Vorab definierte Timing-Kriterien

1. Rapid-Delayed-Rate: Anteil der Rapid-Episoden, bei denen De-Risking verspätet
   oder gar nicht vor dem Trough erfolgt.
2. Rapid-Onset-Active-Rate: Anteil der Rapid-Episoden, die am ersten
   Drawdown-Tag bereits de-risked sind.

Timing gilt als verbessert, wenn die 31-Session-Variante in mindestens 3 von 4
Validierungssets beide Kriterien verbessert: geringere Delayed-Rate und höhere
Onset-Active-Rate.

## Vorab definierte Research-Risiko-Kriterien

Die 31-Session-Variante darf in mindestens 3 von 4 Validierungssets beim
Research-Drawdown nicht schlechter sein als 63 Sessions und beim Research-
Rolling-Profit-Factor nicht schlechter sein.

## Entscheidungsregel

- Timing verbessert in >=3/4 auf beiden Kriterien + Risiko nicht schlechter in
  >=3/4 auf beiden Kriterien: die 31-Session-Variante darf in einem fünften,
  neuen symbol-disjunkten Validierungssatz unabhängig validiert werden.
- Timing verbessert, aber Risiko-Kriterien verfehlt: Forschungs-Trade-off;
  keine weitere Validierung und keine Produktionseinführung.
- Timing nicht in >=3/4 verbessert: Hypothese verworfen.

Diese Entscheidung verwendet ausschließlich Research-Daten.

## Sicherheit

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Orders
- keine Produktionsänderung