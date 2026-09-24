# T040 Ergebnis — Network Momentum Repair — 2026-09-24

## Ergebnis

Trial T-2026-09-24-040 wurde nach bestandenem Coverage-Gate formal ausgewertet.

Status: **BLOCKED**  
Scientific outcome: **NO_PROMOTION_EVIDENCE**

Die Datenabdeckung war gültig:
- 12 Symbole
- 3.520 angeforderte Daily-Candles je Symbol
- 3.500 gemeinsame Candles
- 2.798 Research-Returnperioden
- 700 blinde Holdout-Returnperioden

## Challenger

Network Momentum, unverändert präregistriert:

- Basis: Research-Rendite **-33,96%**
- Research-Max-DD **41,45%**
- Research-Profit-Factor **0,907**
- Holdout-Rendite **-11,99%**
- Holdout-Max-DD **17,08%**
- Holdout-Profit-Factor **0,923**

Unter 1,5x Kostenstress:
- Research-Rendite **-40,18%**
- Holdout-Rendite **-15,81%**

Unter 2,0x Kostenstress:
- Research-Rendite **-45,82%**
- Holdout-Rendite **-19,47%**

Rolling:
- 0/5 profitable Research-Rolling-Fenster
- minimale Rolling-PF **0,817**
- durchschnittlicher Rolling-DD **17,77%**

## Feste Kontrolle

SMA-50/200 Long/Flat mit identischer Portfolio-/Kostenmechanik:

- Basis: Research-Rendite **-21,15%**
- Research-Max-DD **32,63%**
- Research-Profit-Factor **0,948**
- Holdout-Rendite **-11,13%**
- Holdout-Max-DD **18,06%**
- Holdout-Profit-Factor **0,926**

Damit erfüllte der Challenger nicht nur die eigenen Gates nicht, sondern verfehlte auch den präregistrierten Nicht-Verschlechterungs-Vergleich.

## Interpretation

Das Ergebnis ist **negative Evidenz für genau den präregistrierten Mechanismus auf diesem Datensatz**. Es ist kein Beleg dafür, dass jede Form von Cross-Asset-Momentum grundsätzlich unwirksam ist.

T039 und T040 werden getrennt archiviert:
- T039: DATA_INVALID wegen unzureichender FTGC-Historie.
- T040: DATA-valid, aber evidenzseitig BLOCKED.

Es gibt keine nachträgliche Parameteränderung, keine Holdout-Auswahl und keinen Versuch,
die Gates nach dem Ergebnis zu lockern.

## Provenienz

Formal report fingerprint:

`912d51447862ba7118dacde2f8acba6c3cce407adec64ea10cbf3aa48661bb65`

Coverage snapshot und formaler Report stammen aus Unified Research Orchestrator Run `36060354235`.

## Sicherheit

PAPER_ONLY=True  
LIVE_TRADING_ENABLED=False  
orders_enabled=False  
automatic_promotion=False  
paid agent/API budget = 0
