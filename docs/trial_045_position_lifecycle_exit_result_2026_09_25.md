# Trial T-2026-09-25-045 — Ergebnis

## Status

**NO_SUPPORT / archived_rejected**

T045 prüfte genau eine vorab definierte Intervention: einen festen ATR(20)-Trailing-Exit im Trend-Sleeve des unveränderten 50/50-Kandidaten. Das Coverage-Gate war bestanden; formal wurden 3.500 gemeinsame Candles mit 2.798 Research-Returns und 700 blinden Holdout-Returns verwendet.

## Formale Provenienz

- Coverage-Workflow: `36116824638`
- Coverage-Artefakt: `10855053438`
- Coverage-ZIP SHA256: `21f41f8ba95f303524520302747c7b474c8ae3fbe11a9014f28e1d3abe626ab2`
- Coverage-Fingerprint: `4c82327c957331851b1184a2a947f77f38e0b73d8e6b54a3fafda424d86296dc`
- Formal-Workflow 1 / Artefakt 1: `36117519189` / `10855484049`
- Formal-ZIP SHA256 1: `6c1d35e1543696a29e3ccd576c7228e302ba9e72ad879533b256d53ff6c54744`
- Report-Fingerprint 1: `c1bb8b62e46336e470110a7baaf9db74c6f5d23e49587b5f990423ade7a78562`
- Reproduktionslauf 2 / Artefakt 2: `36117548408` / `10854674939`
- Formal-ZIP SHA256 2: `6981fd12a8f8b1e6b4b28a4eef885af963e1de5922edf9fbe182047872dd0adb`
- Report-Fingerprint 2: `90bb1b7f84b19a8675bab6ed6505931544e2d320c0cdaf199db4c8666a94595a`

## Hauptbefund

| Kennzahl | Fixed 50/50 | T045 ATR-Exit |
|---|---:|---:|
| Research Return | +60,62 % | +41,23 % |
| Research Max-DD | 19,73 % | 20,07 % |
| Research PF | 1,090 | 1,068 |
| OOS/IS-Ratio | 0,349 | 0,202 |
| Holdout Return | +21,13 % | +8,34 % |
| Holdout Max-DD | 9,79 % | 15,98 % |
| Holdout PF | 1,127 | 1,059 |
| profitable Research-Rolling-Fenster | 4/5 | 3/5 |
| Ø Rolling-DD | 14,02 % | 13,07 % |

Der einzige klare Risiko-Vorteil liegt in der durchschnittlichen Rolling-DD (-0,95 Prozentpunkte). Dieser Vorteil reicht weder für das absolute 10-%-Risikogate noch für die Nicht-Verschlechterungsbedingungen.

## Stress- und Sensitivitätsprüfungen

Die Holdout-Rendite des Challengers bleibt unter 1,5x- und 2x-Kostenstress positiv (6,52 % bzw. 4,73 %). Die Total-Return-Sensitivität bleibt ebenfalls positiv. Diese Teilbefunde kompensieren die gescheiterten Gates nicht.

## Lifecycle-Diagnostik

Der Exit löste 391 Stop-Ereignisse im Trend-Sleeve aus. Es entstanden 14.524 Asset-Days ohne Trendposition gegenüber 13.476 Asset-Days mit positiver Trendposition im Lifecycle-Overlay.

Die formale Doppelausführung reproduzierte sämtliche entscheidungsrelevanten Price-Only-Kernkennzahlen und Gate-Ergebnisse. Nur die sekundäre adjusted-close Total-Return-Sensitivität zeigte minimale numerische Laufabweichungen; diese wird nicht als unabhängiger Versuch gezählt.

## Entscheidung

T045 wird nicht in die Strategie integriert. Keine Suche nach anderem ATR-Fenster, anderer ATR-Multiplikation oder anderer Re-Entry-Regel wird aus diesem Ergebnis abgeleitet. Die Hypothese bleibt geschlossen.

Der nächste methodische Schritt ist die Cross-Trial-Failure-Diagnose über T041–T045.

## Sicherheitsstatus

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`  
`automatic_promotion=False`
