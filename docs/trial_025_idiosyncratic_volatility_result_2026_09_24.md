# Trial 025 — Marktresiduale Volatilität — Ergebnis — 2026-09-24

## Ergebnisstatus

**T-2026-09-24-025: NO_SUPPORT / archived_rejected**

Der Control wurde vollständig, reproduzierbar und paper-only ausgeführt. Es wurden
keine Parameter-, Threshold-, Auswahlbreiten- oder Asset-Suchen durchgeführt und
der Holdout wurde nicht zur Auswahl verwendet.

## Technischer Nachweis

- Workflow-Run: 36022604471
- Artifact-ID: 10818270142
- Report-Fingerprint: 9f2088cb95fb6f7d0d5e3a1b9e6b2857c03c5904871cad4cefaffef9533e860e
- Manifest-Fingerprint: bc146938fa2b112b23bc71503c1649fcf9d84f802b2ce27dc8c8e9a8441f5ed7
- vollständig symbol-disjunktes Universum: COST, TMO, LIN, DE, EMR, SBUX, VZ, MA
- 3.500 Candles je Asset
- 3.498 gemeinsame Point-in-Time-Returnperioden
- Research/Holdout: 2.798 / 700
- vollständige Testsuite: erfolgreich
- Paper-only-Safety: erfolgreich
- Universums-Disjointness: erfolgreich
- Präregistrierung: erfolgreich
- Kostenvertrag: erfolgreich
- Ergebnisintegrität: erfolgreich
- Artifact-Upload: erfolgreich

## Präregistrierte Methode

Monatliche Rangfolge der Standardabweichung der Residuen einer OLS-Regression
Asset-Return gegen den Leave-One-Out-gleichgewichteten Marktreturn der übrigen
sieben Assets, jeweils auf den unmittelbar vorherigen 252 abgeschlossenen
Sessions. Die vier niedrigsten Residual-Volatilitäten wurden gleichgewichtet
long gehalten. Die vier höchsten dienten ausschließlich als Edge-Control.

1x gross, long-only, keine Hebelung, keine Shorts, 10 bps Fee + 5 bps Slippage,
zusätzlich 1,5x- und 2x-Kostenstress.

## Zentrale Kennzahlen

### Base

| Kennzahl | Research | Holdout |
|---|---:|---:|
| Return | +150,43 % | +35,37 % |
| Max. Drawdown | 26,08 % | 15,06 % |
| Profit Factor | 1,118 | 1,156 |
| OOS/Research Return Ratio | — | 0,235 |
| profitable Rolling-Fenster | 5/5 | — |

Kostenstress Holdout:
- 1,5x: +35,06 %
- 2,0x: +34,76 %

### Edge

- Low-Residual-Vol minus High-Residual-Vol, Research: **-2,13 bps/Tag**
- Low-Residual-Vol minus High-Residual-Vol, Holdout: **-2,21 bps/Tag**

Der Edge ist damit bereits im Research negativ und bleibt im Holdout negativ.

## Gate-Auswertung

Bestanden:
- positive Research-Rendite
- Research-PF >= 1,10
- mindestens 50 % profitable Rolling-Fenster
- positiver Holdout
- Holdout-PF >= 1,10
- 1,5x- und 2x-Kostenstress nichtnegativ

Verfehlt:
- Research-Drawdown <= 10 %
- OOS/Research Return Ratio >= 0,25
- Holdout-Drawdown <= 10 %
- positiver Low-Residual-Vol-vs-High-Residual-Vol-Edge im Research
- positiver Low-Residual-Vol-vs-High-Residual-Vol-Edge im Holdout

## Methodische Interpretation

Der Control liefert keinen belastbaren Änderungsgrund für die Strategie.

Insbesondere wird nicht behauptet, dass „idiosyncratic volatility“ allgemein
nicht funktioniert. Dieser Trial war ein bewusst einfacher, preisbasierter
Leave-One-Out-Marktresidual-Proxy und keine vollständige Replikation eines
mehrfaktoriellen Asset-Pricing-Modells.

Aus dem Ergebnis wird keine weitere Suche über Lookback, Auswahlbreite,
Residualisierungsmodell oder verwandte Volatilitätsdefinitionen abgeleitet.
Es gibt keine Produktionsintegration und keine Änderung bestehender Gates,
Gewichte oder Parameter.

## Nächster methodischer Schritt

Der nächste Schritt ist **deskriptive Failure-Diagnose statt unmittelbares
Tuning**. Zu prüfen sind insbesondere:

- welche der fünf Research-Zeitfenster die hohen Drawdowns tragen;
- ob die negative Edge-Beziehung über Zeit gleichgerichtet oder phasenabhängig ist;
- ob die beiden Effekte überwiegend aus gemeinsamen Marktbewegungen oder
  einzelnen Assets stammen;
- ob aus derselben unveränderten Evidenz überhaupt eine vorab definierte,
  methodisch unabhängige Kontrollfrage ableitbar ist.

Ohne eine solche klar vorab definierbare Frage bleibt der Trial abgeschlossen.

## Safety

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- orders_enabled = False
- keine Live-Ausführung
- keine automatische Promotion
