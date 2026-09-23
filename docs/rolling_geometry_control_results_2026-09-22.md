# Rolling-WF Zeitphasen- und Geometrie-Control — Ergebnisse

Stand: 2026-09-22

## Laufidentität
- Universum: benchmark — SPY, QQQ, IWM
- Research-Basis: 4.500 Candles je Asset
- Selection-Profile: score_max, boundary_averse, risk_averse, trade_rich
- Workflow Run: 35747170025
- Artifact-ID: 10703836878
- Code-Version: 62d91c0fa802e983e62879aa0bb7155202f8d7e0
- Diagnostic-Fingerprint: 06ba10b5fb540de887fd2494f8cc328fa849b8f80ac0a867b16386a73525e0e2
- Paper-Only: True
- Live-Trading: False
- Orders: deaktiviert

## Ergebnis
| Geometrie | Training | Test | Step | Fenster | Rolling-Gate |
| --- | ---: | ---: | ---: | ---: | ---: |
| Small | 1.125 | 225 | 225 | 15 | 1/12 |
| Large | 2.250 | 450 | 450 | 5 | 2/12 |

Die fünf Large-Testblöcke entsprechen exakt den Small-Fensterpaaren 6-7, 8-9, 10-11, 12-13 und 14-15. Der Vergleich hält damit den finalen Testbereich konstant, während die Rolling-Geometrie verändert wird.

## Zeitphasen
| Phase | Fenster | profitable Fenster | Quote | Gesamtprofit EUR | Median Fensterprofit EUR |
| --- | ---: | ---: | ---: | ---: | ---: |
| früh 1-5 | 60 | 17 | 28,3 % | -309,00 | -3,18 |
| Mitte 6-10 | 60 | 24 | 40,0 % | +38,22 | -2,26 |
| aktuell 11-15 | 60 | 26 | 43,3 % | -186,87 | -2,63 |

Über alle drei Phasen liegt der Median des Fensterprofits unter null. Die mittlere Phase ist aggregiert knapp positiv, reicht aber wegen des negativen Medians nicht als stabiler Profitabilitätsnachweis.

## Failure-Kriterien
| Geometrie | Profit Factor unter Minimum | Profitabilitätsquote unter Minimum | Gesamtprofit nicht positiv |
| --- | ---: | ---: | ---: |
| Small | 11/12 | 9/12 | 9/12 |
| Large | 10/12 | 8/12 | 8/12 |

## Kandidatenpersistenz
- Small-Geometrie: durchschnittlich 48,2 % gleiche Kandidaten in benachbarten Fenstern; Median 42,9 %; durchschnittlich 6,9 eindeutige Kandidaten je Asset/Profile.
- Large-Geometrie: durchschnittlich 33,3 % gleiche Kandidaten in benachbarten Fenstern; Median 25,0 %; durchschnittlich 3,25 eindeutige Kandidaten je Asset/Profile.

Die Kandidatenwahl ist im Rolling-WF absichtlich fensterspezifisch. Die Persistenzwerte sind daher diagnostisch und kein eigenständiges Gate.

## Einzelne Gate-Passes
- Small: QQQ / boundary_averse
- Large: SPY / boundary_averse und QQQ / risk_averse

Diese Einzelfälle werden nicht als Profilrangfolge interpretiert.

## Fachliche Schlussfolgerung
Die Erhöhung der Fensterzahl löst den Rolling-WF-Engpass nicht. Der Engpass hängt weiterhin stark mit Profit Factor, der Quote profitabler Fenster und dem positiven Gesamtprofit zusammen.

Die zeitliche Zerlegung zeigt keinen durchgehend positiven Abschnitt: Frühphase und aktuelle Phase sind aggregiert negativ; die mittlere Phase ist nur knapp positiv und besitzt weiterhin einen negativen Median je Fenster.

Der häufige Kandidatenwechsel liefert eine plausible diagnostische Spur für die nächste Analyse, beweist aber noch keine Ursache. Der nächste Schritt ist deshalb eine Kandidaten-Migrationsanalyse über aufeinanderfolgende Fenster: konkrete Parameterwechsel, begleitende Änderung der OOS-Metriken und gemeinsame Failure-Kriterien.

Strategie, Parameterraum, Selection-Profile und Gates bleiben bis zu dieser Analyse unverändert.