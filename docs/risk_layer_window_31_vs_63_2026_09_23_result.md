# Risk-Layer-Window 31 vs 63 — Ergebnis 2026-09-23

## Fragestellung

Geprüft wurde die einzige aus dem replizierten Rapid-Drawdown-Lag abgeleitete
präregistrierte Intervention: ein 31-Session- statt 63-Session-Fenster für die
Realized-Volatility-Schätzung bei unverändertem 10%-Jahresziel.

## Methodik

- identischer Fixed Candidate
- identische Signale und 50/50-Aggregation
- identische PIT-Semantik und Kosten
- vier vollständig symbol-disjunkte Validierungsfamilien
- fünf Research-Rolling-Fenster je Familie
- 2.798 Research-Returns je Familie
- keine Zwischenfenster
- Holdout weder berichtet noch zur Entscheidung verwendet
- exakte 63-Session-Parität gegen den bestehenden Control

## Ergebnis

| Validierung | Research DD 31 | Research DD 63 | Rolling PF 31 | Rolling PF 63 | Rapid Timing verbessert? |
|---|---:|---:|---:|---:|---|
| 1 | 15,13% | 16,81% | 1,079 | 1,075 | Nein |
| 2 | 20,88% | 24,87% | 1,017 | 1,017 | Nein |
| 3 | 22,56% | 21,27% | 1,035 | 1,032 | Nein |
| 4 | 18,90% | 19,50% | 1,068 | 1,064 | Ja |

Die präregistrierten Replikationszahlen:

- Rapid-Delayed-Rate verbessert: **1/4**
- Rapid-Onset-Active-Rate verbessert: **1/4**
- Research-DD nicht schlechter: **3/4**
- Research-Rolling-PF nicht schlechter: **4/4**

Der vollständige Support für einen fünften unabhängigen Validierungssatz ist damit
nicht erreicht. Der Hauptgrund ist nicht eine generelle Verschlechterung der
Research-Risikokennzahlen, sondern dass die 31-Session-Variante die vorher
replizierte Rapid-Drawdown-Timing-Lücke nicht in ausreichendem Umfang schließt.

## Interpretation

Das spricht dagegen, dass die beobachtete Risk-Layer-Latenz primär durch die
63-Session-Länge verursacht wird. Eine kürzere Schätzperiode verändert das
Research-Risikoprofil teilweise positiv, reproduziert aber den schnellen
Drawdown-Timing-Effekt nicht.

Insbesondere Validierung 1 und 4 zeigen Verbesserungen bei DD und Rapid-Timing
unterschiedlich stark; Validierung 3 zeigt dagegen weiterhin eine verzögerte
Rapid-Reaktion trotz kürzerer Schätzperiode. Damit liegt kein universeller
Window-Length-Mechanismus vor.

## Konsequenz

Keine Umstellung der Produktions-/Research-Referenz von 63 auf 31 Sessions.
Keine weitere Suche über andere Fensterlängen.

Der nächste zulässige Forschungsschritt muss deshalb die **Reaktionslogik** statt
die Fensterlänge isolieren. Eine neue Intervention darf nur als einzelne,
vollständig präregistrierte Hypothese definiert werden; Holdout bleibt bis zu
einer unabhängigen Validierung unberührt.

## Provenienz

- PR #49, Research: test 31 vs 63 session risk window
- Run: `35870752087`
- Artifact: `10754661827`
- Artifact-Digest: `sha256:d57a02e435663a6b669a5f25e886cbe228cdf60096eb8536d031b16554c2ea18`
- Experiment-Fingerprint: `2aaaf9f1bfa49991a16da4973e44eef2c870c8cb7dc2e6f4e3f35395d22ee3db`
- Volltests: bestanden
- 63-Session-Parität: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- keine Orders
- keine Produktionsänderung
- Holdout nicht zur Auswahl verwendet