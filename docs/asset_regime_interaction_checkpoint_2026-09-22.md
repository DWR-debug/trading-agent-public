# Rolling-WF Asset-x-Regime-Interaktions-Checkpoint — 2026-09-22

## Laufidentität

- Rolling-Control Workflow Run: 35750723097
- Rolling-Control Artifact: 10704817758
- Rolling-Control Diagnostic-Fingerprint: 4fbd29349792371765c43fb25dc8264bdf035ee05eaa76f1b215f9e0d9ba85af
- Kombinierte Regime-/Trend-/Choppiness-Analyse Workflow Run: 35753706618
- Kombinierte Analyse-Fingerprint: 33536438050b545f2c3e2a484f1941197f3205570f2cc3de9283e14bc81f94d0
- Asset-x-Regime-Analyse Workflow Run: 35754173209
- Asset-Analyse-Artifact: 10706073896
- Asset-Analyse-Artifact-Digest: sha256:dd6282993489ca23c86e994cd874bbe29b0fc3dd24410bde4604594a4390116b
- Asset-Analyse-Fingerprint: fc069b7fff159dc9772162cbdf781d42bbcd41a52755d04ada1ffab2ce67581d
- Universe: benchmark — SPY, QQQ, IWM
- Research-Basis: 4.500 Candles je Asset aus dem archivierten 5.000-Candle-Datensatz
- Evaluationen: 240
- Benachbarte Übergänge: 216

## Reproduzierbarkeit und Sicherheit

Der Asset-Layer nutzt ausschließlich das bereits immutable archivierte Rolling-Control-Artifact. Vor der Analyse wurden die Rohdaten erneut über Byte-SHA-256, Full-Dataset-Fingerprint, Research-Fingerprint und Candle-Anzahl verifiziert.

Es wurden keine neuen Daten geladen, keine Backtests ausgeführt und keine Optimierungen durchgeführt. Strategy, Parameterraum, Selection-Profile und Gates bleiben unverändert.

Paper-Only: True
Live-Trading: False
Orders: False

## Asset-Gesamtbild

| Asset | Geometrie | Evaluationen | eindeutige Marktfenster | positive Ergebnisse | PF-Pass | Median Profit EUR | Migration-Rate |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPY | Small | 60 | 15 | 41,7 % | 40,0 % | -0,69 | 41,1 % |
| SPY | Large | 20 | 5 | 35,0 % | 35,0 % | -3,21 | 50,0 % |
| QQQ | Small | 60 | 15 | 40,0 % | 35,0 % | -2,28 | 50,0 % |
| QQQ | Large | 20 | 5 | 35,0 % | 25,0 % | -1,30 | 68,8 % |
| IWM | Small | 60 | 15 | 30,0 % | 26,7 % | -6,47 | 64,3 % |
| IWM | Large | 20 | 5 | 40,0 % | 25,0 % | -4,13 | 81,3 % |

Damit sind die Unterschiede nicht auf einen einzelnen geometrischen Effekt beschränkt. IWM weist zugleich die höchste Kandidatenmigration und die niedrigeren PF-Pass-Raten auf.

## Asset x kombiniertes Regime

### SPY

| Geometrie | Volatilität | Struktur | Eindeutige Marktfenster | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Small | low | choppy | 2 | 8 | 37,5 % | 37,5 % | -1,52 |
| Small | low | mixed | 1 | 4 | 50,0 % | 50,0 % | +3,70 |
| Small | low | trending | 5 | 20 | 35,0 % | 30,0 % | -1,70 |
| Small | middle | choppy | 1 | 4 | 0,0 % | 0,0 % | -17,03 |
| Small | middle | mixed | 1 | 4 | 50,0 % | 50,0 % | -0,31 |
| Small | middle | trending | 2 | 8 | 50,0 % | 50,0 % | +0,87 |
| Small | high | choppy | 1 | 4 | 100,0 % | 100,0 % | +5,97 |
| Small | high | mixed | 1 | 4 | 0,0 % | 0,0 % | -7,04 |
| Small | high | trending | 1 | 4 | 75,0 % | 75,0 % | +4,57 |
| Large | low | trending | 1 | 4 | 50,0 % | 50,0 % | -4,62 |
| Large | middle | mixed | 1 | 4 | 25,0 % | 25,0 % | -1,72 |
| Large | middle | trending | 1 | 4 | 0,0 % | 0,0 % | -23,87 |
| Large | high | choppy | 1 | 4 | 25,0 % | 25,0 % | -3,60 |
| Large | high | mixed | 1 | 4 | 75,0 % | 75,0 % | +15,74 |

### QQQ

