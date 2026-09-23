# Long-Horizon-Control — Benchmark 5.000 vs. 2.500 Daily-Candles — 2026-09-22

## Zweck

Kontrollierte Prüfung, ob die Verlängerung der gemeinsamen Benchmark-Historie von 2.500 auf 5.000 Daily-Candles die diagnostisch beobachteten OOS-/Generalisierungsmuster verändert.

Unverändert blieben:
- Benchmark-Universum: SPY, QQQ, IWM
- vier Selection-Profile
- 1.280 Kandidaten im Parameterraum
- Optimizer-Top-N = 5
- Train-/WFO-/Rolling-WF-Protokoll
- Holdout-Verhältnis = 10 %
- Gebühren = 0,1 %
- Slippage = 0,05 %
- alle sieben Research-Gates und ihre Schwellenwerte
- Paper-Only-Sicherheitszustand

Der Lauf ist damit als separater Horizon-Control-Checkpoint und nicht als Parameter-/Gate-Experiment zu interpretieren.

## Reproduzierbare Laufidentität

### 5.000-Candle-Control
- GitHub Actions Run: `35742631852`
- Commit: `3ce7b4ecc71f410c2092fe5dff5cf5451a224280`
- Experiment-Fingerprint: `3ee18c1ed7c1e067a683230cd69f56cdf36ea4f74227a267d85d1d03c19ddd0f`
- Artifact-ID: `10699853862`
- Evidenzfamilie: 4 Reports, 12 Dataset-Auswertungen
- gemeinsame Datenbasis: 5.000 Candles je Asset
- Research-Abschnitt: 4.500 Candles
- Holdout: 500 Candles
- Datenbereich: 2006-11-02 bis 2026-09-21
- Paper-Only: `True`
- Live-Trading: `False`
- Orders: deaktiviert

### Vergleichslauf 2.500
- GitHub Actions Run: `35731263325`
- Artifact-ID: `10695925573`
- Evidenzfamilie: 4 Reports, 12 Dataset-Auswertungen
- gemeinsame Datenbasis: 2.500 Candles je Asset
- gemäß identischem 10-%-Holdout-Protokoll entsprechend kürzerer Research-/Holdout-Abschnitt

## Gate-Matrix

| Gate | 2.500 | 5.000 | Veränderung |
| --- | ---: | ---: | ---: |
| data_quality | 12/12 | 12/12 | unverändert |
| backtest (baseline_sanity) | 4/12 | 0/12 | längere Historie deckt mehr Drawdown-Verletzungen auf |
| walk_forward | 1/12 | 5/12 | +4 |
| rolling_walk_forward | 0/12 | 2/12 | +2 |
| robustness | 2/12 | 5/12 | +3 |
| overfit | 1/12 | 4/12 | +3 |
| holdout | 2/12 | 6/12 | +4 |

Alle 12 Datensätze des 5.000-Candle-Laufs bleiben formal `BLOCKED`, weil das `backtest`-Gate als Baseline-Sanity-Gate in allen 12 Fällen am maximalen Drawdown von 10 % scheitert. Dieses Gate ist selection-profilunabhängig.

Wichtig ist daher die getrennte Betrachtung der kandidatenbezogenen OOS-Gates: mehrere dieser Gates zeigen gegenüber 2.500 Candles deutlich mehr bestandene Auswertungen.

## Zentrale diagnostische Befunde

### Walk-Forward

Die Anzahl bestandener WFO-Auswertungen steigt von 1/12 auf 5/12.

Im 5.000-Candle-Lauf bestehen:
- boundary_averse: 1/3
- risk_averse: 2/3
- score_max: 2/3
- trade_rich: 0/3

Diese Zahlen sind deskriptiv und keine Profilrangfolge.

Einzelne Beispiele zeigen die stärkere OOS-Evidenz bei längerem Horizont:
- SPY / boundary_averse: WFO-OOS-Profit ca. 63,5 EUR, PF ca. 1,92
- QQQ / risk_averse: WFO-OOS-Profit ca. 43,1 EUR, PF ca. 1,75
- QQQ / score_max: WFO-OOS-Profit ca. 179,9 EUR, PF ca. 1,66

### Rolling Walk-Forward

Die Zahl bestandener Rolling-WF-Gates steigt von 0/12 auf 2/12.

Positiv profitable Fenster nehmen von 19/60 auf 22/60 zu, also von 31,7 % auf 36,7 %.

