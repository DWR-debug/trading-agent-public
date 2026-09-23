# Rolling-WF Kombinierter Regime-/Trend-/Choppiness-Checkpoint — 2026-09-22

## Laufidentität

- Rolling-Control Workflow Run: 35750723097
- Rolling-Control Artifact: 10704817758
- Rolling-Control Diagnostic-Fingerprint: 4fbd29349792371765c43fb25dc8264bdf035ee05eaa76f1b215f9e0d9ba85af
- Kombinierte Analyse Workflow Run: 35753706618
- Analyse-Artifact: 10707282362
- Analyse-Artifact-Digest: sha256:2a2f4e8b5371f45ac40e22e0c19adadc0f7af8eb9443b88f10bd59c6eb8f3b9f
- Analyse-Fingerprint: 33536438050b545f2c3e2a484f1941197f3205570f2cc3de9283e14bc81f94d0
- Research-Basis: 4.500 Candles je Asset aus einem archivierten 5.000-Candle-Datensatz
- Universe: benchmark — SPY, QQQ, IWM
- Market-Features: 60 eindeutige Rolling-Testfenster
- Evaluationen: 240
- Benachbarte Übergänge: 216

## Reproduzierbarkeit und Sicherheit

Vor der Diagnose wurden die archivierten CSV-Dateien anhand ihrer Byte-SHA-256-Werte, Full-Dataset-Fingerprints, Research-Fingerprints und Candle-Anzahlen geprüft. Die Analyse nutzt ausschließlich diese immutable Datenbasis.

Es wurden keine neuen Daten geladen, keine Backtests ausgeführt und keine Optimierungen durchgeführt. Strategie, Parameterraum, Selection-Profile und Gates bleiben unverändert.

Paper-Only: True
Live-Trading: False
Orders: False

## Methodik

### Volatilität

Die ex-ante Volatilität verwendet die Standardabweichung der letzten 20 Log-Close-Returns vor dem jeweiligen Teststart, annualisiert mit 252. Die Regimeklassifikation basiert auf historischen Perzentilen und verwendet ausschließlich Beobachtungen mit einem Endpunkt strikt vor dem Teststart:

- low: unter 33 %
- middle: 33 % bis 67 %
- high: über 67 %

### Trend-/Choppiness-Struktur

Für die letzten 60 Log-Close-Returns vor dem Teststart wird die Directional Efficiency berechnet:
abs(sum(log returns)) / sum(abs(log returns))

Niedrige Effizienz wird als choppy, mittlere als mixed und hohe als trending klassifiziert. Auch hier werden die Grenzwerte aus historischen Perzentilen vor dem jeweiligen Teststart abgeleitet. Die Trendrichtung wird zusätzlich über das Vorzeichen der 60-Tage-Log-Return-Summe beschrieben.

## Kombinierte Ergebnisse

### Small-Geometrie

| Volatilität | Struktur | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |
| --- | --- | ---: | ---: | ---: | ---: |
| low | choppy | 16 | 31,2 % | 31,2 % | -2,98 |
| low | mixed | 28 | 32,1 % | 32,1 % | -3,02 |
| low | trending | 52 | 28,8 % | 25,0 % | -2,41 |
| middle | choppy | 8 | 25,0 % | 25,0 % | -8,18 |
| middle | mixed | 20 | 50,0 % | 50,0 % | -0,22 |
| middle | trending | 16 | 43,8 % | 43,8 % | 0,00 |
| high | choppy | 12 | 58,3 % | 50,0 % | +2,32 |
| high | mixed | 12 | 25,0 % | 0,0 % | -7,04 |
| high | trending | 16 | 56,2 % | 56,2 % | +3,37 |

### Large-Geometrie

