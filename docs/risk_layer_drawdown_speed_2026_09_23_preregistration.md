# Risk-Layer-Drawdown-Speed — Pre-Registration 2026-09-23

## Forschungsfrage

Ist die Reaktionsverzögerung der unveränderten 63-Session-/10%-Volatility-
Risikosteuerung bei schnellen maximalen Drawdowns systematisch größer als bei
langsamen Drawdowns?

## Datenbasis

Vier bereits abgeschlossene, vollständig symbol-disjunkte Validierungsfamilien:

- Run 35865847394 / Artifact 10751817990
- Run 35839443616 / Artifact 10740188093
- Run 35851876264 / Artifact 10745697729
- Run 35867637587 / Artifact 10753545703

Jede der vier Familien wird in ihren fünf bereits definierten Research-
Rolling-Fenstern ausgewertet. Damit entstehen 20 feste Research-Fenster.

## Feste Definitionen

- Rapid: maximale Drawdown-Episode innerhalb des Research-Fensters dauert
  höchstens floor(63/2) = 31 Sessions.
- Slow: mehr als 31 Sessions.
- Delayed: erste De-Risking-Session mindestens zwei Drawdown-Tage nach
  Episodenbeginn, oder keine De-Risking-Session bis zum Trough.
- Onset-active: Scale < 1,0 am ersten Drawdown-Tag.

## Entscheidungsregel

Für jedes der vier Validierungssets werden Rapid und Slow getrennt betrachtet.

- Wenn die Delayed-or-Never-Rate bei Rapid höher ist als bei Slow in mindestens
  3/4 Sets, wird der Kontrast als repliziert klassifiziert.
- Falls diese Regel nicht greift, aber die Onset-active-Rate bei Rapid niedriger
  ist als bei Slow in mindestens 3/4 Sets, wird der Kontrast ebenfalls als
  repliziert klassifiziert.
- Andernfalls gilt der Befund als nicht repliziert.

Die Regel ist rein deskriptiv. Sie erlaubt keine Auswahl eines Parameters und
keine Produktionseinführung.

## Konsequenz

Bei repliziertem Rapid-Drawdown-Onset-Kontrast darf als nächste Forschungsfrage
ein separat präregistrierter schnellerer State-/Risk-Control untersucht werden.
Es werden dabei keine Zielparameter aus dem aktuellen Befund übernommen, bevor
die neue Untersuchung selbst präregistriert wurde.

Bei fehlendem Kontrast bleibt die bestehende Risk-Layer-Architektur unverändert.

## Auswertungsgrenze

Der Holdout wird weder berichtet noch für die Entscheidung verwendet.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Parameteroptimierung
- keine Asset-Auswahl
- keine Gate-Änderung
- keine Produktionsmutation
- keine Orders