Der Rolling-WF-Gesamtbefund bleibt jedoch weiterhin ein Hauptengpass: Über die 12 Auswertungen hinweg bleiben die Ergebnisse heterogen und mehrere Datensätze verfehlen Profit-Factor-, Gesamtprofit- oder Fensterquoten-Anforderungen.

Die beiden bestandenen Rolling-WF-Auswertungen im 5.000-Candle-Lauf sind:
- SPY / boundary_averse
- QQQ / risk_averse

### Robustness

Die Passrate steigt von 2/12 auf 5/12.

Damit werden unter dem unveränderten Stress-Test mehrere ausgewählte Kandidaten robuster als im 2.500-Candle-Kontrolllauf, ohne dass daraus eine allgemeine Strategieeigenschaft abgeleitet werden kann.

### Overfit

Die Passrate steigt von 1/12 auf 4/12.

Das ist besonders relevant, weil die bisherige familienweite Diagnose das OOS-/IS-Verhältnis als häufigsten Failure-Befund identifiziert hatte. Der längere Horizont reduziert diesen Failure-Anteil sichtbar, beseitigt ihn aber nicht.

### Holdout

Die Passrate steigt von 2/12 auf 6/12.

Der Holdout bleibt strikt vom Research-Abschnitt getrennt. Für einzelne Dataset/Profile-Kombinationen ist die finale 500-Candle-Holdout-Prüfung positiv, während andere Kombinationen weiterhin scheitern.

### Kandidatendynamik

Die längere Historie verändert nicht nur Metriken, sondern auch die zeitabhängige Kandidatenauswahl.

Übereinstimmung des Rolling-Kandidaten mit dem festen WFO-Kandidaten:

| Profil | 2.500 | 5.000 |
| --- | ---: | ---: |
| score_max | 66,7 % | 26,7 % |
| boundary_averse | 73,3 % | 40,0 % |
| risk_averse | 66,7 % | 26,7 % |
| trade_rich | 60,0 % | 86,7 % |

Damit zeigt der Horizon-Control-Lauf, dass die verlängerte Historie die Optimierungs-/Kandidatenstruktur selbst beeinflusst. Der Effekt ist profilabhängig und wird nicht als Ranking interpretiert.

## Asset-Struktur

Der 5.000-Candle-Lauf zeigt weiterhin deutliche Asset-Heterogenität:

- SPY erhält mehrere bestandene kandidatenbezogene OOS-Gates, darunter einen bestandenen Rolling-WF-Fall.
- QQQ zeigt ebenfalls mehrere bestandene WFO-, Robustness-, Overfit- und Holdout-Gates und einen bestandenen Rolling-WF-Fall.
- IWM besteht im 5.000-Candle-Lauf zwar das Holdout-Gate für alle vier Profile, bleibt aber bei WFO, Rolling-WF, Robustness und Overfit durchgehend blockiert.

Damit bestätigt sich erneut, dass der Generalisierungsbefund nicht allein durch die Selection-Regel erklärt wird; Asset-spezifische Unterschiede bleiben bestehen.

## Fachliches Fazit

Der Long-Horizon-Control liefert einen klaren diagnostischen Befund:

1. Eine Verdopplung der historischen Datenbasis verändert die Evidenzlage messbar.
2. Mehrere kandidatenbezogene OOS-Gates bestehen deutlich häufiger als im 2.500-Candle-Kontrolllauf.
3. Die Rolling-WF-Anforderung bleibt trotz Verbesserung ein zentraler Engpass.
4. Das Baseline-Drawdown-Gate wird durch die längere Historie strenger sichtbar und blockiert deshalb weiterhin die formale Gesamtfreigabe.
5. Die Kandidatenauswahl wird bei mehreren Profilen zeitabhängiger; dies ist mit einer längeren Historie vereinbar, aber kein Ursachenbeweis.
6. Die Daten liefern damit noch keine belastbare Grundlage für eine Änderung des Parameterraums, der Selection-Profile oder der Gates.

Der nächste Research-Schritt sollte deshalb nicht unmittelbar die Parameteroptimierung verändern, sondern die durch den Horizon-Control neu sichtbaren Muster gezielt auseinandernehmen: Welche Änderungen stammen aus zusätzlicher Trainingshistorie, welche aus der erweiterten Holdout-Stichprobe, und welche Failure-Kriterien bleiben über beide Horizonte invariant?

## Sicherheitszustand

Der gesamte Lauf wurde ausschließlich im Paper-/Simulationsmodus ausgeführt:
- `paper_only = True`
- `live_trading_enabled = False`
- `orders_enabled = False`

Keine Orderausführung.

