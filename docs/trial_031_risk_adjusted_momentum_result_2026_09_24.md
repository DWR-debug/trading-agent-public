# Ergebnis: Trial T-2026-09-24-031 — Risk-Adjusted Cross-Sectional Momentum

## Status

**NO_SUPPORT / archived_rejected**

Der präregistrierte Trial wurde vollständig auf `DWR-debug/trading-agent-public`
ausgeführt. Es wurde genau eine feste Signalintervention auf einem neuen,
vollständig symbol-disjunkten Validierungssatz geprüft. Keine Parameter-,
Threshold-, Varianten- oder Holdout-Suche.

## Technischer Nachweis

- PR #142
- Workflow-Run: `36043071782`
- Artifact-ID: `10826903506`
- Artifact-SHA256: `sha256:9b42882a4ee9082c2b6194f4b671513b7da50685d850bac561aaa3df1bab551a`
- Report-Fingerprint: `f22e6cad28fbfbf73495f35da056b0bb8fe80c30ecd7d54deb09385452533cad`
- Manifest-Fingerprint: `54b0f757eb14cff8f1066629219c6470a2363d10bb34daa72f104fc772cdffa0`
- Coverage-Preflight: Workflow `36042442309`, Artifact `10827700335`
- Coverage-Fingerprint: `cc21adf1e1c12a28932e9eec1e246fa498781e0b583f92a52f85b5af24ca566b`
- 13 neue symbol-disjunkte ETFs
- 3.500 Candles je Asset / 3.498 gemeinsame PIT-Returns
- 2.798 Research / 700 Holdout
- 670+ Tests sowie alle Trial-Vorprüfungen und Ergebnisintegrität grün
- keine Orders

## Intervention

Fixed Candidate:
50 % SMA 50/200 inverse-volatility Trend + 50 % 12-1 raw-return CS Top-2 +
aggregiertes 63-Sessionen/10%-Volatilitätsbudget.

Challenger:
Nur die CS-Rangfolge wurde ersetzt durch

`252-Sessionen kumulierte Rendite / Realized Volatility derselben 252-Sessionen-Formation`

mit 21-Sessionen Skip, monatlicher Auswahl und Top-2 Long-only.

## Base-Szenario

| Kennzahl | Fixed Candidate | Risk-Adjusted CS |
|---|---:|---:|
| Research Return | +1,65 % | −8,37 % |
| Research Max DD | 22,65 % | 26,77 % |
| Research PF | 1,011 | 0,994 |
| Profitable Rolling-Fenster | 3/5 | 3/5 |
| Ø Rolling DD | 16,08 % | 16,50 % |
| Holdout Return | +27,14 % | +24,47 % |
| Holdout Max DD | 15,59 % | 14,56 % |
| Holdout PF | 1,165 | 1,150 |

Die Intervention verbessert den Holdout-Drawdown um rund 1,03 Prozentpunkte,
verschlechtert aber Research-Return, Research-DD, Research-PF, Rolling-PF,
Rolling-DD sowie die Holdout-Rendite und den Holdout-PF.

## Kostenstress

| Szenario | Challenger Holdout Return | Challenger Holdout DD | Challenger PF |
|---|---:|---:|---:|
| Base | +24,47 % | 14,56 % | 1,150 |
| 1,5x Kosten | +23,26 % | 14,69 % | 1,143 |
| 2x Kosten | +22,06 % | 14,82 % | 1,137 |

## Präregistrierte Entscheidung

Nicht bestanden:

- Research-Return > 0
- Research-Drawdown <= 10 %
- Research-PF >= 1,10
- Rolling-PF >= 1,10
- durchschnittlicher Rolling-Drawdown <= 10 %
- OOS/IS >= 0,25
- Holdout-Drawdown <= 10 %
- mehrere Nicht-Verschlechterungsbedingungen gegenüber dem Fixed Candidate

Bestanden wurden u. a. positive Rolling-Fensterquote, positiver Holdout,
Holdout-PF und beide Kostenstress-Nichtnegativitätskriterien. Das reicht
nicht für den fest definierten Vertrag.

## Forschungsentscheidung

Keine Lookup-/Skip-/Volatilitätsdefinition-Suche auf diesem Datensatz.
Keine nachträgliche Ausnutzung des Holdouts. Keine Gewichts- oder Gate-Anpassung.
Keine Produktionsintegration.

Der konkrete risk-adjusted-momentum Control wird als **NO_SUPPORT** archiviert.

## Sicherheitsstatus

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
`orders_enabled=False`

Keine Live-Ausführung.
