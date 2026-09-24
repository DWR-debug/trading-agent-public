# Ergebnis: Trial T-2026-09-24-026 — Common-Market-Momentum-Gate

## Status

Entscheidung: NO_SUPPORT / archived_rejected

Der präregistrierte Trial wurde als einzelner, vollständig symbol-disjunkter
Research-Control auf dem öffentlichen Repository ausgeführt. Es gab keine
Parameter-, Varianten-, Threshold- oder Holdout-Suche.

## Technischer Nachweis

- PR #130
- Merge-Commit des Research-Controls: f6d3e27d000df688b65a46c2407e349f75ed5651
- Workflow-Run: 36026930038
- Artifact-ID: 10820420657
- Artifact-SHA256: sha256:600c70bbb015c026208299dcee6ac3b370d580d7f29da2fcabdc7518e69c3523
- Report-Fingerprint: 094e7d6264ecfc96dbe8ce3b1770543754e1df66a5fa572fafa6c6a071c47e73
- Manifest-Fingerprint: 6b8b0405adb5b95b31b14b4b81432eaa789dead64860c027c7cd22b159a29dda
- Code-Commit der Präregistrierung: 1877e2e20337d4c889231b77a9ac03c5d5101f5a
- 3.500 Daily-Candles je Symbol
- 3.498 gemeinsame Point-in-Time-Return-Perioden
- 2.798 Research / 700 Holdout
- alle Vorprüfungen: Testsuite, Paper-only-Safety, Disjointness,
  Präregistrierung und Kostenvertrag grün
- Ergebnisintegrität grün
- keine Orders

## Präregistrierte Intervention

Die bestehende feste 50/50-Architektur blieb unverändert:

- 50 % SMA 50/200 inverse-volatility Trend-Sleeve;
- 50 % 12-1 Cross-Sectional-Momentum Top-2;
- bestehendes 63-Sessionen-/10%-Volatilitätsbudget.

Einziger Eingriff:

- ACWI als externer Signal-Proxy;
- 252-Sessionen Adjusted-Close-Momentum;
- bei positivem Momentum volle bestehende Exposition;
- bei nichtpositivem Momentum Gesamtportfolio auf Cash;
- Gate erst nach dem bestehenden Volatilitätsbudget;
- Gate-Umschaltungen kostenwirksam.

## Ergebnis im Base-Szenario

| Kennzahl | Fester Kandidat | Common-Market-Gate |
|---|---:|---:|
| Research Return | +27,58 % | −4,99 % |
| Research Max DD | 23,37 % | 34,01 % |
| Research PF | 1,054 | 0,996 |
| Profitable Research-Rolling-Fenster | 4/5 | 2/5 |
| OOS/IS-Return-Ratio | 0,051 | 0,000 |
| Holdout Return | +1,41 % | −0,79 % |
| Holdout Max DD | 19,95 % | 19,69 % |
| Holdout PF | 1,018 | 1,003 |

Die Intervention erfüllt keines der zwölf absoluten Kriterien des
präregistrierten Vertrages. Von den fünf Nicht-Verschlechterungsbedingungen
erfüllt sie ausschließlich die Bedingung für den Holdout-Drawdown.

## Kostenstress

Unter 1,5x Kosten:

- Baseline Holdout: +0,45 %
- Gate Holdout: −1,81 %

Unter 2x Kosten:

- Baseline Holdout: −0,50 %
- Gate Holdout: −2,82 %

Der Gate-Pfad verbessert daher auch unter den festgelegten Kostenstressen keine
der promotionsrelevanten Bedingungen.

## Diagnostischer Zusatzbefund

Das Gate war im Research in 76,73 % der Perioden aktiv, im Holdout aber in
99,57 %. Trotz dieser nahezu vollständigen Aktivierung im Holdout war die
Holdout-Rendite negativ. Der Befund spricht gegen eine einfache Interpretation
als generelle Risikoabsenkung durch Cash-Timing. Das ist rein deskriptiv und
keine Kausalaussage.

## Forschungsentscheidung

Die Hypothese wird beendet:

- kein Threshold-Tuning;
- keine alternative Momentum-Lookback-Suche;
- keine zweite Gate-Variante auf demselben Datensatz;
- keine Gate-, Parameter- oder Gewichtsänderung;
- keine Produktionsintegration;
- keine Leverage-/Short-Ausweitung;
- keine Orders.

Der Control wird als negative Evidenz gegen diese konkrete Common-Market-Gate-
Konstruktion dauerhaft archiviert.

## Nächster methodischer Schritt

Nach Trial 026 wird die Forschung nicht in eine weitere allgemeine
Volatilitäts-/Cash-Gate-Suche ausgeweitet. Die bereits vorhandene
Cross-Sectional-Reversal-Diagnostik ist die nächste orthogonale
Hypothesenquelle. Eine daraus abgeleitete Intervention muss erneut
präregistriert, vollständig symbol-disjunkt und holdout-blind validiert werden.

## Sicherheitsstatus

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False

Keine Live-Ausführung.
