# Trial 016 — Ergebnis: Cross-Asset Cross-Sectional Momentum

**Trial-ID:** T-2026-09-24-016  
**Status:** `archived_rejected`  
**Workflow Run:** 35990335834  
**Artifact:** 10803962414  
**Artifact SHA-256:** e09b7a3ff668dbea2b75470bfa8506d9da120f356fa494465d3783188540ad4c  
**Report-Fingerprint:** fa9c9046a7f48588fe12a5347a13350f446f6cdfd65fae9d7d097058160272ea  
**Manifest-Fingerprint:** c4502fe1da2d783ea77e3d75a80b2931362b419f4d30b63f88dfc9cb8a54ae54  
**Code-Version des Runs:** fe44af1452e0de61164fcbecef0416ce8bcbf360

## Forschungsdesign

Präregistrierte Replikation der bestehenden 12-1-Cross-Sectional-Momentum-Mechanik
auf einem vollständig symbol-disjunkten Nicht-Aktien-ETF-Universum:

- DBA, DBB, FXA, FXY, MUB, SHV, EMB, BWX
- 3.500 gemeinsame Tages-Candles
- 3.498 Return-Perioden
- 2.798 Research / 700 Holdout
- Formation 252 Sessions
- Skip 21 Sessions
- Rebalance 21 Sessions
- Top 2, 100 % Long, equal-weight
- keine Hebelung, keine Shorts
- Basis-Kosten 0,15 % je Turnover-Einheit
- Stress: 2× Kosten
- fester SMA-50/200-Control
- fester 50/50-Blend
- keine Parameteroptimierung und keine Holdout-Selektion

Die Datenakquisition bestätigte für jedes der acht Symbole 3.500 Candles und eine
gemeinsame Timestamp-Intersection. Der gemeinsame Zeitraum reichte nach
Ausrichtung vom 17.10.2012 bis 21.09.2026.

## Ergebnis

### Basis-Szenario

| Pfad | Research Return | Research Max DD | Research PF | Holdout Return | Holdout Max DD | Rolling positiv |
|---|---:|---:|---:|---:|---:|---:|
| CS Momentum Top-2 | +0,11 % | 30,51 % | 1,010 | +4,70 % | 13,64 % | 2/5 |
| SMA 50/200 Control | −16,85 % | 24,89 % | 0,957 | +1,81 % | 8,01 % | 1/5 |
| Equal Weight Buy-and-Hold | −20,40 % | 26,77 % | 0,940 | +9,05 % | 6,89 % | 1/5 |
| 50/50 Blend | −8,47 % | 26,77 % | 0,986 | +3,44 % | 8,80 % | 2/5 |

### 2×-Kostenstress

| Pfad | Research Return | Research Max DD | Research PF | Holdout Return | Holdout Max DD | Rolling positiv |
|---|---:|---:|---:|---:|---:|---:|
| CS Momentum Top-2 | −7,70 % | 33,17 % | 0,992 | +2,21 % | 13,77 % | 2/5 |
| SMA 50/200 Control | −23,15 % | 26,48 % | <1 | −0,17 % | 8,49 % | 1/5 |
| Equal Weight Buy-and-Hold | −20,52 % | 26,88 % | 0,939 | +9,05 % | 6,89 % | 1/5 |
| 50/50 Blend | −15,50 % | 29,75 % | 0,966 | +1,21 % | 9,21 % | 2/5 |

## Wissenschaftlicher Befund

Trial 016 liefert **keinen belastbaren Nachweis** für eine robuste zusätzliche
Ertragsquelle.

Der primäre CS-Momentum-Pfad liegt im vollständigen Research-Zeitraum praktisch
bei Null (+0,11 %) und trägt dabei einen Maximum Drawdown von 30,51 %. Unter
verdoppelten Kosten wird daraus −7,70 %. Nur zwei von fünf festen Research-
Rolling-Fenstern sind positiv.

Der Holdout ist mit +4,70 % positiv, wurde aber vollständig blind und nicht zur
Auswahl genutzt. Er reicht zusammen mit dem schwachen Research- und Rolling-
Befund nicht für eine Forschungsübernahme.

Der feste 50/50-Blend bleibt ebenfalls im gesamten Research negativ und wird
daher nicht als zusätzliche Kapazitätsquelle akzeptiert.

**Entscheidung:** `archived_rejected`. Keine Produktionsänderung.

## Forschungsbedeutung

Zusammen mit Trial 014 (Shorting/Leverage) und Trial 015 (Mean Reversion) ergibt
sich ein konsistenterer Negativbefund gegen einfache Maßnahmen wie zusätzliches
Leverage, Shorting oder ein zweites kurzfristiges Signal-/Ranking-Schema als
alleinige Lösung für zusätzliche robuste Ertragskapazität.

Der nächste sinnvolle Forschungsschritt ist daher nicht die weitere Feinoptimierung
dieser drei Familien. Priorität hat die Identifikation wirklich unabhängiger
Renditequellen und anschließend deren Kopplung an das bereits implementierte
Kapital-/Entnahmemodell unter denselben Robustheits- und Kosten-Gates.

## Sicherheit

Der Workflow bestätigte:

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`

Die vollständige Testsuite bestand mit **558 Tests**.