| Volatilität | Struktur | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |
| --- | --- | ---: | ---: | ---: | ---: |
| low | mixed | 8 | 62,5 % | 50,0 % | +2,66 |
| low | trending | 4 | 50,0 % | 50,0 % | -4,62 |
| middle | choppy | 4 | 50,0 % | 0,0 % | -4,70 |
| middle | mixed | 12 | 33,3 % | 33,3 % | -1,30 |
| middle | trending | 8 | 0,0 % | 0,0 % | -4,67 |
| high | choppy | 8 | 50,0 % | 50,0 % | +3,55 |
| high | mixed | 8 | 50,0 % | 37,5 % | -0,03 |
| high | trending | 8 | 12,5 % | 0,0 % | -22,88 |

Leere Regimezellen werden nicht als Evidenz interpretiert. Mehrere Large-Zellen enthalten nur zwei eindeutige Marktfenster und werden daher mit besonderer Vorsicht gelesen.

## Trendrichtung

| Geometrie | Richtung | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |
| --- | --- | ---: | ---: | ---: | ---: |
| Small | up | 120 | 32,5 % | 30,8 % | -2,64 |
| Small | down | 60 | 46,7 % | 40,0 % | -2,92 |
| Large | up | 32 | 28,1 % | 21,9 % | -9,28 |
| Large | down | 28 | 46,4 % | 35,7 % | -0,44 |

Die Richtung ist deskriptiv; sie wird nicht als separates Gate verwendet.

## Kandidatenmigration

Über 216 aufeinanderfolgende Übergänge:

- 119 Migrationen
- 97 stabile Kandidaten
- Migrationsrate 55,1 %

Bei zunehmender Volatilität (> +10 Prozentpunkte im ex-ante Volatilitäts-Perzentil) lag die Migrationsrate bei 59,3 %. Bei zunehmender Struktur-Effizienz (> +10 Prozentpunkte) lag sie bei 56,8 %.

Für Strukturänderungen lagen positive Destinationen bei 35,0 % (contracting), 37,5 % (stable band) und 38,6 % (expanding). Der PF-Pass lag bei 30,0 %, 31,3 % und 34,1 %.

Damit steigt die Kandidatenmigration bei starken Strukturänderungen nicht in einem Ausmaß, das einen eigenständigen stabilen Performanceeffekt nahelegt.

## Parameterbezogene Beobachtung

Die häufigsten Änderungen bleiben:

- momentum.lookback: 76
- mean_reversion.window: 75
- mean_reversion.threshold: 62

Die risk_per_trade-Änderungen sind seltener (22), weisen aber in dieser Diagnose eine höhere positive Destination- und PF-Pass-Quote auf als Übergänge ohne diese konkrete Änderung. Wegen kleiner Stichprobe und möglicher Wechselwirkungen ist daraus keine kausale Aussage oder Parameterempfehlung abzuleiten.

## Fachliche Einordnung

Der kombinierte Layer zeigt, dass die Rolling-Schwäche nicht durch einen einzigen Volatilitätszustand erklärt wird. Marktstruktur differenziert die Ergebnisse zusätzlich, und die Wirkung verändert sich mit der Rolling-Geometrie.

Besonders auffällig ist die große Geometrie im high-volatility/trending-Regime mit 12,5 % positiven Destinationen, 0 % PF-Pass und einem Medianprofit von -22,88 EUR. Bei der Small-Geometrie ist dasselbe Regime dagegen 56,2 % positiv mit 56,2 % PF-Pass und +3,37 EUR Medianprofit. Das spricht gegen eine einfache, geometrieunabhängige Regel aus Volatilität und Trendstruktur.

Die Ergebnisse sind diagnostisch, nicht kausal. Die wiederholten Evaluationen über Selection-Profile sind keine unabhängigen Marktbeobachtungen. Es gibt keinen belastbaren Anlass, Parameterraum, Selection-Profile oder Gates zu verändern.

## Nächster Diagnose-Layer

Der sinnvollste nächste Schritt ist eine Asset-x-Regime-Interaktionsanalyse auf exakt demselben immutablem Artifact. Dabei soll geprüft werden, ob die beobachteten kombinierten Regimeeffekte hauptsächlich von SPY, QQQ oder IWM getragen werden. Auch dieser Layer bleibt rein diagnostisch und verändert keine Research-Entscheidungen.
