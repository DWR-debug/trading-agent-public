# Trial 023 — MAX-Effect Cross-Sectional Control — 2026-09-24

## Trial-ID

T-2026-09-24-023

## Forschungsfrage

Prüft wird eine einzige, feste, long-only Cross-Sectional-Hypothese:
Assets mit dem niedrigsten maximum daily close-to-close return im unmittelbar
vorangegangenen abgeschlossenen Kalendermonat erzielen im folgenden Monat
höhere Renditen als Assets mit dem höchsten Vorperioden-MAX.

Die Literatur dokumentiert einen negativen Zusammenhang zwischen vorherigem
monatlichem MAX und nachfolgenden Renditen; zugleich zeigen spätere Arbeiten,
dass die Stärke des Effekts kontextabhängig sein kann. Der Repository-Control
prüft deshalb ausschließlich, ob eine festgelegte, kostenbereinigte Variante
auf einem neuen Holdout-Satz die projektweiten Robustheitsgates erreicht.

Referenzquellen:
- Bali, Cakici & Whitelaw (2011), Maxing out: Stocks as lotteries and the
  cross-section of expected returns, Journal of Financial Economics.
- Walkshäusl (2014), The MAX effect: European evidence, Journal of Banking &
  Finance.
- aktuelle Literaturausweitung wird nicht zur nachträglichen Regeländerung
  verwendet.

## Daten

Festes, vollständig symbol-disjunktes U.S.-Aktienuniversum:

ORCL, CSCO, TXN, ADP, UPS, ABT, GILD, AMGN

- 3.500 Candles je Asset
- 3.498 Point-in-Time-Return-Perioden
- Research: 2.798 Returns
- Holdout: 700 Returns
- Timestamp-Intersection-Alignment erforderlich
- bei zu kurzer gemeinsamer Historie: fail-closed
- Yahoo historical daily data

## Präregistrierte Regel

1. Für jeden vollständig abgeschlossenen Kalendermonat wird je Asset der
   maximale positive/negative close-to-close Tagesreturn dieses Monats bestimmt.
2. Die erste Returnperiode eines Monats, deren Preisänderung den Vormonats-
   Schluss mit dem Monatsanfang verbindet, wird **nicht** dem Vormonats-MAX
   zugerechnet.
3. Am nächsten Kalendermonat werden die vier Assets mit dem niedrigsten MAX
   mit je 25% Gewicht gehalten.
4. Die vier Assets mit dem höchsten MAX bilden ausschließlich den deskriptiven
   Kontrollkorb für die Low-MAX-minus-High-MAX-Edge-Messung.
5. Bruttoexposure: 1,0x; nur Long; keine Hebelung.
6. Umschichtung: beim Kalendermonatswechsel.
7. Ausführung: Entscheidung an Timestamp t; Realisierung des folgenden
   close-to-close Intervalls t+1 bis t+2.
8. Kosten: 10 bps Fee + 5 bps Slippage = 15 bps One-Way.
9. Kostenstress: 1,5x und 2,0x.
10. Kein Parameter-Suchlauf, keine Threshold-Suche, keine Asset-Auswahl nach
    Ergebnissen, keine Holdout-Selektion.

Die Auswahl von vier Assets ist vorab festgesetzt, weil der Validierungssatz
acht Assets umfasst; es wird keine Extremquintil-/Dezilbreite gesucht.

## Entscheidungs-Gates

Alle folgenden Gates müssen gleichzeitig erfüllt sein:

- Research Return > 0
- Research Drawdown <= 10%
- Research Profit Factor >= 1,10
- mindestens 50% profitable Research-Rolling-Fenster
- OOS/Research Return Ratio >= 0,25
- Holdout Return > 0
- Holdout Drawdown <= 10%
- Holdout Profit Factor >= 1,10
- Holdout Return bei 1,5x Kosten >= 0
- Holdout Return bei 2,0x Kosten >= 0
- Low-MAX-minus-High-MAX Edge > 0 im Research
- Low-MAX-minus-High-MAX Edge > 0 im Holdout

Es gibt keinen zusätzlichen, nachträglichen Gate-Modifikator.

## Governance und Safety

- research_only = true
- strategy_variants = 1
- selection_after_results = false
- parameter_search = false
- threshold_search = false
- holdout_selection = false
- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- orders_enabled = False

Ein positives Ergebnis führt nicht automatisch zu Produktion. Promotion wäre ein
separater Governance-Schritt nach unabhängiger Evidenz und bestehenden Gates.

## Erwarteter Befund

Die Hypothese gilt ausschließlich dann als unterstützt, wenn alle oben definierten
Gates im vollständigen Control bestanden werden. Andernfalls lautet der
Outcome NO_SUPPORT; bei technischen Daten-/Integritätsproblemen wird kein
Alpha-Befund interpretiert.

