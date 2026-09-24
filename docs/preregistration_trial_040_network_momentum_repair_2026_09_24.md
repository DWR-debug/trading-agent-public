# Präregistrierung: Trial T-2026-09-24-040 — Network Momentum Repair

## Einordnung

T040 ist ein **Repair-Successor** von T039. T039 wurde ausschließlich wegen
Datenqualität blockiert: FTGC lieferte die vorgeschriebene Historie nicht.

T040 verändert deshalb ausschließlich einen Datenpunkt:

**FTGC → BIV**

Die Network-Momentum-Regel, die Portfolio-Mechanik, der Kostenvertrag und der
Research-/Holdout-Split bleiben unverändert.

T040 ist dadurch **keine vollständig unabhängige symbol-disjunkte Validierung**.
Elf Symbole werden aus T039 übernommen. BIV wurde vorab in einem festen
Coverage-only-Kandidatenpool geprüft und war dort der erste coverage-valide
Kandidat. Die Auswahl verwendete keinerlei Performance- oder Holdout-Kennzahl.

## Forschungsfrage

Kann derselbe bereits fest definierte Cross-Asset-Network-Momentum-Mechanismus
nach dem reinen Datenqualitäts-Reparaturwechsel FTGC → BIV auf einem ansonsten
unveränderten Datensatz die bestehenden Evidenz-Gates erfüllen?

## Universe

EIRL, ENZL, NORW, EDEN, FXF, FXC, CEW, EIDO, SCHO, MINT, BIV, RWX

Coverage-Vertrag:
- 3.520 Daily-Candles je Symbol
- mindestens 3.500 gemeinsame Candles
- 2.800 Research-Candles / 2.798 Research-Returnperioden
- 700 blinder Holdout
- 3.498 PIT-Returnperioden insgesamt

## Präregistrierte Regel

- eigener 252/21-Trendreturn
- Peer-Lag exakt 21 Sessions
- Lead-Lag-Korrelation über exakt 252 Sessions
- nur positive Links
- Netzwerk-Score als korrelationsgewichteter Mittelwert der verzögerten Peer-Trendsignale
- fixer 50/50-Blend mit dem eigenen Trendsignal
- finale Richtung Long/Flat
- monatliches Rebalancing
- inverse Volatilitätsgewichtung
- 10% jährliches Volatilitätsziel
- maximale Research-Exposure gemäß bestehender Projektobergrenze
- Close-at-t-Entscheidung, danach Open-to-Open-Return
- Basis-Kosten: 0,10% Fee + 0,05% Slippage
- Stress: 1,5x und 2,0x Kosten
- feste SMA-50/200-Long/Flat-Kontrolle

Es findet keine Parameter-, Threshold-, Lag-, Lookback-, Peer- oder Blend-Suche
und keine Holdout-Selektion statt.

## Coverage-Governance

Vor jeder Performanceauswertung muss der T040-Coverage-Preflight erfolgreich
sein. Ohne Coverage-Pass wird der Versuch als DATA_INVALID dokumentiert und
terminiert.

Bei Coverage-Pass wird der exakt geprüfte OHLCV-Snapshot mit Fingerprints
archiviert. Die formale Auswertung liest nur diesen Snapshot.

## Evidenz-Gates

Die bestehenden Projekt-Gates bleiben unverändert:
positive Research-Rendite; Research-DD <=10%; Research-PF >=1,10;
Rolling-PF >=1,10; mindestens 50% profitable Rolling-Fenster; durchschnittliches
Rolling-DD <=10%; OOS/Research-Ratio >=25%; positiver Holdout; Holdout-PF >=1,10;
Holdout-DD <=10%; nichtnegative Holdout-Rendite bei 1,5x/2x Kostenstress;
keine Verschlechterung der vorgeschriebenen Kontrollmetriken.

Ein Pass führt zu keiner automatischen Promotion.

## Herkunft der Assetauswahl

Die Auswahl wurde aus dem fixen Pool

BIV, BSV, DBV, DGL, FXB, JNK, RJI, UDN, VCLT, VGIT

ausschließlich anhand von Coverage vorgenommen.

Ergebnis der Messung:
BIV, BSV, FXB, JNK, UDN, VCLT und VGIT waren coverage-valid; DBV, DGL und
RJI waren zum Messzeitpunkt datenungültig. BIV war gemäß fester Reihenfolge
der deterministische erste Kandidat.

Coverage-Discovery-Fingerprint:
`d5a189c99dcac3263090212ea259df01a7c2f2fac15f89f84f03f0b29495afab`

## Sicherheit

`PAPER_ONLY=True`  
`LIVE_TRADING_ENABLED=False`  
Keine Orders. Keine automatische Promotion. Keine bezahlte Agenten-/API-Nutzung.
