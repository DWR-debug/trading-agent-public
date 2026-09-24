# Ergebnis: Trial T-2026-09-24-027 — Fixed TSM Ensemble Trend Sleeve

## Status

**Entscheidung: NO_SUPPORT / archived_rejected**

Der präregistrierte Trial wurde vollständig auf `DWR-debug/trading-agent-public`
ausgeführt. Es wurde genau eine feste Intervention auf einem neuen,
vollständig symbol-disjunkten Validierungssatz geprüft. Es gab keine
Parameter-, Threshold-, Varianten- oder Holdout-Suche.

## Technischer Nachweis

- PR #132: gemerged
- Workflow-Run: `36029169717`
- Artifact-ID: `10820593251`
- Artifact-SHA256: `sha256:1320c20515be7d24e64f23d9af7090ab4c9f9bb53b6e17c16b924a84e878c247`
- Report-Fingerprint: `57b87f09de867cb2ef535aaf7e6132618d5e116ca36b04d9968cc8c5b327cf51`
- Manifest-Fingerprint: `c817bd74d4912316726dbc51347fe0dab22049acadd753bef0bdece89fe59748`
- Code-Commit: `169b239c188678c71d3d9bb9ae092e785832c72e`
- 13 neue vollständig symbol-disjunkte ETFs
- 3.500 Daily-Candles je Asset
- 3.498 gemeinsame Point-in-Time-Return-Perioden
- 2.798 Research / 700 blinder Holdout
- vollständige Vorprüfungen und Ergebnisintegrität: grün
- keine Orders

## Einzige Intervention

Der Fixed Candidate blieb ansonsten unverändert:

- 50 % SMA 50/200 inverse-volatility Trend-Sleeve;
- 50 % 12-1 Cross-Sectional Momentum Top-2;
- bestehendes 63-Session-/10%-Volatilitätsbudget;
- gleiche Point-in-Time-Ausführung;
- gleiche Gebühren und Slippage.

Nur das Trend-Signal wurde ersetzt durch:

- feste TSM-Mehrheitsentscheidung über 63, 126 und 252 Sessions;
- mindestens zwei positive Horizonte -> Long;
- sonst Flat;
- keine Shorts und kein Hebel;
- monatliche Reallokation;
- 60-Sessionen Volatilitätsgewichtung und 25%-Asset-Cap.

## Base-Szenario

| Kennzahl | Fixed Candidate | TSM Challenger |
|---|---:|---:|
| Research Return | +57,55 % | +56,76 % |
| Research Max DD | 16,34 % | 16,52 % |
| Research PF | 1,096 | 1,096 |
| Profitable Rolling-Fenster | 4/5 | 4/5 |
| Rolling PF | 1,096 | 1,096 |
| Ø Rolling DD | 12,82 % | 13,32 % |
| OOS/IS Return Ratio | 0,461 | 0,521 |
| Holdout Return | +26,55 % | +29,57 % |
| Holdout Max DD | 13,45 % | 10,66 % |
| Holdout PF | 1,164 | 1,182 |

Der Challenger verbessert damit die Holdout-Rendite, den Holdout-PF, den
Holdout-Drawdown und das OOS/IS-Verhältnis. Gleichzeitig verfehlt er die
unveränderten Research-Risiko-/PF-Schwellen und ist beim Research-Return,
Research-Drawdown und durchschnittlichen Rolling-Drawdown schlechter.

## Präregistrierte Gates

Absolute Kriterien:

- Research-Return: PASS
- Research-Drawdown: FAIL
- Research-PF: FAIL
- Rolling-PF: FAIL
- profitable Rolling-Fensterquote: PASS
- durchschnittlicher Rolling-Drawdown: FAIL
- OOS/IS: PASS
- Holdout positiv: PASS
- Holdout-PF: PASS
- Holdout-Drawdown: FAIL
- 1,5x-Kostenstress: PASS
- 2x-Kostenstress: PASS
- Total-Return-Sensitivität: PASS

Nicht-Verschlechterungsvertrag gegenüber dem festen Kandidaten:

- Research-Return: FAIL
- Research-Drawdown: FAIL
- Research-PF: PASS
- Rolling-PF: PASS
- profitable Rolling-Fensterquote: PASS
- durchschnittlicher Rolling-Drawdown: FAIL
- OOS/IS: PASS
- Holdout-Return: PASS
- Holdout-PF: PASS
- Holdout-Drawdown: PASS

Formaler Status: **BLOCKED / NO_SUPPORT**.

## Bedeutung

Der Trial liefert positive zusätzliche Holdout-Evidenz für die feste
63/126/252-TSM-Familie, aber nicht für eine Promotion des bestehenden
Kandidaten. Insbesondere bleibt die Research-Risikostruktur oberhalb der
unveränderten Schwellen.

Die positive Holdout-Seite darf deshalb nicht rückwirkend zur Auswahl oder
Nachoptimierung benutzt werden.

## Konsequenz

- keine TSM-Lookback-Suche;
- keine Änderung der TSM-Definition;
- keine Gewichtsanpassung;
- keine Gate-Lockerung;
- keine Produktionsintegration;
- keine Echtgeldfreigabe;
- keine Orders.

Trial 027 wird als negative/inkonklusive Evidenz gegen die konkrete
Trend-Sleeve-Ersetzung archiviert.

## Sicherheitsstatus

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`

Keine Live-Ausführung.
