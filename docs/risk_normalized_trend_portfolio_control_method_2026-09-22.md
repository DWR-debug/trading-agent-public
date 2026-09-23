# Risikonormalisierter Trend-Portfolio-Control — Methodik

## Zweck

Dieser Control prüft eine einzelne, vorregistrierte Portfolioallokationsregel.
Er verändert weder die getesteten Signalfamilien noch den Produktionspfad.

## Vorregistrierte Regel

Für jedes Asset gilt:
- Richtung aus TSM-Ensemble 63/126/252 oder SMA 50/200.
- Nur Assets mit aktivem Signal erhalten Gewicht.
- Gewicht proportional zu 1 / ATR-Prozent.
- Vorzeichen entspricht der Signalrichtung.
- Gewichte werden so normiert, dass die Summe ihrer Absolutwerte 100 % beträgt.

Der Regel wird nicht auf dem Holdout angepasst.

## Kontrollfragen

1. Verbessert risikobasiertes Gewicht gegenüber gleichem Kapitalgewicht
   die Portfolio-Stabilität?
2. Bleiben positive Rolling-Fenster erhalten?
3. Wie verändern sich PF und maximaler Drawdown?
4. Gibt es einen Unterschied zwischen TSM, SMA und deren festem Blend?

## Interpretation

Ein positives Ergebnis wäre nur ein Nachweis, dass die Portfolioallokation als
mechanische Risikokonstruktion interessant ist. Es wäre kein Beweis für Alpha
und keine Produktionsfreigabe.

Ein negatives Ergebnis würde die Literatur-/Risikoadaptions-Hypothese für diese
konkrete Portfolioebene schwächen, nicht aber die Trendfamilien insgesamt.

## Sicherheitszustand

Paper-Only bleibt aktiv. Live-Trading bleibt deaktiviert. Es gibt keine Orders.
