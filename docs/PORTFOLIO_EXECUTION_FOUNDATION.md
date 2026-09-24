# Portfolio-/Execution-Foundation — 2026-09-24

## Zweck

Diese Schicht schafft nur technische, fail-closed Infrastruktur. Sie ändert
keine bestehende Strategie, kein Research-Gate und keine Produktionskonfiguration.

## Portfolio

Der FixedPortfolioAllocator:

- validiert bereits festgelegte signierte Sleeve-/Symbol-Exposures,
- prüft Gross-, Net- und Per-Symbol-Limits,
- kombiniert mehrere Sleeves deterministisch,
- verändert Gewichte nicht automatisch.

Eine Constraint-Verletzung führt zu einem Fehler statt zu automatischer
Normalisierung oder Optimierung. Damit kann die spätere Portfolio-Research-Schicht
explizite Allokationshypothesen testen, ohne dass der technische Unterbau selbst
eine Auswahlentscheidung trifft.

## Execution / Kosten

Das opt-in ExecutionCostModel bildet separat ab:

- Gebühr,
- Slippage,
- halben Spread auf jeder Seite,
- explizite Round-Trip-Kosten,
- Short-Borrow-Kosten pro Tag.

Projekt-Basiswerte bleiben 10 bps Gebühr + 5 bps Slippage. Bei fehlendem Spread
betragen die Kosten damit 15 bps je Richtung bzw. 30 bps für einen vollständigen
Round Trip.

Die bestehende PaperBroker-/Backtest-Implementierung wird in diesem ersten Schritt
bewusst nicht geändert. Dadurch bleiben bisherige Research-Resultate reproduzierbar.

## Safety

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
orders_enabled=False

Diese Foundation ist kein Produktions- oder Alpha-Feature und erzeugt keine Orders.
