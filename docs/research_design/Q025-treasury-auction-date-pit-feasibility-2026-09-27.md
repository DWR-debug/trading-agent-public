# Q025 — Treasury Auction-Date PIT Feasibility

Stand: 2026-09-27

## Zweck

Q024 zeigte, dass der aktuelle offizielle Treasury Auction Results RSS Feed
reproduzierbare `pubDate`-Timestamps liefert, aber keine historische Abdeckung
für die 89 festen Q019-Ereignisse besitzt.

Q025 beantwortet deshalb die verbleibende H2-Datumsfrage ohne künstliche
Intraday-Präzision:

> War das für Q019 verwendete `bid_to_cover_ratio` nachweislich am
> Auktionstag öffentlich, sodass `record_date` nicht der früheste
> Informationszeitpunkt gewesen sein kann?

## Ex ante fixierter Datenvertrag

Die 89 Q019-Ereignisse bleiben vollständig unverändert.

Für jedes Event werden geprüft:
- Q019 `auction_date`
- Q019 `record_date`
- Q019 `cusip`
- Q019 `bid_to_cover_ratio`
- offizielles Treasury Auction Results PDF, eindeutig über CUSIP und
  Auction-Results-Inhalt identifiziert
- Result-PDF-Datum / offizielles Result-Datum

Die Treasury Auction Timeline wird als historische Primärquelle für die
Release-Semantik verwendet. Sie dokumentiert:
- ab Januar 2003: offizielle Release-Zeit = aufgezeichnete Zustellung der
  Results-XML an den FRIT-Server,
- ab April 2004: automatisierte Internet-Veröffentlichung der Result-PDFs,
- ab August 2004: Auction Results innerhalb von 2 Minuten ± 30 Sekunden.

Da Q019 erst 2011 beginnt, liegt die gesamte feste Population in diesem
post-2004 Release-Regime.

## Pass-Kriterium

Q025 gilt als `DATE_PIT_VALIDATED`, wenn:
1. 89/89 Result-PDFs eindeutig identifiziert sind,
2. deren Result-Datum dem jeweiligen Q019 `auction_date` entspricht,
3. `record_date > auction_date` für 89/89 Ereignisse.

Damit ist keine exakte Intraday-Zeit notwendig, um den wesentlich späteren
Q019 `record_date` als frühesten Informationszeitpunkt zurückzuweisen.

## Interpretation

Ein Q025-Pass bedeutet ausschließlich:
- Das Signal ist datenseitig auf den Auktionstag zurückführbar.
- `record_date` ist für Q019 ein späterer Datumsanker.

Es bedeutet **nicht**, dass eine zeitverschobene Strategie profitabel ist.

## Governance

Keine Performance, kein Holdout, keine Parameter-/Asset-/Threshold-/
Horizon-/Varianten-Suche, keine Gateänderung, keine Promotion, keine
Live-Ausführung.

Sicherheit:
`PAPER_ONLY=True`
`LIVE_TRADING_ENABLED=False`
`orders_enabled=False`
`automatic_promotion=False`
