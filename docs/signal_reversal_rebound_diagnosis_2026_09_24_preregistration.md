# Präregistrierung: Signal-Reversal-/Rebound-Diagnose 2026-09-24

## Forschungsfrage

Sind die schlechtesten Research-Tage des unveränderten 50/50-Kandidaten systematisch mit
einem vorherigen Rückgang und anschließendem Rebound des Validierungsuniversums und/oder
einer kurzfristigen Umkehr innerhalb der festen Cross-Sectional-Momentum-Signale verbunden?

Die Diagnose dient ausschließlich der Root-Cause-Eingrenzung. Sie ist keine Produktions-
oder Gate-Entscheidung.

## Externe Motivation

Daniel und Moskowitz (2016) beschreiben Momentum-Crashs als negative Renditeepisoden,
die insbesondere nach Markt-Rückgängen und gleichzeitig mit Markt-Rebounds auftreten können.
Moreira und Muir (2017) untersuchen Volatilitätssteuerung und argumentieren, dass die
zeitliche Variation von Risiko gegenüber der erwarteten Rendite relevant sein kann.

Quellen:
- Daniel, K. & Moskowitz, T. J. (2016), "Momentum Crashes", Journal of Financial Economics
  122(2), 221-247. DOI: https://doi.org/10.1016/j.jfineco.2015.12.002
- Moreira, A. & Muir, T. (2017), "Volatility-Managed Portfolios", Journal of Finance
  72(4), 1611-1644. DOI: https://doi.org/10.1111/jofi.12513

## Feste Datenbasis

Vier bereits abgeschlossene, immutable und symbol-disjunkte Validierungen:

1. Artifact 10751817990
2. Artifact 10740188093
3. Artifact 10745697729
4. Artifact 10753545703

Je Validierung werden ausschließlich die 2.798 Research-Perioden ausgewertet.
Holdout-Metriken werden nicht ausgegeben und dürfen die Diagnose nicht beeinflussen.

## Feste Zustände

### 1. Rebound-after-decline

Am Entscheidungszeitpunkt gilt:

- der gleichgewichtete 20-Session-Return des gesamten 13-Asset-Validierungsuniversums
  auf Close-to-Close-Basis ist < 0;
- die unmittelbar folgende realisierte gleichgewichtete Open-to-Open-Rendite des
  13-Asset-Universums ist > 0.

Der Proxy ist ausdrücklich kein externer Marktindex. Er ist ein vorab festgelegter,
gleichgewichteter Querschnitt der 8 Trend- und 5 Cross-Sectional-Assets.

### 2. Cross-Sectional-Winner-Reversal

Die unmittelbar realisierte Open-to-Open-Rendite der zwei vom unveränderten
252-Session/21-Session/21-Session/Top-2-Regel ausgewählten Cross-Sectional-Gewinner
minus der gleichgewichteten Rendite der drei nicht ausgewählten Assets ist < 0.

Damit wird ausschließlich die kurzfristige Umkehr der bereits fest bestimmten Gewinner
gegenüber den Nichtgewinnern gemessen.

### 3. Kombinierter Zustand

Der kombinierte Zustand ist die logische UND-Verknüpfung aus
"Rebound-after-decline" und "Cross-Sectional-Winner-Reversal".

## Vorgegebene Auswertung

Für jeden Zustand werden im Research dokumentiert:

- Beobachtungsanzahl und Anteil;
- mittlere und mediane Portfolio-Research-Rendite;
- positive Tagesquote;
- Profit Factor;
- Differenz zum Nicht-Zustand;
- Anteil der schlechtesten 5% Portfolio-Tage;
- Enrichment Ratio der schlechtesten 5% gegenüber allen Research-Tagen;
- Zustand am Beginn des maximalen Research-Drawdowns und in dessen ersten zwei Tagen;
- Zustandsanteile in fünf fest abgegrenzten Research-Fenstern.

Ein Zustand gilt innerhalb eines Validierungssatzes nur dann als "enriched", wenn
mindestens 10 Research-Beobachtungen vorliegen, die Enrichment Ratio der schlechtesten
5% > 1 ist und die mittlere Portfolio-Rendite im Zustand unter jener der Nicht-Zustands-
Tage liegt.

Eine replizierte Diagnose erfordert denselben Flag in mindestens 3 von 4 Validierungen (`>=3/4`).
Diese Regel erzeugt keine Änderung an Kandidat, Parametern oder Gates.

## Unverändert

- Kandidat und 50/50-Sleeve-Gewichte;
- Trend-Regel;
- Cross-Sectional-Regel;
- Point-in-Time-Semantik;
- Kosten-/Turnover-Modell;
- bestehende immutable Daten- und Ergebnisartefakte;
- Research/Holdout-Grenze;
- keine Optimierung;
- keine Asset-Auswahl;
- keine Parameter- oder Schwellenwertsuche;
- keine Gate- oder Produktionsänderung;
- keine neuen Daten-Downloads;
- Paper-only, keine Orders.

## Erwartete Nutzung des Ergebnisses

Nur bei einem replizierten Befund darf daraus anschließend eine separat präregistrierte,
eng definierte Architekturhypothese für einen neuen, vollständig symbol-disjunkten
Validierungssatz abgeleitet werden. Der Holdout dieser vier Datensätze bleibt für diese
Entscheidung ausgeschlossen.

## Sicherheitsvertrag

`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`; Orders sind nicht aktiviert.
