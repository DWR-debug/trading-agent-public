# Zeit-/Asset-Failure-Analyse — Rolling-WF

Stand: 2026-09-22

## Technischer Zustand

Die diagnostische Analyse ist erfolgreich abgeschlossen. Sie verwendet ausschließlich archivierte Research-Artefakte und führt selbst keine neuen Backtests oder Optimierungen aus.

- Rolling-Control Source Run: 35747170025
- Rolling-Control Diagnostic-Fingerprint: 06ba10b5fb540de887fd2494f8cc328fa849b8f80ac0a867b16386a73525e0e2
- Candidate-Migration Source Run: 35749957065
- Candidate-Migration Artifact-ID: 10704770495
- Candidate-Migration Analysis-Fingerprint: 171faa85316d7f9b5377263ea7058cdd30cc6c679626adf89d2e37b3978ad9
- Time/Asset Analysis Run: 35750002836
- Time/Asset Artifact-ID: 10704985412
- Time/Asset Analysis-Fingerprint: 274c5328ad89209121061890c670cafe131f7bf22715b50538c50e8afbb5038e
- 24 Evaluationen, 240 Rolling-Fenster
- vollständige Testsuite: grün
- Paper-Only-Safety: grün
- beide Cross-Workflow-Artefakte: erfolgreich geladen und per Fingerprint verifiziert

## Formale Rolling-Gate-Failures

| Kriterium | Evaluationen | Failures | Fail-Rate |
| --- | ---: | ---: | ---: |
| nonpositive_total_profit | 24 | 17 | 70,8 % |
| profit_factor | 24 | 21 | 87,5 % |
| profitable_window_ratio | 24 | 17 | 70,8 % |

Die drei Kriterien überlappen; die Failure-Zählungen sind daher nicht additiv.

## Zeitphasen

Die Fenster werden je Geometrie chronologisch in drei annähernd gleich große Abschnitte geteilt.

| Geometrie | Phase | Fenster | positive Quote | PF-Pass | Gesamtprofit EUR | Median Fensterprofit EUR |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| large | early | 24 | 54,2 % | 50,0 % | +170,28 | +2,11 |
| large | middle | 12 | 25,0 % | 8,3 % | -101,77 | -4,73 |
| large | recent | 24 | 25,0 % | 16,7 % | -328,88 | -6,12 |
| small | early | 60 | 28,3 % | 25,0 % | -309,00 | -3,18 |
| small | middle | 60 | 40,0 % | 40,0 % | +38,22 | -2,27 |
| small | recent | 60 | 43,3 % | 36,7 % | -186,87 | -2,63 |

Damit zeigt die Zeitzerlegung keine anhaltend positive Phase über beide Geometrien. Bei large liegt die beste lokale Phase am Anfang und kippt danach deutlich ins Negative. Bei small verbessert sich die positive Fensterquote im späteren Verlauf, während der aggregierte Profit und der Medianprofit weiterhin keine durchgehend positive Übertragung zeigen.

## Asset-spezifische Failure-Dichte

Je Asset liegen acht formale Evaluationen vor: zwei Geometrien × vier Selection-Profile.

| Asset | nonpositive_total_profit | profit_factor | profitable_window_ratio |
| --- | ---: | ---: | ---: |
| IWM | 8/8 | 8/8 | 6/8 |
| QQQ | 4/8 | 6/8 | 6/8 |
| SPY | 5/8 | 7/8 | 5/8 |

IWM zeigt damit im untersuchten Benchmark-Universum die höchste Häufung dieser drei formalen Rolling-Failures. Die Aussage bleibt auf diese drei konkret untersuchten Assets begrenzt und ist keine allgemeine Aussage über Assetklassen.

## Asset- und Zeitkontext

Besonders auffällig ist die große Geometrie:
- QQQ: 75,0 % positive Fenster in early, danach 0,0 % in middle und 12,5 % in recent.
- SPY: 62,5 % -> 25,0 % -> 12,5 %.
- IWM: 25,0 % -> 50,0 % -> 50,0 %; trotz dieser späteren positiven Fensterquoten bleibt der Gesamtprofit negativ.

Bei der kleinen Geometrie steigen die positiven Fensterquoten für QQQ und SPY bis in die aktuelle Phase, aber die aggregierten Phasenprofite bleiben für alle drei Assets in mindestens zwei Phasen negativ. Das zeigt eine zeitlich nicht stabile Übertragung statt eines einheitlichen globalen Zeitmusters.

## Kandidatenmigration im Zeitkontext

| Geometrie | Phase | Status | Fenster | positive Destination |
| --- | --- | --- | ---: | ---: |
| large | early | migration | 8 | 75,0 % |
| large | early | stable | 4 | 25,0 % |
| large | middle | migration | 6 | 50,0 % |
| large | middle | stable | 6 | 0,0 % |
| large | recent | migration | 18 | 27,8 % |
| large | recent | stable | 6 | 16,7 % |
| small | early | migration | 27 | 14,8 % |
| small | early | stable | 21 | 47,6 % |
| small | middle | migration | 38 | 42,1 % |
| small | middle | stable | 22 | 36,4 % |
| small | recent | migration | 22 | 45,5 % |
| small | recent | stable | 38 | 42,1 % |

Auch hier ist das Muster geometrieabhängig. Es gibt deshalb keinen stabilen allgemeinen Zusammenhang, nach dem Kandidatenmigrationen das Folgefenster systematisch verschlechtern oder verbessern.

## Parameterwechsel nach Phase

Die Parameterwechsel zeigen unterschiedliche lokale Muster. Mehrere Parameter können in derselben Transition gleichzeitig wechseln; die Gruppen sind daher überlappend.

Beispielsweise liegen in large/early die positiven Destination-Raten bei Änderungen von Momentum-lookback, Mean-Reversion-Window und Threshold jeweils hoch, während dieselben Strategieparameter in small/early deutlich niedrigere Raten aufweisen. In small/recent sind einzelne Parameterwechsel wieder mit höheren Destination-Raten verbunden.

Diese Unterschiede sind rein deskriptiv. Es gibt keine Grundlage, daraus einen Parameterwert als Ursache oder allgemeine Verbesserung abzuleiten.

## Fachliche Schlussfolgerung

Die zeit- und assetbezogene Diagnose schärft den bisherigen Befund:

1. Der Rolling-WF-Engpass konzentriert sich weiterhin stark auf Profit Factor, positive Gesamtprofitabilität und profitable-window-Ratio.
2. Die Failure-Dichte ist assetabhängig; IWM ist im aktuellen Benchmark stärker von den drei betrachteten formalen Failures betroffen als QQQ und SPY.
3. Die Zeitstruktur ist geometrieabhängig. Besonders die große Geometrie zeigt einen deutlichen Qualitätsabfall nach der frühen Phase.
4. Kandidatenmigrationen erklären den Engpass nicht durch einen einheitlichen Migration-vs.-Stabilität-Effekt.
5. Die Kombination aus Zeitphase, Asset und Kandidatenwechsel liefert damit eine plausible Ursachenstruktur für weitere Diagnostik, aber noch keine belastbare kausale Ursache.

Daher bleiben Parameterraum, Selection-Profile, Gate-Schwellen, Gebühren und Slippage unverändert. Als nächster diagnostischer Schritt ist die Prüfung sinnvoll, ob dieselben Failure-Muster an konkrete Marktregime-/Volatilitätszustände oder an bestimmte Strategieparameter-Kombinationen gekoppelt sind und ob dieses Muster über die drei Benchmark-Assets reproduziert wird.

Sicherheitszustand: Paper-Only True; Live-Trading False; Orders False.
