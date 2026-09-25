# Q012 Information-Alpha Temporal Stability — Ergebnis 2026-09-25

## Status

**COMPLETED_DISCOVERY_ONLY.** Keine Performanceevidenz, keine Hypothesen-/Asset-/Parameterauswahl und keine Promotion.

## Ausführung

- Workflow: 36148187652
- Artifact: 10870661281
- Artifact-SHA256: 7af99a87b2bf79e63806e9b5ccb4a782fcc91950bc9541528d518d85ff411912
- Q012-Result-Fingerprint: d9fcf20826282fa881c6d960e79b759e2f4ac2dac911bde9d33c2839df4edc2c
- Fenster: 2026-03-29 bis 2026-09-24
- Assets: SPY, TLT, GLD
- gemeinsame Beobachtungen: 123
- Event-Fenster: 25
- Roh-GDELT-Zeilen: 17,636,611; übersprungen: 101

## Point-in-Time-Vertrag

Event-Features wurden ausschließlich für previous_market_day < event_day < target_market_day gebildet. Der Next-Day-Return ist previous_market_close -> target_market_close; der Five-Day-Horizont startet am Target-Close. Same-Day-Returns wurden nicht verwendet.

## Befund

Die zeitliche Stabilität ist **heterogen und nicht als allgemeiner, stabiler GDELT-Effekt interpretierbar**:

- Die Next-Day-Vorzeichen bleiben über die beiden chronologischen Hälften in 12 von 18 festen Asset/Feature-Paaren gleich (66,7 %).
- Für den Five-Day-Horizont sind es 9 von 18 (50,0 %).
- SPY-Beziehungen bleiben sehr klein.
- TLT wechselt bei allen sechs festen Features das Vorzeichen zwischen den Hälften.
- GLD hält bei allen sechs Features das Vorzeichen; die Effektgrößen bleiben jedoch moderat, und mehrere Volumen-/Aufmerksamkeitsfeatures sind redundant.

## Wissenschaftliche Konsequenz

Q012 liefert einen belastbaren **Diagnosebefund**, aber keinen Performancekandidaten. Insbesondere autorisiert Q012 keine Auswahl eines „besten“ Features, Assets oder Horizonts und keine Änderung bestehender Gates.

Der nächste sinnvolle diagnostische Schritt ist daher die **Mechanismus-/Redundanzprüfung der sechs bereits fixierten GDELT-Features** auf derselben eingefrorenen längeren Stichprobe: Event-Präsenz, gemeinsame Volumen-/Aufmerksamkeitskomponenten sowie Tone/Severity sollen getrennt werden, ohne eine Feature-Auswahl für Trading zuzulassen.

## Sicherheit

`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`, `automatic_promotion=False`.
