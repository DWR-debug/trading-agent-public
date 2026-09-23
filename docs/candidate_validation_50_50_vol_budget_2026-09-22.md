# Candidate Validation: feste 50/50 + 10%-Volatilitätsbudget-Architektur

## Zweck

Dieser Control validiert die unveränderte Kandidatenarchitektur auf zwei vorab festgelegten, vollständig disjunkten Asset-Universen:

- Trend-Sleeve: DIA, EEM, LQD, IEF, VNQ, USO, FXE, TIP
- Cross-Sectional-Sleeve: XLK, XLF, XLE, XLV, XLI

Die Universen haben keinen Symbol-Overlap mit den bisherigen Mechanismus-Replikationen. Die Validierung ist damit asset-unabhängig, aber ausdrücklich **nicht out-of-time**; die Daten werden im Workflow neu als aktuelle historische Yahoo-Daten vorbereitet.

## Kandidat

- 50 % Cross-Asset SMA 50/200, inverse Volatilitätsgewichtung, Long/Flat
- 50 % 12-1 Cross-Sectional Momentum, Top-2 Long-only
- 10 % annualisiertes Realized-Volatility-Ziel
- 63 Sessions Lookback
- nur De-Risking, nie Hebel
- Signale, Sleeve-Gewichte und Ausführung unverändert
- keine Optimierung und keine Selection-Profile

Die Point-in-Time-Semantik bleibt: Close(t)-Entscheidung, Ausführung am nächsten Open und anschließende Open-to-Open-Periode.

## Daten und Trennung

Je Asset werden 3.500 abgeschlossene Daily-Candles geladen. Aufgrund der zweistufigen Point-in-Time-Return-Konstruktion entstehen 3.498 gemeinsame Return-Beobachtungen.

Davon sind 2.798 Research-Beobachtungen und 700 vollständig blinde Holdout-Beobachtungen. Die fünf festen Rolling-Fenster decken den gesamten Research-Abschnitt ab; das letzte Fenster enthält den verbleibenden Rest der ganzzahligen Fünftelteilung.

Vor der Auswertung werden Universe, Asset-Reihenfolge, Candle-Anzahl, Dataset-Fingerprint, gemeinsame Zeitachse und Paper-Only-Sicherheit fail-closed verifiziert.

## Kostenstress und Gates

Verwendet werden drei vorab festgelegte Kostenszenarien:

- Base: 0,10 % Fee + 0,05 % Slippage
- 1,5× Stress: exakt die bestehende ResearchGateConfig-Stressgröße
- 2× Stress: zusätzlicher Vergleich gemäß dem bereits abgeschlossenen Mechanismus-Convergence-Control

Die numerischen Schwellen werden aus ResearchGateConfig übernommen und nicht geändert:

- Profit Factor mindestens 1,10
- maximaler Drawdown 10 %
- mindestens 50 % profitable Research-Rolling-Fenster
- OOS/IS-Renditeverhältnis mindestens 0,25
- Holdout positiv
- 1,5× und 2× Stress-Holdout nicht negativ

Bei diesem kontinuierlichen Portfolio-Return-Control werden keine künstlichen Trade-Count-Gates erzeugt.

## Total-Return-Sensitivität

Für jedes der 13 Validierungsassets wird der Yahoo Adjusted-Close-Pfad separat geladen und auf die exakt verifizierten Rohdatenzeitpunkte ausgerichtet.

Die Sensitivität ersetzt nicht das Point-in-Time-Ausführungsmodell. Stattdessen wird die Differenz zwischen Adjusted-Close- und Roh-Close-Return auf den bestehenden Open-to-Open-Portfolio-Returnpfad aufgesetzt. Dadurch bleibt der Ausschüttungs-/Corporate-Action-Effekt als separater diagnostischer Layer sichtbar.

## Sicherheits- und Interpretationsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Änderung der Produktionsstrategie
- kein Gate-Loosening
- keine Optimierung als Abkürzung
- kein nachträgliches Out-of-Time-Framing

Ein PASS wäre ausschließlich ein Research-/Kandidatenbefund und keine Produktionsfreigabe. Ein BLOCKED-Befund wird ebenfalls nicht durch Parameteränderungen „repariert“, sondern führt zur fachlichen Diagnose der konkreten Failure-Kriterien.


## Ergebnis des Validierungslaufs 2026-09-22

