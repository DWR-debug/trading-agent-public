# Research Hypothesis Radar — 2026-09-24

Dieses Dokument trennt mutige Hypothesengenerierung ausdrücklich von Evidenz.

## H1 — Cross-Asset Network Momentum / Trend Spillover

Klasse: RESEARCH_HYPOTHESIS

Idee: Die eigene Trendrichtung eines Assets wird durch ein fest definiertes, aus anderen Assets
abgeleitetes Lead-Lag-/Trend-Signal bestätigt oder verworfen. Das ist eine neue Informationsgeometrie
gegenüber einem reinen Eigenpreis-Trend.

Motivation: Li & Ferreira (2025) untersuchen Network Momentum aus Lead-Lag-Beziehungen zwischen
Commodity-Märkten und berichten Verbesserungen gegenüber univariatem Trend-Following.
Quelle: arXiv:2501.07135.

Hauptprüfung: incremental value gegenüber dem bestehenden Trend-Sleeve; keine Parameter-Suche.

## H2 — Trend-Signal-Variabilität

Klasse: RESEARCH_HYPOTHESIS

Idee: Nicht die Mehrheitsrichtung selbst, sondern die Streuung/Variabilität mehrerer bereits
fest definierter Trend-Signale könnte zusätzliche Information tragen. Das unterscheidet sich
von T027s Majority-Vote-Familienersatz.

Motivation: Declerck & Vy (2024) berichten Information in der Variabilität binärer Cross-Asset-
Trend-Signale. Quelle: SSRN 5032806.

## H3 — Echter Carry-Conditioned Trend State

Klasse: RESEARCH_HYPOTHESIS + DATA_REQUIREMENT

Idee: Trend-Exposition wird durch einen fest definierten Carry-Zustand des jeweiligen Marktes
bedingt, statt Carry einfach als zusätzlichen Returnfaktor zu behandeln.

Motivation: aktuelle Arbeiten dokumentieren Carry-Premia und deren ausgeprägte Crash-/Tail-Abhängigkeit.
Quellen: Gouws (2026), SSRN 6978300; Castro et al. (2025), SSRN 5047797.

Datenblocker: Die bestehende Yahoo-Daily-OHLC-Pipeline liefert kein allgemein definiertes,
reproduzierbares Futures-Curve- oder FX-Forward-Carry-Maß. Eine reine ETF-Return-Proxy wird
nicht als echte Carry-Variable bezeichnet.

## H4 — Equity/Bond State Transmission

Klasse: RESEARCH_HYPOTHESIS

Idee: feste Equity/Bond-Cross-Asset-Information als Zustandsvariable für die jeweils andere
Richtung, ohne daraus ein allgemeines Cash-Gate zu machen.

Motivation: aktuelle Cross-Asset-Momentum-Forschung findet ökonomisch relevante Timing-Komponenten,
während andere Befunde den Zusatznutzen nach Kontrolle der Net Exposure begrenzen.

## Auswahlregel

Der unmittelbar nächste formale Schritt bleibt T035 Family-Level WFO. Erst nach dessen Archivierung
wird eine neue Hypothese gewählt.

H1 ist derzeit der interessanteste konzeptionelle Kandidat, nicht ein validierter Gewinner.
H3 bleibt strategisch relevant, ist aber zunächst ein Datenproblem.

## Anti-Selbsttäuschungsregel

„Neu“ oder „ungewöhnlich“ ist keine Evidenz. Jede Hypothese braucht:
Datenvertrag -> Disjointness -> Präregistrierung -> blindes Holdout -> Rolling/WFO -> Kostenstress
-> Ausführbarkeitsprüfung -> formale Gates.

Keine Idee aus diesem Radar erhält dadurch Produktionsstatus.
