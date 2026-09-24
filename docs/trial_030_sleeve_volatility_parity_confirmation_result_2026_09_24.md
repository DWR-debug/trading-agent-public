# Ergebnis: Trial T-2026-09-24-030 — Sleeve Volatility Parity Confirmation

## Status

**NO_SUPPORT / archived_rejected**

Trial 030 wurde als bestätigender, einmaliger Risk-Allocation-Control auf einem
neuen vollständig symbol-disjunkten Datensatz ausgeführt. Es gab keine
Parameter-, Threshold-, Varianten- oder Holdout-Suche.

## Technischer Nachweis

- Coverage-Preflight: Workflow `36040186007`, Artifact `10825967102`
- Research-Workflow: `36040997311`
- Artifact: `10825679094`
- Artifact-SHA256: `sha256:cc46dfadb3581fab21012b651b857b32e06a43dc37399d45479423da899f2191`
- Report-Fingerprint: `26cc96a1d7210a97443016f5374fccc2e1c466ce2eb1f6859ca778c9a3eefabe`
- Manifest-Fingerprint: `9ef4c9fa58e6a8a573d0836379572d7a441a2fb5300fc4eca33155b2059cf224`
- 13 neue vollständig symbol-disjunkte ETFs
- 3.500 Ziel-Candles je Symbol; 3.520 tatsächlich vorbereitet
- 3.498 gemeinsame PIT-Returns im Researchlauf
- 2.798 Research / 700 blinder Holdout
- vollständige Testsuite, Safety, Universe-Check, Kostenvertrag und Ergebnisintegrität: grün
- keine Orders

## Intervention

Unverändert:
- 50 % SMA 50/200 Trend-Sleeve;
- 50 % 12-1 CS Top-2;
- aggregiertes 63-Session-/10%-Volatilitätsbudget;
- gleiche Point-in-Time-Ausführung und Kosten.

Einzige Änderung:
- monatliche Sleeve-Gewichtung nach inverser 63-Tage-Volatilität;
- Gewichte summieren sich auf 100 %;
- Allokationsumschaltungen werden als Turnover kostenwirksam;
- Warm-up 50/50;
- kein Shorting, kein Hebel.

## Base-Szenario

| Kennzahl | Fixed Candidate | Parity Challenger |
|---|---:|---:|
| Research Return | +32,69 % | +21,19 % |
| Research Max DD | 18,30 % | 19,19 % |
| Research PF | 1,064 | 1,046 |
| Rolling PF | 1,064 | 1,046 |
| Ø Rolling DD | 13,81 % | 14,15 % |
| OOS/IS | 0,720 | 1,112 |
| Holdout Return | +23,54 % | +23,56 % |
| Holdout Max DD | 12,37 % | 12,32 % |
| Holdout PF | 1,148 | 1,149 |

Der Challenger verbessert die Holdout-Rendite nur um rund 0,02 Prozentpunkte,
den Holdout-PF marginal und den Holdout-DD minimal. Gleichzeitig verschlechtert
er die Research-Rendite, Research-DD, Research-PF, Rolling-PF und den
durchschnittlichen Rolling-DD.

## Präregistrierte Entscheidung

Die absoluten Research-Kriterien für DD/PF/Rolling-PF/Rolling-DD und Holdout-DD
werden verfehlt. Der Nicht-Verschlechterungsvertrag scheitert bei Research-Return,
Research-DD, Research-PF, Rolling-PF und durchschnittlichem Rolling-DD.

Formaler Status: **BLOCKED / NO_SUPPORT**.

## Konsequenz

Keine weitere Risk-Parity-/Volatility-Parity-Suche und kein Tuning dieses Controls.
Keine Produktionsintegration, keine Echtgeldfreigabe, keine Orders.

## Sicherheitsstatus

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`

Keine Live-Ausführung.