GitHub Actions Run: 35784541912  
Artifact-ID: 10719572732  
Report-Fingerprint: 9766e07ba1d63b1cc5ee901a1a7e3570187fcbbc463b7295fb1cb221dc66fbf9  
Trend-Manifest-Fingerprint: c9a2a44f04703db86dc455113b3d128451683a930bdea8ec84b54a0b47a925a4  
Cross-Sectional-Manifest-Fingerprint: 61f560824ca09bf4f87330af2e07e0cec1464625ad075674159b6496ce8117d3

Technische Vorbedingungen:
- 362 Tests bestanden
- Paper-Only-Safety bestanden
- beide 3.500-Candle-Manifeste fail-closed verifiziert
- 13 unabhängige ETFs verarbeitet
- 3.498 gemeinsame Return-Beobachtungen
- 2.798 Research / 700 blinder Holdout

### Kandidatenbefund

Die feste 50/50 + 10%-Vol-Budget-Architektur wurde als BLOCKED klassifiziert, weil unveränderte Research-Gates auf der unabhängigen Datenbasis nicht vollständig bestanden wurden.

Base, Price-only:
- Research Return: +42,30 %
- Research Drawdown: 16,81 %
- Research PF: 1,075
- Holdout Return: +29,78 %
- Holdout Drawdown: 12,01 %
- Holdout PF: 1,194
- OOS/IS Return Ratio: 0,704
- profitable Research-Rolling-Fenster: 4/5 = 80 %

Die formalen Failure-Kriterien sind:
- Research-Drawdown > 10 %
- Rolling-Research-PF < 1,10
- durchschnittlicher Rolling-Drawdown > 10 %
- Holdout-Drawdown > 10 %

Nicht fehlgeschlagen sind:
- positive Research-Gesamtrendite
- profitable-window-Quote
- OOS/IS-Ratio
- positiver Holdout
- Holdout-PF
- 1,5x-Kostenstress
- 2x-Kostenstress
- Total-Return-Sensitivität

Kostenstress:
- 1,5x: Holdout +28,58 %, DD 12,10 %, PF 1,187
- 2x: Holdout +27,39 %, DD 12,18 %, PF 1,179

### Rolling-Fenster

| Fenster | Return | Max DD | PF |
| --- | ---: | ---: | ---: |
| 1 | +11,40 % | 5,19 % | 1,219 |
| 2 | -3,61 % | 15,59 % | 0,976 |
| 3 | +11,14 % | 15,00 % | 1,110 |
| 4 | +17,68 % | 16,81 % | 1,146 |
| 5 | +1,32 % | 10,54 % | 1,018 |

Der Fehler ist damit kein reines Holdout-Problem. Die Risikoseite und die
Rolling-PF-Seite verfehlen bereits im Research-Zeitraum die unveränderten
Schwellen.

### Vol-Budget-Effekt gegenüber unskaliert

Base, unskaliert:
- Research +62,39 %, DD 25,27 %, PF 1,088
- Holdout +40,26 %, DD 15,80 %, PF 1,229

Base, 10%-Vol-Budget:
- Research +42,30 %, DD 16,81 %, PF 1,075
- Holdout +29,78 %, DD 12,01 %, PF 1,194

Das feste Budget reduziert den Drawdown deutlich, reicht auf diesem
unabhängigen Universum aber noch nicht bis zum 10%-Gate.

### Total-Return-Sensitivität

Im Base-Holdout verändert die Adjusted-Close-Sensitivität den Befund in
positive Richtung:
- Renditedelta: +6,23 Prozentpunkte
- Drawdowndelta: -0,15 Prozentpunkte
- PFdelta: +0,0368

Damit ist der offene ETF-Total-Return-Punkt fachlich kontrolliert, aber
noch nicht als eigenständige Produktionsrechnung zu verstehen.

### Interpretation

Der Lauf bestätigt eine wichtige Trennung:

Die Mechanismus-/Portfolio-Idee erzeugt auf einer vollständig neuen Asset-Basis
weiterhin einen positiven Holdout-Befund und ein akzeptables OOS/IS-Verhältnis.
Die vollständige Research-Gate-Konformität ist jedoch noch nicht gegeben,
weil die Risikostruktur und der Rolling-PF auf der langen unabhängigen Basis
noch nicht stabil genug sind.

Die Klassifikation BLOCKED ist deshalb ein echter Forschungsbefund und kein
Anlass, Gate-Schwellen nachträglich zu lockern oder die Kandidatenparameter
an diese Daten anzupassen.

Wichtig: Die Validierung ist asset-unabhängig, aber nicht out-of-time. Die
13 ETFs sind neue Symbole gegenüber den vorherigen Mechanismus-Replikationen,
nicht jedoch eine zeitlich vollständig unbekannte Zukunftsperiode.
