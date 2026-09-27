# Q026 — H2 Treasury Auction-Date Shift Performance

Stand: 2026-09-27

## Zweck

Q025 hat für die feste Q019-Population den Datumsteil von H2 validiert:
Das Auction-Result ist auf den Auktionstag zurückzuführen, während Q019
`record_date` für alle 89 Events 2–14 Kalendertage später liegt.

Q026 testet deshalb genau **eine** vorher festgelegte Mechanismusänderung:

> Gleiche Q019-/Q020-Signaldefinition, aber Signalverfügbarkeit wird vom
> `record_date` auf den `auction_date` verschoben und anschließend auf den
> ersten XNYS-Handelstag **strictly after auction_date** abgebildet.

Es gibt keine weitere Varianten- oder Parameterauswahl.

## Fixed Signal

Für jedes Q019 10-Year-Auction-Event:
- signierte Änderung des `bid_to_cover_ratio` gegenüber dem unmittelbar
  vorherigen 10-Year-Event,
- positiv = +1, negativ = -1, unverändert = 0.

Diese Signaldefinition ist identisch zu Q019/Q020.

## Einzige Intervention

Die alte Q020-Abbildung

`first XNYS session strictly after record_date`

wird ersetzt durch

`first XNYS session strictly after auction_date`.

Alle anderen Komponenten bleiben unverändert:
- Signal
- Assets
- Gewichtung
- Exposure
- Kosten
- Haltezeit
- Ausführungsmodell
- Forschungs-/Holdout-Geometrie
- Research-Gates.

## Fresh Validation Universe

12 vollständig symbol-disjunkte Assets:

`WEC, ED, OKE, VLO, EIX, NDSN, HST, AKAM, IT, DVN, HAL, SLB`

Ziel: 3.500 gemeinsame Tagesbars, mit 4.000 Rohbars Headroom.

## Geometrie

- Study window: 2011-01-01 bis 2025-09-24
- 3.500 gemeinsame Tagesbars
- 2.798 Research
- 700 Holdout
- 5 Rolling Windows
- Holdout blind
- Cost grid wie Q020: base / 1.5x / 2x.

## Gates

Unverändert gegenüber dem etablierten Evidence-Vertrag:
- positive Research-Rendite
- Research MaxDD <= 10%
- Research PF >= 1.1
- Rolling PF >= 1.1
- Rolling profitable-window ratio >= 0.5
- Rolling average DD <= 10%
- OOS/IS return ratio >= 0.25
- positive Holdout-Rendite
- Holdout PF >= 1.1
- Holdout MaxDD <= 10%
- 1.5x-/2x-Kostenstress nicht negativ
- Total-return sensitivity nicht negativ.

## Interpretation

Ein positives Ergebnis wäre ausschließlich Evidenz für diese **eine**
H2-Timingintervention auf einem frischen Universum.

Es darf nicht als Beweis einer allgemein profitablen Treasury-Strategie
interpretiert werden.

Ein Fehlschlag schließt diese feste Timing-Intervention und eröffnet keine
nachträgliche Timing-/Threshold-/Horizon-Suche.

## Governance / Safety

- neue Coverage-Prüfung vor Performance
- Snapshot-Fingerprint vor Performance unveränderlich
- Performance-Authorization erst nach erfolgreicher Coverage
- kein Holdout-Selection
- keine Promotion
- kein Live Trading

`PAPER_ONLY=True`
`LIVE_TRADING_ENABLED=False`
`orders_enabled=False`
`automatic_promotion=False`