| Geometrie | Volatilität | Struktur | Eindeutige Marktfenster | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Small | low | choppy | 1 | 4 | 25,0 % | 25,0 % | -10,66 |
| Small | low | mixed | 3 | 12 | 41,7 % | 41,7 % | -2,43 |
| Small | low | trending | 4 | 16 | 18,8 % | 18,8 % | -2,06 |
| Small | middle | mixed | 3 | 12 | 58,3 % | 58,3 % | +4,24 |
| Small | high | choppy | 1 | 4 | 50,0 % | 50,0 % | +2,78 |
| Small | high | mixed | 2 | 8 | 37,5 % | 0,0 % | -8,44 |
| Small | high | trending | 1 | 4 | 75,0 % | 75,0 % | +6,76 |
| Large | low | mixed | 1 | 4 | 75,0 % | 50,0 % | +2,66 |
| Large | middle | mixed | 2 | 8 | 37,5 % | 37,5 % | -1,30 |
| Large | high | mixed | 1 | 4 | 25,0 % | 0,0 % | -0,44 |
| Large | high | trending | 1 | 4 | 0,0 % | 0,0 % | -16,13 |

### IWM

| Geometrie | Volatilität | Struktur | Eindeutige Marktfenster | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| Small | low | choppy | 1 | 4 | 25,0 % | 25,0 % | -4,37 |
| Small | low | mixed | 3 | 12 | 16,7 % | 16,7 % | -7,65 |
| Small | low | trending | 4 | 16 | 31,2 % | 25,0 % | -7,52 |
| Small | middle | choppy | 1 | 4 | 50,0 % | 50,0 % | +6,41 |
| Small | middle | mixed | 1 | 4 | 25,0 % | 25,0 % | -13,30 |
| Small | middle | trending | 2 | 8 | 37,5 % | 37,5 % | -6,47 |
| Small | high | choppy | 1 | 4 | 25,0 % | 0,0 % | -10,66 |
| Small | high | trending | 2 | 8 | 37,5 % | 37,5 % | -5,37 |
| Large | low | mixed | 1 | 4 | 50,0 % | 50,0 % | +1,12 |
| Large | middle | choppy | 1 | 4 | 50,0 % | 0,0 % | -4,70 |
| Large | middle | trending | 1 | 4 | 0,0 % | 0,0 % | -4,13 |
| Large | high | choppy | 1 | 4 | 75,0 % | 75,0 % | +14,26 |
| Large | high | trending | 1 | 4 | 25,0 % | 0,0 % | -35,92 |

Viele Zellen enthalten nur ein bis drei eindeutige Marktfenster. Solche Zellen sind deshalb Beobachtungspunkte und kein stabiler Nachweis.

## Kandidatenmigration

| Asset | Geometrie | Transitions | Migrationen | Migration-Rate | positive Destinationen | PF-Pass | Median Destination Profit EUR |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPY | Small | 56 | 23 | 41,1 % | 41,1 % | 39,3 % | -0,69 |
| SPY | Large | 16 | 8 | 50,0 % | 25,0 % | 25,0 % | -4,56 |
| QQQ | Small | 56 | 28 | 50,0 % | 41,1 % | 35,7 % | -1,48 |
| QQQ | Large | 16 | 11 | 68,8 % | 25,0 % | 12,5 % | -4,77 |
| IWM | Small | 56 | 36 | 64,3 % | 32,1 % | 28,6 % | -5,35 |
| IWM | Large | 16 | 13 | 81,3 % | 50,0 % | 31,3 % | -4,52 |

Die Asset-Aufteilung unterstützt damit die Beobachtung, dass Kandidatenmigration stark assetabhängig ist. IWM zeigt im untersuchten Datensatz die höchste Migration in beiden Rolling-Geometrien.

## Fachliche Einordnung

Die Asset-Aufteilung erklärt den Rolling-WF-Engpass ebenfalls nicht durch eine einzige Regel. Sie zeigt jedoch, dass die bisherige Failure-Struktur nicht homogen über SPY, QQQ und IWM verteilt ist.

IWM kombiniert im aktuellen Artifact die niedrigste PF-Pass-Quote mit der höchsten Kandidatenmigration. QQQ liegt dazwischen, während SPY die geringste Migration aufweist. Dieses Muster ist über beide Geometrien sichtbar.

Gleichzeitig bleiben die kombinierten Regimeeffekte asset- und geometrieabhängig. Beispielsweise ist das high-volatility/trending-Regime bei Large für IWM und QQQ klar schwach, während die Small-Ergebnisse dort bei einzelnen Assets deutlich anders ausfallen. Die wenigen eindeutigen Marktfenster in vielen Zellen verhindern eine robuste Generalisierung.

Daher wird aus dieser Analyse weiterhin keine automatische Änderung von Parameterraum, Selection-Profilen oder Gates abgeleitet.

## Nächster sinnvoller Diagnose-Layer

Die bisherige Kette hat jetzt drei Ebenen sauber getrennt:

1. Zeit- und Horizon-Struktur
2. Volatilität und Marktstruktur
3. Asset-spezifische Interaktion und Kandidatenmigration

Der nächste diagnostische Schritt sollte deshalb nicht noch eine weitere freie Regimezerlegung sein, sondern die **Stabilität der Failure-Metriken direkt nach Kandidatenwechseln**: Vergleich des ersten OOS-Fensters nach einer Migration mit dem entsprechenden Fenster bei stabilem Kandidaten, getrennt nach Asset und Geometrie. Damit testen wir die inzwischen stärkste Hypothese gezielt, ohne Strategie, Parameterraum oder Gates zu verändern.
