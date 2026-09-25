# Trial T-2026-09-25-044 — Ergebnis

## Status

**NO_SUPPORT / archived_rejected**

T044 war der rein technische Repair-Successor zu T043. Das Coverage-Gate war
bestanden; die formale Evaluation wurde anschließend auf exakt 3.500 gemeinsamen
Candles, 2.798 Research-Returns und 700 blinden Holdout-Returns durchgeführt.

## Formale Provenienz

- Workflow: `36113366355`
- Artifact: `10853724277`
- Report-Fingerprint: `e64b4f9c65f47cad6f51ce614ec7ebf1c1a7f96c2df206f372aea04d656fd861`
- eingefrorener Coverage-Fingerprint: `e72ec9c6edc259ff60fada9112cda76081c4c9b214859d239858af0836b037bc`
- Parent: T043
- keine Holdout-Selektion, keine Parameter-/Variantensuche
- 724+ Tests in der zugrunde liegenden CI-Baseline; formaler Orchestratorlauf erfolgreich
- keine Orders, Paper-Only aktiv

## Hauptbefund

Der Challenger ersetzt ausschließlich das Trend-Signal des festen 50/50-Kandidaten
durch eine long-only einstimmige 63/126/252-Session-TSM-Konsistenz.

| Kennzahl | Fixed 50/50 | T044 Challenger |
|---|---:|---:|
| Research Return | +68,09 % | +45,97 % |
| Research Max-DD | 14,56 % | 13,38 % |
| Research PF | 1,100 | 1,078 |
| OOS/IS-Ratio | 0,332 | 0,314 |
| Holdout Return | +22,61 % | +14,43 % |
| Holdout Max-DD | 14,60 % | 17,12 % |
| Holdout PF | 1,142 | 1,096 |
| profitable Research-Rolling-Fenster | 4/5 | 4/5 |
| Ø Rolling-DD | 10,84 % | 11,36 % |

Der Challenger verbessert im Research den Max-DD nur um rund 1,18 Prozentpunkte.
Gleichzeitig verliert er 22,11 Prozentpunkte Research-Rendite. Im blinden
Holdout verliert er 8,18 Prozentpunkte Rendite, erhöht den Max-DD um 2,52
Prozentpunkte und senkt den PF.

Die Total-Return-Sensitivität bleibt positiv und die 1,5x-/2x-Kostenstress-Holdouts
bleiben positiv. Diese Teilbefunde reichen jedoch nicht zur Promotion.

## Rolling-Diagnose

Die Veränderung ist nicht konsistent über die fünf Research-Fenster:

- Fenster 1: Challenger schwächer bei Rendite, DD und PF.
- Fenster 2: Rendite etwas weniger negativ, aber kein Vorteil bei DD/PF.
- Fenster 3: Challenger deutlich renditeschwächer bei ähnlichem DD.
- Fenster 4: Challenger ist der einzige klare DD-/PF-Verbesserungsbereich.
- Fenster 5: Challenger erneut deutlich renditeschwächer.

Das spricht gegen eine robuste Generalisierung der strengeren Konsistenzfilterung.

## Entscheidung

T044 wird nicht in die Produktionsstrategie integriert.
Es gibt kein Tuning der 63/126/252-Lookbacks, keine Suche nach anderer
Konsensschwelle und keine nachträgliche Holdout-Auswahl.

Die technische Repair-Logik von T044 bleibt als reproduzierbares Muster für
gemeinsame Kalender-Reparaturen erhalten; die Signalhypothese selbst wird
geschlossen.

## Sicherheitsstatus

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`  
`automatic_promotion=False`
