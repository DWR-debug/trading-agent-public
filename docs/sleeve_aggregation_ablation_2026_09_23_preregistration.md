# Sleeve-Aggregations-Ablation — Pre-Registration 2026-09-23

## Forschungsfrage

Ist die feste 50/50-Aggregation aus Trend-Sleeve und Cross-Sectional-Sleeve selbst
ein wiederkehrender Treiber der beobachteten Research-Risiko-/Rolling-Failures?

Die Untersuchung ist eine Research-Ablation, keine Produktionsänderung.

## Vorab festgelegte Varianten

- Trend-only: 100% Trend / 0% Cross-Sectional
- Current mix: 50% Trend / 50% Cross-Sectional
- Cross-Sectional-only: 0% Trend / 100% Cross-Sectional

Keine weiteren Gewichtsvarianten werden getestet.

## Datenbasis

Es werden ausschließlich die bereits abgeschlossenen vier unabhängigen
Validierungsartefakte verwendet:

- Run 35865847394 / Artifact 10751817990
- Run 35839443616 / Artifact 10740188093
- Run 35851876264 / Artifact 10745697729
- Run 35867637587 / Artifact 10753545703

Die zugrunde liegenden 13+13? nein: 13 Symbole je? werden nicht neu ausgewählt,
ersetzt oder nach Ergebnissen gefiltert. Die vier vorhandenen Universen bleiben
unverändert.

## Auswertungsgrenze

Nur die jeweils vorab definierten 2.798 Research-Returns werden für alle
Vergleiche und Entscheidungen verwendet.

Der 700-Return-Holdout wird nicht als Kennzahl ausgegeben und nicht in die
Entscheidungsregel einbezogen. Es erfolgt keine Re-Evaluation des Holdouts.

## Unveränderte Rechenlogik

- Trend: SMA 50/200, inverse Volatilitätsgewichtung
- Cross-Sectional: 12-1 Momentum, 252 Sessions Formation, 21 Sessions Skip,
  21 Sessions Rebalancing, Top-2 Long-only
- identische Point-in-Time-Semantik
- 10% annualisiertes Realized-Volatility-Budget über 63 Sessions,
  ausschließlich De-Risking
- Base-Kosten sowie 1,5x- und 2x-Kostenstress
- identische Daten-/Manifest-/Fingerprint-Prüfungen
- keine Parameteroptimierung
- keine Gate-Änderung
- keine Production-Integration
- keine Orders

## Vorab definierte Kontrastregel

Für die Base-Kosten wird je Validierungssatz ausschließlich aus Research-Metriken
gezählt:

1. Trend-only dominiert die 50/50-Mischung, wenn es sowohl geringeren Research-
   Drawdown als auch höheren Research-Rolling-Profit-Factor aufweist und
   mindestens ein Unterschied strikt ist.
2. Cross-Sectional-only dominiert analog.
3. Der 50/50-Mix gilt als Aggregations-Risiko-Kontrast, wenn er gleichzeitig
   höheren Research-Drawdown und niedrigeren Research-Rolling-PF als beide
   Single-Sleeve-Kontrollen aufweist.

Eine dieser Aussagen wird nur dann als replizierter Kontrast klassifiziert, wenn
sie in mindestens 3 von 4 unabhängigen Validierungssätzen erfüllt ist.

## Konsequenzregel

- Wird eine einzelne Sleeve in mindestens 3/4 Sätzen gegenüber 50/50 auf beiden
  Research-Risikokriterien dominant, wird daraus ausschließlich eine neue,
  separat präregistrierte Research-Validierung dieser festen Sleeve-Architektur
  auf einem fünften, neuen symbol-disjunkten Datensatz abgeleitet.
- Wird stattdessen der 50/50-Mix in mindestens 3/4 Sätzen von beiden
  Single-Sleeves auf beiden Kriterien dominiert, wird als nächste Forschungsfrage
  eine separat präregistrierte Aggregationsregel untersucht.
- Trifft keine Regel zu, gilt der Befund als kein universeller
  Aggregationskontrast; es erfolgt keine Gewichts-/Parameteroptimierung.

Diese Konsequenzregeln verwenden ausschließlich Research-Daten. Eine
Holdout-basierte Auswahl oder Bestätigung findet nicht statt.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Live-Ausführung
- keine Produktionsänderung
