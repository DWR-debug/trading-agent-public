# Trial 025 — Deskriptive Failure-Diagnose — 2026-09-24

## Zweck

Diese Diagnose interpretiert ausschließlich das bereits abgeschlossene und
unveränderte Trial-025-Ergebnis. Sie erzeugt keine neue Hypothese, keine
Parameterwahl und keine Produktionsentscheidung.

## Zeitliche Struktur

Die fünf festen Research-Rolling-Fenster zeigen:

| Fenster | Return | Max. Drawdown | Profit Factor |
|---|---:|---:|---:|
| 1 | +3,59 % | 8,55 % | 1,054 |
| 2 | +3,19 % | 16,81 % | 1,030 |
| 3 | +50,56 % | 19,05 % | 1,234 |
| 4 | +54,76 % | 24,79 % | 1,220 |
| 5 | +0,55 % | 26,08 % | 1,017 |

Der positive Research-Gesamtertrag wird damit stark von den mittleren zwei
Fenstern getragen. Die frühen Fenster sind nahezu flat und weisen PFs nahe 1
auf; das letzte Fenster liefert fast keinen zusätzlichen Gesamtertrag bei
gleichzeitigem höchsten Maximaldrawdown.

Das ist ein deskriptiver Hinweis auf zeitlich uneinheitliche Ergebnisqualität,
kein Nachweis einer bestimmten Marktursache.

## Edge-Struktur

Der fest definierte Low-Residual-Vol-vs-High-Residual-Vol-Edge ist in beiden
Splits negativ:

- Research: -2,13 bps/Tag
- Holdout: -2,21 bps/Tag

Die Richtung ist damit im Holdout nicht nur nicht bestätigt, sondern praktisch
gleichgerichtet negativ. Daraus folgt kein Beweis gegen die allgemeine
Forschungsliteratur, weil Trial 025 einen einfachen preis-/marktresidualen
Proxy verwendet und kein vollständiges mehrfaktorielles idiosyncratic-volatility
Modell.

## Risiko-/Übertragungsproblem

Der Research-Return ist positiv und der Holdout ebenfalls positiv, aber:

- Research-DD: 26,08 % statt Gate <= 10 %
- Holdout-DD: 15,06 % statt Gate <= 10 %
- OOS/Research: 0,235 statt Gate >= 0,25

Der Profit Factor und die Rolling-Quote sind dagegen positiv. Das Muster ist
deshalb nicht ein einfacher „alles negativ“-Failure, sondern eine Kombination
aus unzureichender Drawdown-Kontrolle, schwacher Return-Übertragung und
fehlendem Charakteristik-Edge.

## Methodische Konsequenz

Es wird **keine** Suche nach:

- anderen Lookbacks,
- anderen Auswahlbreiten,
- anderen Residualisierungsmodellen,
- anderen Marktdefinitionen,
- anderen Schwellen,
- anderen Assets

aus diesem Ergebnis abgeleitet.

Damit bleibt Trial 025 abgeschlossen mit:

**NO_SUPPORT / archived_rejected**

## Nächster Schritt

Der nächste Research-Schritt soll erst nach einer separaten, vorab definierten
und methodisch unabhängigen Kontrollfrage erfolgen. Ein unmittelbares Variieren
des Trial-025-Designs wäre nachträgliches Tuning und wird deshalb nicht
durchgeführt.

## Safety

- PAPER_ONLY = True
- LIVE_TRADING_ENABLED = False
- orders_enabled = False
- keine Produktionsintegration
