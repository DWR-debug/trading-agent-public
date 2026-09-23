# Trend Family Walk-Forward Control — 2026-09-22

## Zweck

Dieser Control prüft nicht einzelne Parameter, sondern ausschließlich die
Übertragung zwischen bereits untersuchten Strategiefamilien.

Vorab festgelegte aktive Familien:
- monatliches Time-Series Momentum, gleichgewichtet
- SMA 50/200 Long/Flat mit inverser Volatilitätsgewichtung
- fixer 50/50-Blend aus TSM und SMA

Passive Referenz:
- gleichgewichtetes Buy-and-Hold

## Walk-Forward-Protokoll

Quelle ist das unveränderte Cross-Asset-Archiv aus Run 35780008533:

SPY, EFA, TLT, GLD, DBC, UUP, QQQ, IWM.

- 3.500 Candles je Asset
- 2.800 Research
- 700 blinder Holdout
- 1.400 Training
- 280 OOS-Test
- Schrittweite 280
- 5 Rolling-Fenster

In jedem Research-Fenster wird genau eine Familienentscheidung getroffen:

1. höchste Trainings-Profit-Factor
2. bei Gleichstand höchste Trainingsrendite
3. bei erneutem Gleichstand niedrigster Trainings-Drawdown
4. abschließend lexikographischer Strategiename als deterministischer Tiebreak

Es gibt keine Parameteroptimierung und keine Selection-Profile.

Der jeweils ausgewählte Familie wird für das gesamte anschließende OOS-Fenster
eingefroren.

Nach dem fünften Research-Fenster wird die dort ausgewählte Familie für den
gesamten 700-Tage-Holdout eingefroren. Der Holdout beeinflusst die Auswahl nicht.

## Kostenstress

Die Familienwahl erfolgt ausschließlich auf Basis des Basiskostenfalls.

Danach wird dieselbe Auswahl zusätzlich mit verdoppelten Gebühren und Slippage
bewertet.

Damit kann Kostenrobustheit geprüft werden, ohne eine zweite, rückwirkende
Auswahlregel einzuführen.

## Interpretation

Ein positiver Familien-WFO-Befund bedeutet nicht, dass die ausgewählte Familie
produktionsreif ist.

Er würde lediglich zeigen, dass eine kleine Familienauswahl auf Trainingsdaten
zeitweise OOS übertragbar ist.

Ein negativer Befund wäre ebenfalls wertvoll: Dann wäre die aktuelle
Strategiefamilien-Auswahl noch nicht stabil genug für eine Integration in die
Produktion.

## Sicherheitsstatus

- Paper-Only
- Live-Trading deaktiviert
- keine Orders
- keine Gateänderung
- keine Änderung des Produktions-Parameterraums
