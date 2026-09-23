# Kandidaten-Migrationsanalyse — Rolling-WF

Stand: 2026-09-22

Die Analyse verwendet ausschließlich den archivierten Rolling-Geometrie-Control-Report aus Run 35747170025. Es wurden keine neuen Backtests oder Optimierungen ausgeführt.

## Technischer Zustand

- PR #65: gemerged
- Merge-Commit: 45ac4ca0cc075c81683264840235047f46edb9e9
- Source-Code-Version: 62d91c0fa802e983e62879aa0bb7155202f8d7e0
- Source-Diagnostic-Fingerprint: 06ba10b5fb540de887fd2494f8cc328fa849b8f80ac0a867b16386a73525e0e2
- Analysis-Fingerprint: 171faa85316d7f9b5377263ea7058cdd30cc6c679626adf89d2e37b3978ad9
- Transitions: 216
- Migrationen: 119
- stabile Transitionen: 97
- Migrationsrate: 55,1 %
- Paper-Only: True
- Live-Trading: False
- Orders: False

## Gesamtvergleich

| Gruppe | Transitions | positive Destination | PF >= 1,10 | DD <= 10 % | Median Profit EUR |
| --- | ---: | ---: | ---: | ---: | ---: |
| migration | 119 | 37,0 % | 32,8 % | 94,1 % | -1,67 |
| stable | 97 | 37,1 % | 30,9 % | 97,9 % | -3,06 |

Auf Gesamtebene unterscheiden sich die Migrations- und stabilen Transitionen bei der positiven Destination-Rate praktisch nicht. Die PF-Passrate ist bei Migrationen etwas höher, der Median-Destination-Profit weniger negativ. Der Befund allein belegt keinen ursächlichen Zusammenhang.

## Geometrien

| Geometrie | Gruppe | Transitions | positive Destination | PF >= 1,10 | Median Profit EUR |
| --- | --- | ---: | ---: | ---: | ---: |
| small | migration | 87 | 34,5 % | 33,3 % | -2,52 |
| small | stable | 81 | 42,0 % | 35,8 % | -2,39 |
| large | migration | 32 | 43,8 % | 31,2 % | -1,09 |
| large | stable | 16 | 12,5 % | 6,3 % | -9,46 |

Der Unterschied zwischen Migration und Stabilität ist geometrieabhängig. Bei der Small-Geometrie sind stabile Transitionen bei positiver Destination häufiger; bei der Large-Geometrie ist die positive Destination-Rate bei Migrationen höher. Wegen der unterschiedlichen Stichprobengrößen und der explorativen Anlage wird daraus keine allgemeine Regel abgeleitet.

## Parameter-Assoziationen

Über alle 216 Transitionen:

| Parameter | Änderung Count | positive Destination bei Änderung | positive Destination ohne Änderung | PF-Pass bei Änderung | PF-Pass ohne Änderung |
| --- | ---: | ---: | ---: | ---: | ---: |
| risk_per_trade | 22 | 54,5 % | 35,1 % | 50,0 % | 29,9 % |
| leverage | 0 | — | 37,0 % | — | 31,9 % |
| momentum.lookback | 76 | 32,9 % | 39,3 % | 31,6 % | 32,1 % |
| mean_reversion.window | 75 | 32,0 % | 39,7 % | 26,7 % | 34,8 % |
| mean_reversion.threshold | 62 | 40,3 % | 35,7 % | 38,7 % | 29,2 % |

Die Counts sind unterschiedlich groß. Besonders bei `risk_per_trade` ist die Gesamtzahl der Änderungen klein; deshalb ist die beobachtete Differenz nicht als robuste Parameteraussage zu behandeln.

## Häufigste Migrationskombinationen

- `mean_reversion.threshold + mean_reversion.window + momentum.lookback`: 28
- `mean_reversion.window + momentum.lookback`: 19
- `mean_reversion.threshold + momentum.lookback`: 12
- `risk_per_trade` allein: 11
- `momentum.lookback` allein: 11
- `mean_reversion.threshold + mean_reversion.window`: 11

Leverage wechselte in keiner Transition.

## Fachliche Interpretation

Die Analyse bestätigt zunächst die bereits sichtbare Kandidatendynamik: Zwischen aufeinanderfolgenden Rolling-Fenstern wechseln die ausgewählten Kandidaten in 119 von 216 Transitionen.

Der Gesamtvergleich zeigt jedoch keinen starken, einheitlichen Unterschied zwischen Migration und Stabilität. Die Folgefenster bleiben in beiden Gruppen häufig unter den lokalen Profitabilitäts- und Profit-Factor-Anforderungen; der Median-Destination-Profit ist in beiden Gruppen negativ.

Die Parametervergleiche sind ebenfalls deskriptiv. Sie zeigen einzelne Zusammenhänge, aber keine belastbare Grundlage für eine Änderung des Parameterraums. Insbesondere lässt sich aus diesen Transitionen nicht ableiten, dass ein bestimmter Parameterwechsel die nachfolgende OOS-Qualität verursacht oder verbessert.

Die Destination-Flags sind bewusst Fensterdiagnostik. Sie sind nicht identisch mit den formalen Rolling-Gate-Kriterien, die auf den gesamten Rolling-Satz angewendet werden.

## Konsequenz für die nächste Research-Stufe

PR #65 liefert damit den geplanten diagnostischen Nachweis der Kandidatenmigration, ohne selbst neue Research-Ergebnisse zu erzeugen. Der verbleibende Rolling-WF-Engpass lässt sich nicht durch einen einfachen „Migration schlecht / Stabilität gut“-Mechanismus erklären.

Die nächste sinnvolle Prüfung ist daher eine zeitlich und assetbezogen konditionierte Failure-Analyse: Welche konkreten Rolling-Failure-Kriterien häufen sich in bestimmten Zeitphasen und Asset-Typen, und ob dieselben Failure-Muster über verschiedene Kandidatenwechsel hinweg wiederkehren. Parameterraum, Selection-Profile und Gate-Schwellen bleiben bis zu belastbarer Gegen-Evidenz unverändert.

Sicherheitszustand: Paper-Only True; Live-Trading False; Orders False.
