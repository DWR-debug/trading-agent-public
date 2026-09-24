# Trial 024 — Monthly Low-Volatility Cross-Sectional Control — Ergebnis — 2026-09-24

## Entscheidung

NO_SUPPORT / archived_rejected

Trial T-2026-09-24-024 wurde vollständig und reproduzierbar auf einem neuen,
vollständig symbol-disjunkten U.S.-Aktienuniversum ausgeführt. Präregistrierung,
Paper-only-Sicherheit, Disjointness, Datenintegrität und Ergebnisfingerprint
waren erfolgreich.

## Provenienz

- Workflow-Run: 36018203202
- Artifact-ID: 10814949024
- Artifact-Digest: sha256:a4a1a0bb5870b45859b22d72f2d13b8881106f7d88785d265172ad751736c134
- Report-Fingerprint: feb4376f1da051aa157efba098354ffce13ecc75969b4ded849dd90f8e9f1203
- Workflow-Code-SHA: feead383cde51b310a535cbeb439a616bf0ec246
- Branch-Head bei Research-Lauf: 59a67bc63033fe0ca938ec17069c3ac4d8c78225
- Manifest-Fingerprint: b8359acf7d532c6989dd41b31d6d8fdd836b3b1668c20b6fcadf3e2cfc0695da

## Daten

Universum:

INTC, QCOM, AVGO, HON, LMT, RTX, CSX, NSC

- 3.500 Candles je Asset
- 3.498 Point-in-Time-Returnperioden
- Research: 2.798
- Holdout: 700
- 3.501 gemeinsame Candles vor dem deterministischen Tail-Trim
- 3.502 Candles je Asset angefordert
- Timestamp-Intersection-Alignment: erfolgreich

## Präregistrierte Regel

Am Übergang eines Kalendermonats wird die Standardabweichung der unmittelbar
vor dem aktuellen Monat liegenden 252 abgeschlossenen Close-to-Close-Returns
berechnet. Die vier Assets mit der niedrigsten Volatilität erhalten je 25%
Long-Gewicht. Die vier höchsten bilden ausschließlich den deskriptiven
High-Vol-Control. Gross Exposure 1,0x, keine Hebelung, keine Short-Positionen.

Kosten: 10 bps Fee + 5 bps Slippage = 15 bps One-Way.
Zusätzlich 1,5x- und 2,0x-Kostenstress.

## Ergebnisse

| Kennzahl | Research | Holdout |
|---|---:|---:|
| Return | +146,08% | +46,03% |
| Max Drawdown | 42,53% | 18,54% |
| Profit Factor | 1,108 | 1,175 |
| OOS/Research-Return-Ratio | — | 0,315 |
| profitable Rolling-Fenster | 5/5 | — |

Kostenstress im Holdout:

- 1,5x: +45,81% Return, 18,54% Drawdown, PF 1,175
- 2,0x: +45,59% Return, 18,54% Drawdown, PF 1,174

Low-Vol minus High-Vol Edge:

- Research: -0,00031712 pro Tag ≈ -3,17 bps/Tag
- Holdout: -0,00103955 pro Tag ≈ -10,40 bps/Tag

Es gab 155 gültige Monatsselektionen und 12,0 Turnover-Einheiten im Basislauf.

## Gate-Befund

Bestanden:

- Research Return positiv
- Research Profit Factor >= 1,10
- profitable Research-Rolling-Fenster >= 50%
- OOS/Research-Return-Ratio >= 0,25
- Holdout Return positiv
- Holdout Profit Factor >= 1,10
- 1,5x-Kostenstress nichtnegativ
- 2x-Kostenstress nichtnegativ

Verfehlt:

- Research Drawdown <= 10%
- Holdout Drawdown <= 10%
- positiver Low-Vol-minus-High-Vol-Edge im Research
- positiver Low-Vol-minus-High-Vol-Edge im Holdout

## Methodische Konsequenz

Der Control zeigt eine positive Rendite- und PF-Serie sowie vollständige
Rolling-Research-Positivität. Die Kernhypothese als Charakteristik wird aber
nicht unterstützt: Der Low-Vol-Edge ist bereits im Research negativ und wird
im Holdout noch negativer. Zusätzlich bleiben die absoluten Drawdown-Grenzen
deutlich verfehlt.

Daraus folgt:

- keine Low-Vol-Lookback-Suche
- keine Auswahlbreiten-Suche
- keine alternative Volatilitätsdefinition
- keine Asset-Suche
- keine Kostenanpassung
- keine Produktionsintegration

## Safety

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- orders_enabled = False
- keine Live-Ausführung
- keine Research-Orders

Der Control wird nicht als Widerlegung der Literatur interpretiert; er liefert
ausschließlich Evidenz für die präregistrierte Implementierung und den geprüften
Datensatz.
