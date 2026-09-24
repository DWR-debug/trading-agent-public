# Präregistrierung: CS-Reversal-Schweregrad und Persistenz 2026-09-24

## Forschungsfrage

Der vorherige Vierfach-Befund zeigte eine replizierte Anreicherung des bereits
fest definierten Cross-Sectional-Winner-Reversal-Zustands. Diese Anschlussdiagnose
charakterisiert ausschließlich Schweregrad, Persistenz und die feste
21-Session-Rebalance-Phase.

## Feste Datenbasis

- Artifact 10751817990
- Artifact 10740188093
- Artifact 10745697729
- Artifact 10753545703

Je Satz werden ausschließlich die 2.798 Research-Perioden ausgewertet.
Holdout-Daten bleiben ausgeschlossen.

## Unveränderter Zustand

Reversal liegt vor, wenn der realisierte Open-to-Open-Return der festen Top-2
CS-Gewinner minus dem gleichgewichteten Return der drei Nichtgewinner < 0 ist.

Es wird kein neuer Reversal-Schwellenwert eingeführt.

## Auswertung

### Schweregrad

Für Reversal- und Nicht-Reversal-Tage werden Beobachtungszahl, Anteil,
Mittelwert, Median, Minimum, Mittelwertdifferenz, schlechtesten 5%-Enrichment und der
Anteil der negativen Portfolio-Return-Masse ausgewiesen.

### Persistenz

Aufeinanderfolgende Reversal-Tage bilden exakt eine Episode. Pro Episode werden
Länge, Start/Ende, kumulierter Spread, mittlerer Spread, Minimum und kumulierter
Portfolio-Return gespeichert. Zusätzlich werden mittlere, mediane und maximale
Länge sowie die vollständige Längenverteilung berichtet.

Es wird keine Episodenlänge optimiert oder als Gate verwendet.

### Rebalance-Phase

Jede Research-Periode erhält deterministisch die Phase Index modulo 21,
wobei 21 der unveränderten CS-Rebalance-Periode entspricht. Für alle 21 Phasen
werden Reversal-Anzahl, Reversal-Rate, negative Portfolio-Tagesrate und
mittlerer Winner-to-Nonwinner-Spread ausgewiesen.

Keine Phase wird ausgewählt oder zur Strategieänderung verwendet.

## Replikation

Der Richtungsbefund gilt als repliziert, wenn in mindestens >=3/4 der
Validierungen der mittlere Reversal-Spread relativ zu Nicht-Reversal-Tagen
negativ ist. Die Worst-5%-Anreicherung wird zusätzlich gezählt.

## Unverändert

Kandidat, 50/50-Gewichte, Trend-Regel, CS-Regel, Point-in-Time-Semantik,
Kostenmodell, immutable Artefakte und Research/Holdout-Grenze bleiben
unverändert. Keine Optimierung, Asset-Auswahl, Parameter-/Schwellenwertsuche,
Gate- oder Produktionsänderung, keine neuen Daten-Downloads. PAPER_ONLY=True.

## Erwartete Nutzung

Nur ein replizierter deskriptiver Befund darf später in eine separat
präregistrierte Architekturhypothese für einen neuen, vollständig
symbol-disjunkten Validierungssatz überführt werden.
