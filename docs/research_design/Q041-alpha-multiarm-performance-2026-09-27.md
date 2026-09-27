# Q041 — Fixed Alpha Multi-Arm Performance

**Stand:** 2026-09-27  
**Status:** PREREGISTERED / FIXED-MULTI-ARM PERFORMANCE  
**Voraussetzungen:** T058 Coverage + T059 PIT

## Ziel

Q041 prüft vier klar definierte preis-/OHLCV-Mechanismen auf dem frisch validierten Q038-Universum und stellt ihnen den unveränderten T052-Control gegenüber.

Es gibt keine Familienrangfolge und keine Auswahl eines Arms aus Holdout-Daten. Alle fünf Arms werden nach identischem Evidence-Vertrag ausgewertet.

## Fest eingefrorene Arms

**CONTROL:** unveränderter T052-Kern aus 50 % SMA 50/200 inverse-volatility Trend-Sleeve und 50 % 12-1 Top-2 Cross-Sectional Momentum.

**A1:** Multi-Horizon TSM-Consensus mit 21/63/252 Sessions. Nur positive Konsensus-Signale erhalten Gewicht; positive Titel werden gleichgewichtet, maximal 1.0x Gross.

**A2:** 252-Session Cross-Sectional Momentum mit festem 21-Session Skip; Top 2 gleichgewichtet.

**A3:** 252-Return Residual Momentum, Residualisierung gegen die gleichgewichtete Universumsrendite; Top 2 gleichgewichtet.

**A5:** 252-Return Low-Beta-Definition gegenüber der gleichgewichteten Universumsrendite; zwei niedrigsten Betas gleichgewichtet.

Keine Short-Positionen, kein Leverage und keine nachträgliche Parameteranpassung.

## Evidence-Vertrag

2.798 Research-Perioden und 700 Holdout-Perioden. Unverändert bestehen 13 Gates zu Research-Return, Drawdown, Profit Factor, Rolling-Stabilität, OOS/IS, Holdout-Rendite/-PF/-DD, Cost Stress und Total-Return-Sensitivity.

Der Holdout bleibt bis zur finalen Auswertung blind für Auswahlentscheidungen.

## Sicherheitszustand

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`ORDERS_ENABLED=False`  
`AUTOMATIC_PROMOTION=False`

Ein Q041-Ergebnis ist Forschungs-Evidence. Es erzeugt keine automatische Handelsfreigabe.
