# Q015 Information-Alpha Mechanism Discrimination — 2026-09-25

Q015 ist eine rein diagnostische Anschlussstudie zu Q014. Sie untersucht nicht die Profitabilität
einer Handelsregel, sondern die Frage, ob die bereits vorab festgelegten GDELT-Mechanismusgruppen
im selben historischen Datensatz inkrementelle Information enthalten.

## Wissenschaftlicher Ausgangspunkt

Q014 bestätigte über das gesamte feste Jahr 2025-09-25 bis 2026-09-24 eine starke Redundanz der
vier Intensitäts-/Breitenmerkmale und eine deutlich geringere Redundanz von Tone gegenüber dieser
Familie. Die Return-Assoziationen blieben jedoch nach Asset und Horizont gemischt und sind rein
deskriptiv.

Der zuvor eingesetzte untergeordnete Hypothesen-Agent lieferte mehrere konkurrierende Erklärungen
und hob insbesondere Mechanismus-Diskrimination als getrennte Forschungsfrage hervor. Sein Output
wurde ausdrücklich als IDEAS_ONLY / NOT_EVIDENCE behandelt. Keine Hypothese wurde aufgrund eines
Holdouts ausgewählt.

## Präregistrierter Mechanismusraum

- intensity_breadth: event_count, attention_score, source_breadth, article_count
- severity: negative_goldstein
- tone: mean_tone

Alle sechs Features bleiben fixiert. Innerhalb von intensity_breadth erfolgt keine Auswahl.

## Verfahren

Nur Event-Fenster werden analysiert. Für jeden der sechs festen Zellen aus
SPY/TLT/GLD × Next-Day/Five-Day wird:

1. jeder Prädiktor und die Zielrendite innerhalb der Zelle in Midranks transformiert;
2. für jede der acht möglichen Gruppen-Teilmengen ein OLS-Modell mit Intercept berechnet;
3. die R²-Beiträge der drei Mechanismusgruppen symmetrisch über alle sechs Gruppen-Reihenfolgen
   mittels exakter Shapley-Zerlegung aufgeteilt.

Damit hängt der Gruppenbeitrag nicht von einer künstlich gewählten Eintrittsreihenfolge ab.

## Datenvertrag

- exakt Q014-Zeitfenster: 2025-09-25 bis 2026-09-24
- exakt Q014-GDELT-Chunks aus Workflow 36158184847
- mindestens 80 gemeinsame Marktbeobachtungen
- mindestens 40 Event-Fenster
- mindestens 40 vollständige Event-Beobachtungen je Asset/Horizont-Zelle
- keine Holdout-, Feature-, Asset-, Horizon- oder Parametersuche
- keine Performancefreigabe, keine Gateänderung, keine Produktion

Die Marktpreise werden einmal aus Yahoo Finance adjusted daily close für das feste Zeitfenster geladen
und als Q015-Input unveränderlich eingefroren. Der Input erhält einen eigenen SHA-256-Fingerprint.

## Interpretation

Q015 liefert eine strukturierte Mechanismusdiagnose, keinen Trading-Nachweis. Ein Ergebnis darf keine
beste Gruppe auswählen und nicht unmittelbar in eine Handelsregel übersetzt werden.

Eine spätere Performancehypothese benötigt eine neue Präregistrierung, ein frisches
symbol-disjunktes Universum, unveränderte Evidence-Gates und eine vorab fixierte Handelsregel.

## Sicherheit

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
