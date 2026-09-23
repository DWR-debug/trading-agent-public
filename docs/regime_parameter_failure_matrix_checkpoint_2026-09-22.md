# Regime × Parameterstruktur × Failure-Matrix — Checkpoint 2026-09-22

## Laufidentität

- Repository: `DWR-debug/trading-agent`
- PR: #82
- Merge-Commit: `dea1aa81225b12d76abef36c2c1884dacdc27ecd`
- Workflow Run: 35762937300
- Artifact ID: 10711386089
- Artifact-Digest: `sha256:6adc88933045043b5563eb8cd87809524c4ed8b9d165cb5949b8c3e65f98f2ea`
- Analysis-Fingerprint: `9aa88bf691bfcfc94b5e4de5cbabae950a606af1d7a80645e61b3ab8be960f2f`
- Source Rolling-Control Run: 35750723097
- Source Rolling-Control Fingerprint: `4fbd29349792371765c43fb25dc8264bdf035ee05eaa76f1b215f9e0d9ba85af`
- Research-Basis: Benchmark, 5.000 Candles je Asset, 4.500 Research-Candles
- Eindeutige Rolling-Testfenster: 60

## Umfang

- Evaluation-Kontexte: 24
- Fensterzeilen: 240
- eindeutige Kandidatenstrukturen: 70
- wiederkehrende vollständige Kandidatenstrukturen: 35

Verbundene Dimensionen:

`Asset × Geometrie × Selection-Profil × ex-ante Volatilitätsregime × ex-ante Strukturregime × Zeitphase × Kandidatenstruktur × Outcome/Fallkriterium`

Untersuchte Kandidatenparameter:

- `momentum.lookback`
- `mean_reversion.window`
- `mean_reversion.threshold`
- `risk_per_trade`
- `leverage`

## Formale Failure-Kriterien

| Kriterium | Anzahl betroffener Evaluation-Kontexte |
| --- | ---: |
| `profit_factor` | 21 |
| `nonpositive_total_profit` | 17 |
| `profitable_window_ratio` | 17 |
| `drawdown_limit` | 0 |
| `insufficient_total_trades` | 0 |
| `zero_trade_window_ratio` | 0 |

Die Failure-Kriterien bleiben formal auf Evaluationsebene. Fensterwerte wie Profit, Profit Factor, Drawdown und Trade Count dienen der deskriptiven Kontextualisierung und werden nicht nachträglich zu formalen Einzel-Fenster-Failures umdeklariert.

## Zentrale Befunde

### Wiederkehrende Kandidatenstrukturen

35 von 70 eindeutigen Kandidatenstrukturen wiederholen sich mindestens zweimal.

- 31/35 wiederkehrende Strukturen sind profilintern.
- 4/35 werden von zwei Selection-Profilen geteilt.
- Keine wiederkehrende Struktur wird von mehr als zwei Profilen geteilt.
- 6/35 wiederkehrende Strukturen kommen über alle drei Benchmark-Assets vor, überwiegend innerhalb eines einzelnen Profils.

Eine besonders häufige `trade_rich`-Struktur tritt 39-mal auf und zeigt 17,9 % positive Fenster, 15,4 % PF-Pass und einen Medianprofit von -6,10 EUR.

Eine zwischen `risk_averse` und `score_max` geteilte Struktur tritt 7-mal auf und zeigt 57,1 % positive Fenster sowie 57,1 % PF-Pass. Drei von vier zugehörigen Evaluation-Kontexten scheiterten dennoch an `profitable_window_ratio`.

Das illustriert die notwendige Trennung zwischen Fenster-Outcomes und formalen Rolling-Gates.

### Interpretation

Die wiederkehrenden Kandidaten sind nicht homogen genug, um allein daraus eine globale Parameteränderung abzuleiten. Ein einzelner Parameterwert ist außerdem über Selection-Profil, Asset, Geometrie und Marktphase konfundiert.

Die Matrix bestätigt daher keinen universellen „schlechten Parameter“. Sie zeigt vielmehr, dass Kandidatenstruktur und Selection-Kontext gemeinsam betrachtet werden müssen.

## Methodische Grenzen

- Regimekennzahlen sind ex ante relativ zum jeweiligen Teststart.
- Es wurden keine neuen Marktdaten geladen.
- Es wurden keine neuen Backtests oder Optimierungen ausgeführt.
- Es wurde keine Selection-Regel verändert.
- Der Parameterraum wurde nicht verändert.
- Formale Gates wurden nicht verändert.
- Die Analyse ist deskriptiv, nicht kausal.
- Wiederholte Selection-Profile teilen dieselben Marktfenster und sind daher keine unabhängigen Marktbeobachtungen.

## Entscheidung für die nächste Stufe

Die aktuelle Evidenz rechtfertigt keinen globalen Eingriff.

Der nächste diagnostische Schritt ist eine streng geschichtete Hypothesenbildung innerhalb der tatsächlich wiederkehrenden Profile/Assets/Geometrien. Erst bei Reproduzierbarkeit über mehrere unabhängige Marktfenster und Kontexte wird eine einzelne Änderungshypothese isoliert getestet.

## Sicherheit

- Paper-Only: True
- Live-Trading: False
- Orders: False

Das 30-Tage-GitHub-Artifact bleibt die kurzfristige Laufablage. Dieser Checkpoint ist die dauerhafte, commit-basierte Zusammenfassung der Provenienz und der wichtigsten Befunde.
