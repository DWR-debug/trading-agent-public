# Unabhängiger Europa-Trend-Control — Ergebnisse 2026-09-22

Offizieller Run: 35778620708

Report-Fingerprint:
13f4cff7e7713859309e9b2791975ebbbf4488c1e06f5759d5223b6bc54a072c

Manifest-Fingerprint:
154f5a7ec9f31725f03472f8056ef0d5f53bb05032bede83efa7ea3d5c9253bc

## Datenbasis

Universum:
- RHM.DE
- TUI1.DE
- NEL.OL
- VOW3.DE

Je Asset wurden 2.500 abgeschlossene Tages-Candles vorbereitet.

Die Daten stammen aus dem bereits definierten Aktien-Research-Pfad über
Yahoo Chart und wurden per Manifest fingerprinted.

Vendor-Qualitätsfilter:
- RHM.DE: 1 inkonsistente OHLC-Zeile verworfen
- TUI1.DE: 33 inkonsistente OHLC-Zeilen verworfen
- NEL.OL: 0
- VOW3.DE: 0

Keine Zeile wurde preislich repariert oder synthetisch verändert.
Die verworfenen Vendor-Zeilen wurden ausschließlich nicht in den Research-
Datensatz übernommen und werden im Manifest gezählt.

## Methodik

- Close(t) Entscheidung
- Open(t+1) Ausführung
- Open(t+2) Folge-Open für Renditemessung
- fixe Gebühren 0,10 %
- fixe Slippage 0,05 %
- ATR-basierte Exposition
- gleiches Kapitalgewicht über die vier Assets
- 80 % Research / 20 % Holdout
- keine Optimierung
- keine Selection-Profile
- kein Gate-Tuning
- keine Produktionsumschaltung

Getestete feste Familien:
- Buy-and-Hold
- TSM-Ensemble 63/126/252
- SMA 50/200 Long/Flat
- Donchian 55/20

## Ergebnis

| Strategie | Research | Holdout | max. DD Holdout | PF Holdout | Rolling positiv |
| --- | ---: | ---: | ---: | ---: | ---: |
| Buy-and-Hold | +158,71 % | +8,38 % | 26,49 % | 1,050 | 4/5 |
| TSM-Ensemble | +3,59 % | -2,95 % | 6,92 % | 0,890 | 3/5 |
| SMA 50/200 | +7,06 % | +0,90 % | 2,40 % | 1,059 | 4/5 |
| Donchian 55/20 | +2,73 % | +1,55 % | 2,95 % | 1,083 | 2/5 |

Rolling-Fenster des SMA-50/200-Modells:
- Fenster 1: +1,37 %, PF 1,091
- Fenster 2: -0,02 %, PF 1,001
- Fenster 3: +2,26 %, PF 1,281
- Fenster 4: +0,23 %, PF 1,018
- Fenster 5: +1,15 %, PF 1,081

## Interpretation

Die Europa-Prüfung repliziert die US-Beobachtung nur teilweise.

Das TSM-Ensemble bleibt im Holdout negativ und fällt im letzten Rolling-Fenster
deutlich zurück. Damit ist kein universeller TSM-Effekt über diese beiden
Aktienuniversen belegt.

SMA 50/200 bleibt im Europa-Universum im Holdout positiv und hat 4/5 positive
Rolling-Fenster bei deutlich geringerer Holdout-Drawdown-Exposition als
Buy-and-Hold. Die gemessene Holdout-Rendite ist jedoch klein und der PF liegt
nur knapp über 1.0.

Donchian bleibt ebenfalls positiv im Holdout, aber nur 2/5 Rolling-Fenster sind
positiv.

Buy-and-Hold liefert die höhere Roh-Rendite, aber mit deutlich höherem
Drawdown.

Damit stärkt der Europa-Control die Aussage:

**Längere Trendregeln können die Risiko-/Stabilitätsstruktur gegenüber der
bisherigen kurzfristigen Architektur verbessern, aber die Existenz eines
universellen aktiven Alpha-Edges ist nicht belegt.**

## Methodische Konsequenz

Der nächste Schritt ist keine Auswahl eines einzelnen Modells.

Stattdessen:
1. längere Trendfamilien auf einer wirklich unabhängigen und breiteren
   Multi-Asset-Basis testen,
2. Kosten-/Turnover-Stress auch außerhalb des US-Benchmarks prüfen,
3. danach erst eine kleine Anzahl von Kandidaten in den bestehenden
   WFO-/Rolling-WF-/Robustness-/Overfit-/Holdout-Pfad überführen.

Die bestehenden Gates bleiben unverändert.

## Datenpipeline-Verbesserung

Der Yahoo-Loader unterstützt jetzt optional das explizite Verwerfen
inkonsistenter Vendor-OHLC-Zeilen für den explorativen Aktienpfad.

Standardverhalten bleibt streng.

Die Anzahl verworfener Zeilen wird im Research-Manifest gespeichert, sodass die
Datenqualität nachvollziehbar bleibt.

## Sicherheitszustand

- Paper-Only aktiv
- Live-Trading deaktiviert
- keine Orders
- keine Produktionsstrategie geändert
- keine Gate-Schwellen geändert
