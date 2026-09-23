# Rolling-WF Regime-/Volatilitäts-Checkpoint — 2026-09-22

## Laufidentität

- Rolling-Control Workflow Run: 35750723097
- Rolling-Control Artifact: 10704817758
- Rolling-Control Diagnostic-Fingerprint: 4fbd29349792371765c43fb25dc8264bdf035ee05eaa76f1b215f9e0d9ba85af
- Rohdaten-Manifest-Fingerprint: 1149670a252bbf7989c5dbd71bfbb0cffcd7f0ed028bf59f348295a02ea51d24
- Regime-/Volatilitätsanalyse Workflow Run: 35753219417
- Analyse-Artifact: 10706287550
- Analyse-Fingerprint: 95f7b843b3be5588a721d0f4e4877968526c489ea3e82d88801a66c931040836
- Research-Basis: 4.500 Candles aus einem archivierten 5.000-Candle-Datensatz
- Universe: benchmark — SPY, QQQ, IWM
- Quelle: exakt archivierte Yahoo-Chart-Datasets

## Reproduzierbarkeit

Das Rolling-Control-Artifact enthält die drei Rohdaten-CSV-Dateien vollständig. Vor der Diagnose wurden Byte-SHA-256, Full-Dataset-Fingerprint, Research-Fingerprint, Candle-Anzahl und Manifest-Fingerprint geprüft.

Die Regimeanalyse führt keine neuen Daten-Downloads, Backtests oder Optimierungen aus. Strategie, Parameterraum und Gates bleiben unverändert. Paper-Only ist aktiv; Live-Trading und Orders sind deaktiviert.

## Volatilitätsmethode

Für jedes Rolling-Testfenster wird die ex-ante Volatilität aus den 20 davorliegenden Log-Close-Returns bestimmt. Der Regime-Status wird relativ zur historischen Verteilung berechnet, die ausschließlich Daten vor dem jeweiligen Teststart verwendet:

- low: unter dem 33%-Perzentil
- middle: 33% bis 67%
- high: über dem 67%-Perzentil

Zusätzlich wird die realisierte annualisierte Volatilität innerhalb des Testfensters berechnet.

## Ergebnisse

### Small-Geometrie

| Ex-ante Regime | Marktfenster | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |
| --- | ---: | ---: | ---: | ---: | ---: |
| low | 24 | 96 | 30,2 % | 28,1 % | -2,75 |
| middle | 11 | 44 | 43,2 % | 43,2 % | -2,08 |
| high | 10 | 40 | 47,5 % | 37,5 % | -3,82 |

Die small-Geometrie zeigt damit keinen monotonen Zusammenhang zwischen Volatilitätsregime und Rolling-Performance. Die high-Gruppe hat zwar mehr positive Fenster, aber weiterhin einen niedrigen PF-Pass und den schlechtesten Medianprofit.

### Large-Geometrie

| Ex-ante Regime | Marktfenster | Evaluationen | positive Ergebnisse | PF-Pass | Median Profit EUR |
| --- | ---: | ---: | ---: | ---: | ---: |
| low | 3 | 12 | 58,3 % | 50,0 % | +2,11 |
| middle | 6 | 24 | 25,0 % | 16,7 % | -3,75 |
| high | 6 | 24 | 37,5 % | 29,2 % | -2,29 |

Der low-Regime-Befund der large-Geometrie basiert nur auf drei Marktfenstern und ist deshalb ein schwacher Evidenzpunkt.

## Kandidatenmigration und Volatilitätswechsel

Über alle Geometrien und Selection-Profile hinweg wurden 216 benachbarte Übergänge ausgewertet:

- Migrationen: 119 / 216 = 55,1 %
- stabile Kandidaten: 97 / 216 = 44,9 %

Bei einer Expansion des ex-ante Volatilitäts-Perzentils um mehr als 10 Prozentpunkte lag die Migrationsrate bei 59,3 %. Bei einer entsprechenden Kontraktion lag sie bei 50,0 %.

Für die expanding-Gruppe lag der PF-Pass der Destinationen bei 29,6 % und der Medianprofit bei -3,41 EUR. Bei contracting lag der PF-Pass bei 35,9 % und der Medianprofit bei -0,98 EUR.

Damit gibt es eine diagnostische Spur, dass stärkere Volatilitätsveränderungen mit häufigeren Kandidatenwechseln einhergehen. Ein konsistenter Performancevorteil nach solchen Wechseln ist jedoch nicht sichtbar.

## Parameterbezogene Spur

Die häufigen Änderungen konzentrieren sich weiterhin auf:

- momentum.lookback: 76 Wechsel
- mean_reversion.window: 75 Wechsel
- mean_reversion.threshold: 62 Wechsel

Bei Änderungen dieser drei Parameter lag das Median-Delta des Volatilitäts-Perzentils jeweils ungefähr bei +0,11 bis +0,12, gegenüber ungefähr +0,07 bei Übergängen ohne diese konkrete Änderung.

Das ist mit einer stärkeren Anpassung der Kandidaten an veränderte Volatilitätsbedingungen vereinbar, beweist aber keine Ursache.

## Fachliche Schlussfolgerung

Die Volatilitätsanalyse erklärt den Rolling-WF-Engpass nicht allein. Es gibt Unterschiede zwischen Regimen, aber weder eine stabile monotone Beziehung noch ein Muster, das eine Änderung von Parameterraum, Selection-Profile oder Gates rechtfertigt.

Der diagnostisch nächste sinnvolle Layer ist deshalb eine **kombinierte Marktregimeanalyse aus Volatilität und Trend/Choppiness**, weil die bisherige Evidenz eher auf unterschiedliche Marktstrukturen als auf einen reinen Volatilitätsengpass hindeutet.

Auch dieser nächste Layer sollte ausschließlich auf dem unveränderten, bereits archivierten Datensatz arbeiten.
