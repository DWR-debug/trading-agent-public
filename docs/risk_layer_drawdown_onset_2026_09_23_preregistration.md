# Risk-Layer-Drawdown-Onset — Pre-Registration 2026-09-23

## Forschungsfrage

Reagiert die unveränderte 63-Session-/10%-Realized-Volatility-Risikosteuerung
bereits vor oder am Beginn ihres eigenen maximalen Research-Drawdowns, oder
setzt die De-Risking-Reaktion typischerweise erst nach Drawdown-Beginn ein?

## Datenbasis

Nur die vier bereits abgeschlossenen und vollständig symbol-disjunkten
Validierungsartefakte werden verwendet:

- Run 35865847394 / Artifact 10751817990
- Run 35839443616 / Artifact 10740188093
- Run 35851876264 / Artifact 10745697729
- Run 35867637587 / Artifact 10753545703

## Auswertungsgrenze

Nur die jeweils 2.798 Research-Returns werden ausgewertet.
Der 700-Return-Holdout wird weder berichtet noch für die Entscheidung genutzt.

## Feste Definitionen

- Das maximale Research-Drawdown-Ereignis ist der größte Peak-to-Trough-Drawdown
  innerhalb der jeweiligen 2.798 Research-Returns.
- Episodenbeginn ist die erste Session nach dem lokalen Peak vor dem maximalen
  Trough.
- Onset-active: Scale < 1,0 am ersten Tag der Drawdown-Episode.
- Delayed: erste De-Risking-Session mindestens zwei Drawdown-Tage nach
  Episodenbeginn, oder während der Episode überhaupt kein De-Risking.
- Konsensschwelle: 3 von 4 unabhängigen Validierungen.

## Konsequenzregel

- Delayed in >=3/4: Es wird als separate Forschungsfrage geprüft, ob ein
  vorab definierter Drawdown-/State-Control das Timing-Problem adressieren kann.
- Onset-active in >=3/4: Die bestehende Risk-Layer-Timing-Hypothese wird nicht
  als universeller Mechanismus weiterverfolgt.
- Sonst: mixed risk-layer onset; keine Intervention aus diesem Befund.

Diese Regel ist deskriptiv und kausal nicht beweisend.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Parameteroptimierung
- keine Produktionsänderung
- keine Orders