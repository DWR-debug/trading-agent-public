# Unabhängige Replikation des 12-1 Cross-Sectional-Momentum-Controls

## Ziel

Die erste Cross-Sectional-Momentum-Studie auf SOUN/RKLB/IONQ/ASTS/HIMS
lieferte ein starkes exploratives Signal. Die primäre Variante war:

12-Monats-Formation -> letzter Monat übersprungen -> monatliche Reallokation
-> Top-2 Long-only.

Diese Studie repliziert genau diese Regel auf einem vollständig getrennten
Universum:

NVDA, AMD, TSLA, COIN, PLTR.

Es gibt keine nachträgliche Auswahl der Regel.

## Fixierte Methodik

- 1.300 Tages-Candles je Asset
- 1.040 Research-Candles
- 260 Holdout-Candles
- Formation: 252 Handelstage
- Skip: 21 Handelstage
- Rebalance: 21 Handelstage
- Top-2, gleichgewichtet
- Long-only
- Close(t) -> Open(t+1) -> Open(t+2)
- 0,10 Prozent Gebühr + 0,05 Prozent Slippage
- separater 2x-Kostenstress
- kein Parameter-Optimieren
- keine Selection-Profile
- keine Gate-Änderung
- Paper-Only

## Interpretation

Die Replikation ist nur dann ein belastbarer Fortschritt gegenüber dem ersten
Control, wenn die 12-1-Top-2-Regel auch im zweiten Universum über mehrere
Rolling-Fenster und im Holdout positive Ergebnisse zeigt und der Befund nicht
nur von einer Einzelaktie getragen wird.

Ein positives Ergebnis wäre weiterhin kein Produktionsnachweis. Es würde die
Mechanik lediglich für eine größere Multi-Universe-Replikation qualifizieren.

Ein negatives Ergebnis wäre ebenfalls wertvoll: Dann wäre die erste kleine
Stichprobe eher als lokales/spezifisches Signal einzustufen.

## Sicherheitszustand

Keine Produktionsstrategie geändert.
Keine Live-Ausführung.
Keine Orders.
Paper-Only bleibt aktiv.
