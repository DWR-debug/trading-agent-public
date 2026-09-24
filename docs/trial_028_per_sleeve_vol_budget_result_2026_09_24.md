# Ergebnis: Trial T-2026-09-24-028 — Per-Sleeve Volatility Budget

## Status

**Entscheidung: NO_SUPPORT / archived_rejected**

Der präregistrierte Risiko-Control wurde vollständig auf einem neuen,
symbol-disjunkten 13-ETF-Validierungssatz ausgeführt. Es gab keine
Parameter-, Threshold-, Varianten- oder Holdout-Suche.

## Technischer Nachweis

- PR #134: gemerged
- finaler Workflow: `36038357899`
- Artifact-ID: `10825414801`
- Artifact-SHA256: `sha256:1d733848e28cdecf0c7ea9a5a85dcf0cf9f089fa79eeaafe341c424743c74834`
- Report-Fingerprint: `ee00872c970d9c6935ced344a5642b5b17e27e8ce072a97462518b5a203bc57a`
- Manifest-Fingerprint: `f99f1b40c931c860987c26c65fe988a9d140c866f7370fddad2e40af2ec9b2dd`
- Code-Commit: `1b2a2918d99a54e933adb8cfe8f1a3b357bb7118`
- 13 vollständig symbol-disjunkte ETFs
- 3.500 Daily-Candles je Asset
- 3.498 gemeinsame PIT-Return-Perioden
- 2.798 Research / 700 blinder Holdout
- 662 Tests sowie alle Safety-, Disjointness-, Präregistrierungs- und
  Kostenprüfungen grün
- Ergebnisintegrität grün
- keine Orders

## Einzige Intervention

Der feste Kandidat blieb unverändert:

- 50 % SMA-50/200 inverse-volatility Trend-Sleeve;
- 50 % 12-1 Cross-Sectional Momentum Top-2;
- bestehende Point-in-Time-Ausführung;
- bestehender 63-Sessionen-/10%-Volatilitätsmechanismus;
- gleiche Gebühren und Slippage.

Nur die Reihenfolge der Risikosteuerung wurde verändert:
Das 63-Sessionen-/10%-Volatilitätsbudget wurde zuerst separat auf jede
Sleeve angewendet und erst danach wurden beide Sleeves mit 50/50 aggregiert.

## Ergebnis im Base-Szenario

| Kennzahl | Fixed Candidate | Per-Sleeve Budget |
|---|---:|---:|
| Research Return | +48,63 % | +48,18 % |
| Research Max DD | 22,48 % | 17,55 % |
| Research PF | 1,075 | 1,085 |
| Profitable Rolling-Fenster | 4/5 | 4/5 |
| Ø Rolling DD | 14,98 % | 13,52 % |
| OOS/IS | 0,589 | 0,590 |
| Holdout Return | +28,66 % | +28,45 % |
| Holdout Max DD | 10,25 % | 9,65 % |
| Holdout PF | 1,165 | 1,190 |

Der Control reduziert den Research-Drawdown um **4,93 Prozentpunkte**,
verbessert den Research-PF um **0,0103**, reduziert den Holdout-Drawdown
um **0,61 Prozentpunkte** und erhöht den Holdout-PF um **0,0253**.

Gleichzeitig sinkt die Research-Rendite um **0,44 Prozentpunkte** und die
Holdout-Rendite um **0,21 Prozentpunkte**. Die absoluten Research-Risiko-
und PF-Schwellen werden damit weiterhin nicht vollständig erreicht.

## Kostenstress

| Szenario | Fixed Holdout | Per-Sleeve Holdout |
|---|---:|---:|
| Base | +28,66 % | +28,45 % |
| 1,5x Kosten | +27,55 % | +27,64 % |
| 2x Kosten | +26,44 % | +26,83 % |

Die Total-Return-Sensitivität bleibt ebenfalls positiv:
**+31,71 %** Holdout im Base-Szenario, **+30,87 %** bei 1,5x Kosten und
**+30,04 %** bei 2x Kosten.

## Präregistrierte Gates

**Absolute Gates**

- Research-Return: PASS
- Research-Drawdown: FAIL
- Research-PF: FAIL
- Rolling-PF: FAIL
- profitable Rolling-Fensterquote: PASS
- durchschnittlicher Rolling-Drawdown: FAIL
- OOS/IS: PASS
- Holdout positiv: PASS
- Holdout-PF: PASS
- Holdout-Drawdown: PASS
- 1,5x-Kostenstress: PASS
- 2x-Kostenstress: PASS
- Total-Return-Sensitivität: PASS

**Nicht-Verschlechterung gegenüber dem festen Kandidaten**

- Research-Return: FAIL
- Research-Drawdown: PASS
- Research-PF: PASS
- Rolling-PF: PASS
- profitable Rolling-Fensterquote: PASS
- durchschnittlicher Rolling-Drawdown: PASS
- OOS/IS: PASS
- Holdout-Return: FAIL
- Holdout-PF: PASS
- Holdout-Drawdown: PASS

Formaler Status: **BLOCKED / NO_SUPPORT**.

## Diagnostische Bedeutung

Trial 028 liefert einen deutlich konsistenteren Risikobefund als die zuvor
verworfenenen allgemeinen Cash-/Market-Gates: Die separate Sleeve-Steuerung
reduziert das Drawdown-Niveau in Research und Holdout und verbessert den PF,
ohne den Holdout in den negativen Bereich zu drücken.

Sie ist dennoch kein neuer gültiger Produktionskandidat, weil die
präregistrierte Nicht-Verschlechterung des Return nicht erfüllt wird und die
Research-Gates weiter verfehlt werden.

Die Regel wird deshalb nicht nachträglich auf Rendite optimiert.

## Konsequenz

- kein Threshold-/Lookback-Tuning;
- keine alternative Sleeve-Volatilitätsfenster-Suche;
- keine Lockerung der Research-Gates;
- keine Leverage-/Short-Erweiterung;
- keine Produktionseinbindung;
- keine Echtgeldfreigabe;
- keine Orders.

Trial 028 wird dauerhaft als **interessanter Risk-Control-Befund ohne
Promotion-Unterstützung** archiviert.

## Nächster Forschungsschritt

Die robuste Forschungsfrage verschiebt sich damit weg von weiteren
Cash-/Volatilitäts-Gates hin zur **Kapitalallokation zwischen den bereits
bestehenden Sleeves**: Ein einmalig präregistrierter, fester
Risk-Parity-/Risk-Contribution-Control kann prüfen, ob die durch Trial 028
sichtbar gewordene CS-Konzentration durch eine andere feste Aggregation
reduziert werden kann, ohne zusätzlichen Signal- oder Parameter-Tuning.

Dieser nächste Control muss wieder:
- einen neuen vollständig symbol-disjunkten Validierungssatz verwenden;
- einen blinden Holdout enthalten;
- dieselben Kosten und PIT-Regeln verwenden;
- gegen den unveränderten Fixed Candidate gepaart geprüft werden;
- bei Nichtbestehen archiviert werden.

## Sicherheitsstatus

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`

Keine Live-Ausführung.
