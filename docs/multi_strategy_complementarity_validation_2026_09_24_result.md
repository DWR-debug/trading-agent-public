# Ergebnis: siebte Multi-Strategie-Komplementaritätsvalidierung 2026-09-24

## Laufidentität

- Trial-ID: T-2026-09-24-011
- Workflow-Run: 36001213390
- Artifact-ID: 10808382149
- Artifact-ZIP-SHA256: fb1d6f7be425c4a138a935038e5bb2cda7dc505d551526df64cfec8c77ab18df
- Report-Fingerprint: 730fa24672298e943d8b146184aa6919281b1345a6dbd04461bd476efa4a0654

## Daten und Methodik

Der präregistrierte Control wurde auf dem siebten vollständig symbol-disjunkten Validierungssatz durchgeführt.

Trend:
SLV, RSP, VYM, VIG, DVY, EPP, EWU, EWZ

Cross-sectional:
AAPL, MSFT, AMZN, META, GOOGL

- 3.500 gemeinsame Tages-Candles je Asset
- 3.498 gemeinsame Point-in-Time-Return-Perioden
- Research: 2.798 Returns
- Holdout: 700 Returns
- keine Optimierung
- keine Auswahl
- Holdout nicht zur Selektion verwendet
- identische 10%-Volatilitätssteuerung, Kosten und PIT-Semantik
- keine Orders

Die Datenakquisition benötigte einen rein technischen Puffer, weil die ursprünglichen Zeitreihen der beiden Teiluniversen um einen Handelstag versetzt waren. Anschließend wurden auf der gemeinsamen Zeitachse exakt die letzten 3.500 gemeinsamen Zeitstempel verwendet. Es wurden keine fehlenden Candles aufgefüllt.

## Basis-Szenario

| Variante | Research Return | Research DD | Research PF | Holdout Return | Holdout DD | Holdout PF |
|---|---:|---:|---:|---:|---:|---:|
| Trend-only | +7,03% | 25,71% | 1,0221 | +25,61% | 13,13% | 1,1649 |
| Cross-sectional-only | +171,17% | 14,26% | 1,1833 | +27,99% | 12,85% | 1,1704 |
| Fester 50/50-Blend | +109,70% | 15,61% | 1,1352 | +30,68% | 13,69% | 1,1811 |

Rolling-Profit-Factor des Research:
- Trend-only: 1,0221
- Cross-sectional-only: 1,1833
- 50/50: 1,1352

## Präregistrierte Komplementaritäts-Diagnostik

Die fünf vordefinierten diagnostischen Vergleiche ergaben:

- Research-DD des Blends nicht schlechter als beide Einzelvarianten: Nein
- Research-Rolling-PF des Blends nicht schlechter als beide Einzelvarianten: Nein
- Holdout-DD des Blends nicht schlechter als beide Einzelvarianten: Nein
- Holdout-PF des Blends nicht schlechter als beide Einzelvarianten: Ja
- positive Blend-Rendite in Research und Holdout: Ja

Damit liegt auf diesem siebten Datensatz kein Nachweis der präregistrierten universellen Komplementaritätsstruktur vor.

Das ist ausdrücklich kein Beweis, dass 50/50 grundsätzlich ungeeignet ist. Der Control beantwortet nur die vorab definierte Frage auf diesem neuen Validierungssatz.

## Kostenstress

Die präregistrierten 1,5x- und 2x-Kosten-Szenarien wurden ausgeführt und bleiben Bestandteil des unveränderlichen Research-Artefakts. Die Abweichung der Komplementaritäts-Kriterien ist bereits im Basis-Szenario sichtbar; daher wird keine Gewichtsanpassung aus diesem Datensatz abgeleitet.

## Forschungsentscheidung

- Trial wird als archived_rejected archiviert.
- Keine Änderung an 50/50-Gewichten.
- Keine weitere Gewichtssuche auf diesem siebten Datensatz.
- Keine Änderung bestehender Research-Gates.
- Keine Produktionsintegration.
- Keine Leverage-/Short-Ausweitung.
- Keine Orders.

## Sicherheitsstatus

PAPER_ONLY=True

LIVE_TRADING_ENABLED=False

orders_enabled=False