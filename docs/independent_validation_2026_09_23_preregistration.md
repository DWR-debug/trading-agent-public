# Independent Validation — Pre-Registration 2026-09-23

## Research-Zweck

Die Evidenzbasis der festen 50/50 + 10%-Vol-Budget-Architektur wird auf eine zweite, vollständig symbol-disjunkte ETF-Familie erweitert. Die Untersuchung repliziert die unveränderte Architektur; sie ist keine Optimierung und keine Auswahl aus Ergebnissen.

## Vorab festgelegte Universen

### Trend-Sleeve

VTI, VEA, VTV, VUG, XLB, XLP, XLU, XLY

### Cross-Sectional-Sleeve

XBI, KRE, XME, XOP, XRT

Die Symbolliste ist vor der Datenakquisition festgeschrieben. Kein Asset darf nach Sichtung der Ergebnisse ausgetauscht werden.

Die beiden neuen Universen werden zusätzlich programmatisch gegen alle bereits registrierten Research-Universen auf Symbol-Overlap geprüft.

## Unveränderte Architektur

- Trend: SMA 50/200, inverse Volatilitätsgewichtung, Long/Flat.
- Cross-Sectional Momentum: 12-1, 252 Handelstage Formation, 21 Handelstage Skip, 21 Handelstage Rebalancing, Top-2 Long-only.
- Kapitalgewichtung: 50 % / 50 %.
- Portfolio-Volatilitätsbudget: 10 % annualisierte Realized Volatility, 63 Sessions, ausschließlich De-Risking.
- Point-in-Time-Semantik: Close(t) Entscheidung, nächstes Open, folgende Open-to-Open-Periode.
- Base-Kosten sowie 1,5x- und 2x-Kostenstress unverändert.
- Fünf feste Research-Rolling-Fenster.
- Holdout erst nach vollständiger Research-Auswertung.
- Keine Selection-Profile.
- Keine Parameteroptimierung.
- Keine Gate-Änderung.

## Datenvertrag

- 3.500 Daily-Candles je Asset.
- Identische Candle-/Return-Semantik zur ersten unabhängigen Validierung.
- Vollständiges gemeinsames Zeitachsen-Alignment.
- 2.798 Research-Returns + 700 blinde Holdout-Returns nach identischer zweistufiger Point-in-Time-Konstruktion.
- Datenqualität, Manifest-Identität und Dataset-Fingerprints fail-closed.
- Adjusted-Close-Sensitivität wird separat archiviert.
- Rohdaten und Ergebnisartefakte werden im Workflow archiviert.

## Entscheidungsregel

Die unveränderten Research-Gates bleiben die formale Beurteilungsgrundlage.

Ein PASS ist ausschließlich ein Research-Kandidatenbefund und keine Produktionsfreigabe. Ein BLOCKED-Ergebnis wird als Evidenz gegen die aktuelle robuste Forschungsthese dokumentiert, nicht durch nachträgliche Gate- oder Parameteränderungen repariert.

Bei erneutem BLOCKED wird zuerst dieselbe Failure-/Risk-Diagnostik angewandt. Erst eine über unabhängige Kontexte replizierte Ursache darf eine neue kontrollierte Intervention begründen.

## Provenienz

Der Workflow speichert Run-ID, Code-Version, Manifest-Fingerprints und Ergebnis-Fingerprint im Report. Das Adjusted-Close-Archiv wird zusätzlich mit eigenem Fingerprint gesichert.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine echte Orderausführung
- keine automatische Live-Aktivierung
