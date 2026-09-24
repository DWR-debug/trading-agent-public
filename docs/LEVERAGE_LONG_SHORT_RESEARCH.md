# Leverage- und Long/Short-Research

## Ziel

Leverage und Short-Exposure werden als Werkzeuge untersucht, um die Ertrags-
und Einkommensfähigkeit des Agenten zu erhöhen, ohne das vorab definierte
Risikobudget zu überschreiten.

## Zwei unterschiedliche Hebelmodelle

### Margin-/Kontoleverage

Die Strategie hält ein signiertes Basis-Exposure und multipliziert es mit einem
begrenzten Leverage-Faktor. Finanzierungskosten auf Fremdkapital und
Borrow-Kosten für Short-Positionen werden separat erfasst.

### Täglich resetendes gehebeltes Produkt

Der Hebelfaktor wird pro Periode direkt auf die Basisrendite angewendet.
Die tägliche Komposition erzeugt damit die tatsächliche Pfadabhängigkeit eines
daily-reset Produktes. Das Modell darf nicht mit einer einfachen
Mehrfachmultiplikation der langfristigen Underlying-Rendite verwechselt werden.

Die SEC weist ausdrücklich darauf hin, dass länger als einen Handelstag gehaltene
leveraged/inverse Produkte wegen täglichem Reset und Compounding deutlich von
einer einfachen Multiplikation der Underlying-Performance abweichen können; der
Effekt nimmt bei höherer Volatilität und längeren Haltedauern zu.

## Long/Short

Die Forschung erhält eine symmetrische SMA-50/200-Variante und kann TSM-Ansätze
ebenfalls long und short verwenden.

Short-Kosten werden nicht ignoriert. In einer späteren Validierung müssen
Finanzierung, Borrow, Slippage und eventuelle Produktkosten getrennt
stressgetestet werden.

## Sicherheitsregeln

- keine Live-Orders
- keine automatische Hebelwahl
- Leverage ist eine Forschungsvariable, kein Produktionsdefault
- maximale Exposition bleibt explizit begrenzt
- vollständiger Kapitalverlust beendet die simulierte Position
- unzureichende Evidenz führt zu keiner Exposition

## Forschungsreihenfolge

1. Long/Short-Signalfamilien unabhängig validieren.
2. Danach feste Leverage-Stufen als separat präregistrierte Kontrollen testen.
3. Daily-reset Produkte getrennt von Margin-Leverage untersuchen.
4. Erst danach adaptive Leverage-/Regime-Steuerung prüfen.
5. Jede Variante erneut gegen unabhängige Holdouts, Rolling-Stabilität, Kosten-
   stress und Overfitting-Kriterien prüfen.