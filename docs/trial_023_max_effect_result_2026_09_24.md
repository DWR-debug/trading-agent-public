# Trial 023 — MAX-Effect Cross-Sectional Control — Ergebnis — 2026-09-24

## Entscheidung

**NO_SUPPORT / archived_rejected**

Trial T-2026-09-24-023 wurde vollständig und reproduzierbar ausgeführt. Die
Forschung wurde auf einem neuen, vollständig symbol-disjunkten U.S.-Aktien-
Universum durchgeführt. Präregistrierung, Paper-only-Sicherheit,
Daten-/Kalenderintegrität und Ergebnisfingerprint waren erfolgreich.

## Provenienz

- Workflow-Run: 36016871406
- Artifact-ID: 10815121247
- Artifact-Digest: sha256:58bfcf5d3ee264df34ebb99dd6322fcb5f24c2ec9169d455b1068488da9e71c5
- Report-Fingerprint: bfaeb216996b2f32acd55fff06e217344f24de6aca373a661bedd873c06bb594
- Workflow-Code-SHA: 3b05c02c16901329112814bdb1c7d3486df88fff
- Research-Branch-Head vor Merge: dfd29f361b91f41316313f2b75fe42f3c013a4b3
- Manifest-Fingerprint: 66a17c515f85af51cfbd6d4402fc67c9d2c6cbb215eefdfe459052e2d5618d6b

## Daten

Universum:

ORCL, CSCO, TXN, ADP, UPS, ABT, GILD, AMGN

- 3.500 Candles je Asset
- 3.498 Point-in-Time-Returnperioden
- Research: 2.798
- Holdout: 700
- 3.501 gemeinsame Candles vor dem deterministischen Tail-Trim
- 3.502 Candles je Asset wurden für die Akquisition angefordert
- Timestamp-Intersection-Alignment: erfolgreich

## Präregistrierte Regel

Der MAX ist der maximale positive Close-to-Close-Tagesreturn innerhalb des
unmittelbar vorangegangenen vollständig abgeschlossenen Kalendermonats.

Im Folgemonat werden die vier Assets mit dem niedrigsten MAX mit jeweils 25%
Long gehalten. Gross Exposure 1,0x; keine Short-Positionen; keine Hebelsuche.

Kosten: 10 bps Fee + 5 bps Slippage = 15 bps One-Way.
Zusätzlich wurden 1,5x- und 2,0x-Kostenstress berechnet.

Es gab genau eine Strategievariante; keine Parameter-, Threshold- oder
Asset-Suche und keine Holdout-Selektion.

## Ergebnisse

| Kennzahl | Research | Holdout |
|---|---:|---:|
| Return | +285,84% | +38,85% |
| Max Drawdown | 24,63% | 16,26% |
| Profit Factor | 1,148 | 1,144 |
| OOS/Research-Return-Ratio | — | 0,136 |
| profitable Rolling-Fenster | 4/5 | — |

Kostenstress im Holdout:

- 1,5x: +35,80% Return, 16,32% Drawdown, PF 1,135
- 2,0x: +32,82% Return, 16,39% Drawdown, PF 1,125

MAX-Edge (Low-MAX minus High-MAX):

- Research: +0,00014368 pro Tag ≈ +1,44 bps/Tag
- Holdout: -0,00004064 pro Tag ≈ -0,41 bps/Tag

## Gate-Befund

Bestanden:

- Research Return positiv
- Research Profit Factor >= 1,10
- profitable Rolling-Fenster >= 50%
- Holdout Return positiv
- Holdout Profit Factor >= 1,10
- 1,5x-Kostenstress nichtnegativ
- 2,0x-Kostenstress nichtnegativ
- positiver MAX-Edge im Research

Verfehlt:

- Research Drawdown <= 10%
- OOS/Research-Return-Ratio >= 0,25
- Holdout Drawdown <= 10%
- positiver MAX-Edge im Holdout

## Methodische Konsequenz

Der Research-Befund ist positiv, aber nicht robust über den Holdout:

- Der Low-MAX-Edge dreht sein Vorzeichen von positiv im Research zu negativ im
  Holdout.
- Die absoluten Drawdown-Grenzen werden in beiden Splits verfehlt.
- Die Out-of-Sample-/Research-Ratio liegt mit 0,136 deutlich unter 0,25.

Damit wird der Control nicht integriert.

Es erfolgt kein Tuning von Auswahlbreite, MAX-Fenster, Rebalance-Regel,
Thresholds, Kostenannahmen oder Asset-Universen auf Basis des Holdouts.

Die Literatur wird durch diesen einzelnen negativen Control weder bestätigt noch
widerlegt; der Versuch liefert ausschließlich Evidenz für die präregistrierte
Implementierung im geprüften Datensatz.

## Safety

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- orders_enabled = False
- keine Live-Ausführung
- keine Research-Orders
