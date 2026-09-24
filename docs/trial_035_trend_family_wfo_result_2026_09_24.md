# Trial 035 — Trend Family Walk-Forward Control — Ergebnis — 2026-09-24

## Entscheidung

**NO_SUPPORT / archived_rejected**

Die präregistrierte Family-Level-WFO-Übertragung der drei bereits untersuchten Trendfamilien
erreicht auf der vollständig symbol-disjunkten neuen 10-ETF-Validierungsbasis keinen
belastbaren OOS-Nachweis.

## Technischer Nachweis

- Research-Workflow: `36049312220`
- Research-Artefakt: `10829279056`
- Artifact-ZIP-SHA256: `fb109731fc767f1ac64bf3ffa458d12e7980c08c113e1803cb9f741e2486b94b`
- Report-Fingerprint: `c2ecd54663d29e48c3456887d2a9ed2cc4e92f362c71b1115099192d54f918d4`
- Coverage-Preflight: `36048203151`
- Coverage-Artefakt: `10828838810`
- Coverage-Artifact-SHA256: `e29df32161babcd3a6677d456a4b5572d81afb0c0613e69c62d8c45e4d4dcbfa`
- Coverage-Fingerprint: `f3902d7247663446763a8bf78f370961ddf1cad9c8056b4c993a62745c75c253`
- Manifest-Fingerprint des Research-Laufs: `35b1945569bce3271caabcfa6032da286537d851b31961946a4ca9f0ae67ddfe`
- 10/10 Symbole mit jeweils 3.500 Research-Candles; Preflight jeweils 3.520 Candles
- gemeinsamer Preflight-Kalender: 3.520
- 2.798 Research-Returns / 700 blinder Holdout
- 683 Tests im finalen Research-Run
- PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, orders_enabled=False

## Präregistrierte WFO-Regel

Nur drei bereits getestete Familien durften gewählt werden:

1. `tsm_monthly_equal`
2. `sma_50_200_inverse_vol`
3. `blend_tsm_sma_inverse_vol`

Je Research-Fenster:

- Training: 1.398 Returns
- OOS: 280 Returns
- Auswahl ausschließlich anhand des Training-Profit-Factors, danach Training-Return,
  Training-Drawdown und deterministischem Namens-Tiebreak.

Der im fünften Research-Fenster ausgewählte Kandidat wurde für den gesamten blinden Holdout eingefroren.

Keine Parameter-, Varianten-, Selection-Profile- oder Holdout-Suche.

## Ergebnisse

### WFO-OOS

- Aggregierte OOS-Rendite: **-27,20 %**
- OOS-Max-Drawdown: **31,23 %**
- OOS-Profit-Factor: **0,899**
- Positive OOS-Fenster: **1/5 = 20 %**
- 2x-Kostenstress OOS: **-30,50 %**

Die einzelnen OOS-Fenster waren:

| Fenster | Gewählte Familie | OOS Return | OOS DD | OOS PF |
|---|---|---:|---:|---:|
| 1 | SMA 50/200 inverse-vol | -3,93 % | 11,45 % | 0,931 |
| 2 | SMA 50/200 inverse-vol | -10,09 % | 19,27 % | 0,794 |
| 3 | 50/50 TSM/SMA | +12,51 % | 3,93 % | 1,334 |
| 4 | SMA 50/200 inverse-vol | -9,10 % | 17,33 % | 0,913 |
| 5 | 50/50 TSM/SMA | -17,60 % | 18,60 % | 0,651 |

Die Family-WFO-Auswahl wechselte somit zwar zwischen zwei Familien, übertrug sich aber in
vier von fünf OOS-Fenstern nicht profitabel.

### Blinder Holdout

Die letzte Research-Auswahl war `blend_tsm_sma_inverse_vol`.

- Holdout Return: **+9,57 %**
- Holdout Max-Drawdown: **7,54 %**
- Holdout PF: **1,111**
- 2x-Kostenstress Holdout Return: **+5,65 %**
- 2x-Kostenstress Holdout PF: **1,067**

Damit waren die vier präregistrierten Holdout-Kriterien erfüllt. Das reicht jedoch nicht,
weil der eigenständige WFO-OOS-Vertrag für die Übertragbarkeit klar verfehlt wurde.

## Interpretation

Der Trial liefert damit einen wichtigen Gegenbefund:

Die Fähigkeit, im letzten Research-Fenster eine Familie zu wählen, erzeugte auf diesem
Datensatz **keine robuste positive OOS-Übertragung**, obwohl die anschließend eingefrorene
Familie im Holdout positiv war.

Das ist gerade kein Beleg gegen Trendstrategien insgesamt. Es ist Evidenz gegen diese
konkrete, kleine Family-Selection-Regel auf diesem Validierungsdatensatz.

## Konsequenz

- Keine Produktionseinbindung.
- Kein 30-Tage-Paper-Experiment auf Basis dieses Controls.
- Keine nachträgliche Suche über WFO-Fenster, Traininggröße, Familienauswahlregel oder
  andere Auswahlparameter.
- Kein Holdout-Tuning.
- Der Befund motiviert höchstens neue, klar getrennte Hypothesen über zusätzliche
  Informationsquellen oder Spillover-Strukturen.

## Sicherheitsstatus

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Research-Orders
- keine Live-Ausführung
