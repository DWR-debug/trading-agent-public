# Fourth Independent Validation — Pre-Registration 2026-09-23

## Forschungszweck

Die Evidenzbasis der unveränderten 50/50 + 10%-Vol-Budget-Architektur wird auf
eine vierte, vollständig symbol-disjunkte ETF-Familie erweitert. Dieser Lauf
ist eine reine Replikationsprüfung der bestehenden Architektur und keine
Optimierung.

## Vorab festgelegte Universen

### Trend-Sleeve

SCHB, VO, VB, VXF, VXUS, VGK, IAU, AGG

### Cross-Sectional-Sleeve

KBE, KCE, IYZ, IHI, XHB

Die 13 Symbole wurden vor der Datenakquisition festgelegt. Kein Asset wird nach
Ergebnissichtung ersetzt. Alle Symbole wurden gegen die bereits registrierten
Research-Universen auf Überschneidung geprüft.

Die gewählten Fonds haben eine historische Auflage vor 2012. Damit ist das
vorhandene 3.500-Candle-Protokoll methodisch zeitlich realisierbar; die
Workflow-Datenprüfung bleibt fail-closed und akzeptiert nur tatsächlich
gelieferte 3.500 Candles je Asset.

## Unveränderte Architektur

- Trend: SMA 50/200, inverse Volatilitätsgewichtung, Long/Flat.
- Cross-Sectional Momentum: 12-1, 252 Handelstage Formation, 21 Handelstage
  Skip, 21 Handelstage Rebalancing, Top-2 Long-only.
- Aggregation: 50% / 50%.
- Portfolio-Volatilitätsbudget: 10% annualisierte Realized Volatility, 63
  Sessions, ausschließlich De-Risking.
- Point-in-Time-Semantik: Close(t) Entscheidung, nächstes Open, folgende
  Open-to-Open-Periode.
- Base-Kosten sowie 1,5x- und 2x-Kostenstress unverändert.
- Fünf feste Research-Rolling-Fenster.
- 2.798 Research-Returns + 700 blinde Holdout-Returns.
- Keine Selection-Profile, keine Parameteroptimierung, keine Gate-Änderung.
- Keine Produktionsänderung und keine Orders.

## Entscheidungsregel

Die unveränderten Research-Gates bleiben die formale Beurteilungsgrundlage.
Ein PASS ist nur ein Kandidatenbefund, keine Produktionsfreigabe. Ein BLOCKED
wird nicht durch nachträgliche Parameter-, Gate-, Kosten- oder Asset-Änderung
repariert.

Bei erneuten Failure-Gates wird die vorhandene Failure-/Risk-Diagnostik über
den neuen Satz gelegt. Nur wenn ein neuer, reproduzierbarer Kontrast über
unabhängige Kontexte entsteht, darf daraus eine separat präregistrierte
Intervention abgeleitet werden.

## Provenienz

Workflow und Report speichern Run-ID, Code-Version, Manifest-Fingerprints,
Adjusted-Close-Archiv-Fingerprint und Ergebnis-Fingerprint. Das gesamte
Daten-/Ergebnisartefakt wird archiviert.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine echte Orderausführung
- keine Live-Aktivierung
