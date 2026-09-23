# Risk-Layer-Window 31 vs 63 — Ergebnis 2026-09-23

## Forschungsfrage

Geprüft wurde die einzige aus dem replizierten Rapid-Drawdown-Lag abgeleitete,
präregistrierte Intervention: 31 statt 63 Sessions für die
Realized-Volatility-Schätzung bei unverändertem 10%-Jahresziel.

## Methodik

- identischer Fixed Candidate
- identische Signale und 50/50-Aggregation
- identische PIT-Semantik und Kosten
- vier vollständig symbol-disjunkte Validierungsfamilien
- fünf feste Research-Rolling-Fenster je Familie
- 2.798 Research-Returns je Familie
- keine Zwischenfenster
- Holdout weder berichtet noch zur Entscheidung verwendet
- exakte 63-Session-Parität gegen den bestehenden Control

## Ergebnis

| Validierung | Research DD 31 | Research DD 63 | Rolling PF 31 | Rolling PF 63 | Rapid-Timing verbessert |
|---|---:|---:|---:|---:|---|
| 1 | 15,13% | 16,81% | 1,079 | 1,075 | Nein |
| 2 | 20,88% | 24,87% | 1,017 | 1,017 | Nein |
| 3 | 22,56% | 21,27% | 1,035 | 1,032 | Nein |
| 4 | 18,90% | 19,50% | 1,068 | 1,064 | Ja |

Präregistrierte Replikationszahlen:

- Rapid-Delayed-Rate verbessert: 1/4
- Rapid-Onset-Active-Rate verbessert: 1/4
- Research-DD nicht schlechter: 3/4
- Research-Rolling-PF nicht schlechter: 4/4

Die Bedingung für eine weitere unabhängige Validierung wird damit nicht erreicht.

## Fachlicher Befund

Die 31-Session-Variante verbessert das Research-Drawdown in 3/4
Validierungssets und den Research-Rolling-PF in 4/4. Sie behebt aber die
replizierte Rapid-Drawdown-Timing-Lücke nicht ausreichend: nur 1/4
Validierungssets zeigen gleichzeitig eine Verbesserung der präregistrierten
Rapid-Timing-Metriken.

Damit gibt es keinen replizierten Hinweis, dass die Fensterlänge 63 Sessions
selbst der universelle Ursprung der Risk-Layer-Latenz ist.

- Validierung 1: DD 15,13% vs. 16,81%, PF 1,079 vs. 1,075; Rapid-Timing unverändert.
- Validierung 2: DD 20,88% vs. 24,87%, PF praktisch unverändert; kein Rapid-Ereignis.
- Validierung 3: DD 22,56% vs. 21,27% verschlechtert, PF 1,035 vs. 1,032 verbessert; Rapid-Latenz bleibt bestehen.
- Validierung 4: DD 18,90% vs. 19,50%, PF 1,068 vs. 1,064; Rapid-Timing verbessert.

## Konsequenz

Keine Umstellung von 63 auf 31 Sessions und keine weitere Suche über
Fensterlängen.

Der nächste Forschungsschritt darf deshalb die Reaktionslogik der Risk Layer
isolieren, nicht erneut ungerichtet die Parameterfläche erweitern.

## Provenienz

- PR #49: Research: test 31 vs 63 session risk window
- Run: 35870752087
- Artifact: 10754661827
- Artifact-Digest: sha256:d57a02e435663a6b669a5f25e886cbe228cdf60096eb8536d031b16554c2ea18
- Experiment-Fingerprint: 2aaaf9f1bfa49991a16da4973e44eef2c870c8cb7dc2e6f4e3f35395d22ee3db
- vollständige Testsuite: bestanden
- 63-Session-Parität: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- Holdout nicht zur Auswahl verwendet