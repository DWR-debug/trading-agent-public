# Formaler 500-EUR-Kandidatenlauf

## Startbedingung

Ein Kandidat erhält den formalen 500-EUR-Paperlauf erst nach:

1. vollständig abgeschlossenem, frisch symbol-disjunktem Research-/Holdout-Lauf,
2. \`VALIDATED_PASS\`,
3. bestandenen unveränderten Evidence-Gates,
4. \`holdout_used_for_selection == false\`,
5. unverändertem Paper-only-Sicherheitsvertrag.

Danach wird genau ein eingefrorener Kandidat in einen isolierten 30-Tage-Paperlauf mit exakt EUR 500 überführt.

## Vorstufe

Vor dem formalen Gate sind 500-EUR-Engineering-Shadows technisch möglich, aber sie sind reine technische Beobachtung und dürfen keinen wissenschaftlichen Auswahlentscheid begründen.

H06 ist aktuell noch in dieser Vorstufe: die frische Mechanismus-Replikation ist abgeschlossen, ein unabhängiger Performance-/Holdout-Nachweis fehlt noch.

## Verbote

Der formale Lauf darf weder Kandidaten vergleichen noch automatisch auswählen, Parameter verändern, Holdout erneut für Auswahl verwenden, Leverage erhöhen oder Orders erzeugen.

## Laufvertrag

Der vorhandene 30-Tage-Harness wird mit \`--initial-capital-eur 500\` aufgerufen. Checkpoint, Return-Stream, Evidence, Trial-ID und Kapitalbasis werden gemeinsam gefingerprinted.

Safety:

\`PAPER_ONLY=True\`
\`LIVE_TRADING_ENABLED=False\`
\`orders_enabled=False\`
\`automatic_promotion=False\`
