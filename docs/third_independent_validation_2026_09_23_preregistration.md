# Third Independent Candidate Validation — Pre-Registration 2026-09-23

## Research-Zweck

Die Evidenzbasis der unveränderten 50/50 + 10%-Vol-Budget-Architektur wird auf einen dritten, vollständig symbol-disjunkten ETF-Satz erweitert. Die Untersuchung ist eine reine Replikation; es werden keine Parameter aus den bisherigen Ergebnissen angepasst.

## Vorab festgelegte Universen

### Trend-Sleeve

MDY, IJH, EWA, EWJ, EWG, BND, SHY, HYG

### Cross-Sectional-Sleeve

IYR, IYT, KIE, IHF, IWC

Insgesamt dreizehn Symbole: 8 Trend + 5 Cross-Sectional. Die Symbolliste ist vor der Datenakquisition festgeschrieben. Kein Asset darf nach Sichtung von Research- oder Holdout-Ergebnissen ersetzt werden.

Die beiden neuen Universen werden programmatisch gegen sämtliche bisher registrierten Research-Universen auf Symbol-Overlap geprüft.

## Historienanforderung

Alle ausgewählten ETFs weisen nach den jeweiligen Fondsanbieterangaben eine Historie auf, die die geforderten 3.500 Daily-Candles grundsätzlich ermöglicht. Die Workflow-Datenvorbereitung prüft die tatsächlich gelieferte Candle-Anzahl und Dataset-Fingerprints fail-closed.

## Unveränderte Architektur

- Trend: SMA 50/200, inverse Volatilitätsgewichtung, Long/Flat.
- Cross-Sectional Momentum: 12-1, 252 Handelstage Formation, 21 Handelstage Skip, 21 Handelstage Rebalancing, Top-2 Long-only.
- Kapitalgewichtung: 50 % / 50 %.
- Portfolio-Volatilitätsbudget: 10 % annualisierte Realized Volatility, 63 Sessions, ausschließlich De-Risking.
- Point-in-Time-Semantik: Close(t) Entscheidung, nächstes Open, folgende Open-to-Open-Periode.
- Base-Kosten sowie 1,5x- und 2x-Kostenstress unverändert.
- Fünf feste Research-Rolling-Fenster.
- 2.798 Research-Returns + 700 blinde Holdout-Returns.
- Keine Selection-Profile, keine Parameteroptimierung, keine Gate-Änderung.

## Entscheidungsregel

Der unveränderte Research-Gate-Vertrag bleibt maßgeblich. Das Ergebnis ist eine dritte unabhängige Evidenzprobe und keine Produktionsfreigabe.

Bei BLOCKED wird wieder zuerst die bereits definierte Failure-/Risk-Diagnose angewandt. Bei PASS bleibt die bisherige Robustheitsforderung bestehen; ein positiver Holdout allein überschreibt keine Rolling-/Risikoforderung.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine echte Orderausführung
- keine automatische Live-Aktivierung