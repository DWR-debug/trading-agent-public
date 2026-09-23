# Streng geschichtete Hypothesenbildung und kontrolliertes Gegenexperiment — 2026-09-22

## Ausgangspunkt

Die Regime-Parameter-Failure-Matrix auf dem unveränderten Benchmark-Rolling-Control
führte zu genau einer streng geschichteten, experimentbereiten Hypothese:

- Profil: `trade_rich`
- Geometrie: `small`
- Parameter: `mean_reversion.window`
- Vergleich: 10 vs. 5
- Fixed: risk_per_trade=0.0025, leverage=1.0, momentum.lookback=3, mean_reversion.threshold=0.01
- formaler Evidenzsatz: IWM und QQQ

Die Hypothese wurde nicht als globale Empfehlung interpretiert.

## Unveränderliche Daten- und Kontrollkette

Historischer Rolling-Control:
- Run: 35747170025
- Source-Commit: `62d91c0fa802e983e62879aa0bb7155202f8d7e0`
- Report-Fingerprint: `06ba10b5fb540de887fd2494f8cc328fa849b8f80ac0a867b16386a73525e0e2`
- Manifest-Fingerprint: `2f7124c41901a79f3b7dda684e991ba2008ff09ef0f2a36c96469f2615538836`

Exakter Replay mit Rohdatenarchiv:
- Run: 35766606233
- Artifact: 10712781758
- Artifact-Digest: `sha256:128d99bd79978181e5660cda3bcd34a969e8bd8ac9ae7374b3eba369b25c7599`

Kontrolliertes Gegenexperiment:
- PR #87, Merge-Commit `3eac2f216b4a8ed71233344cc00b53f984283484`
- Run: 35768392064
- Artifact: 10712493969
- Artifact-Digest: `sha256:6ac2a2d139d3ea3ae99695384d8d60451f306ed9225dfe289b6f7c5cfcd1592d`
- Analysis-Fingerprint: `b8b71d4ed86de96c60b8885862a38da61a88d105fd13d62efd6aff2c562b425a`

Dataset-Fingerprints:
- IWM: `51a385563ebd0a3a659d844bcbeccab354f79fd52c1d521633865ff0de476821`
- QQQ: `7923245473b99e9f9f32dafe58d48c3ba101454048eba04a9c14508aacc3b52f`
- SPY: `8c62c32b84fa68b7633670302f90a7f935dc047a1a7ae33cc0e561e79f8266a3`

Paper-Only: True. Live-Trading: False. Orders: False.

## Gegenexperiment

25 formale gepaarte OOS-Fenster wurden auf IWM und QQQ ausgewertet. Der
Originalkandidat musste zuerst die gespeicherten Rolling-Window-Metriken
reproduzieren. Erst dann wurde ausschließlich `mean_reversion.window` auf
den Gegenwert gesetzt.

| Größe | Baseline | Counterfactual |
| --- | ---: | ---: |
| Gesamtprofit IWM+QQQ | -112,03 EUR | -118,86 EUR |
| positive Fensterquote | 28,0 % | 28,0 % |
| PF-Passrate | 20,0 % | 28,0 % |

Gepaarte Profitdifferenz: **-6,82 EUR**.

Asset-spezifisch:
- IWM: positive Fenster 38,5 % -> 23,1 %; PF-Pass 23,1 % -> 23,1 %
- QQQ: positive Fenster 16,7 % -> 33,3 %; PF-Pass 16,7 % -> 33,3 %

Der formale Status lautet:
`hypothesis_not_supported_on_paired_control`

SPY wurde zusätzlich als Hold-out betrachtet: 12 Paare, Profitdelta -1,22 EUR,
positive Fensterquote 33,3 % -> 41,7 %, PF-Pass 33,3 % -> 41,7 %. Dieser Befund
war nicht Teil der Hypothesenformulierung.

## Schlussfolgerung für die Entwicklung

Es wurde keine Parameter-, Selection- oder Gateänderung vorgenommen. Der
Ergebnisbefund ist ein Ausschluss eines konkreten Änderungsansatzes, nicht ein
neuer globaler Parameterentscheid.

Der nächste Research-Schritt ist die Suche nach einer zweiten, unabhängig
replizierbaren Hypothese aus einem anderen streng geschichteten Kontrast.