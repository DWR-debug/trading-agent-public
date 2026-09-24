# Post-hoc explorative Diagnose: CS-Reversal-Vorläufer

Diese Diagnose ist ausdrücklich post-hoc explorativ. Sie untersucht auf den vier
bereits vorhandenen immutable Validierungsartefakten, welche Informationen am
Beginn eines Return-Intervalls zwischen späteren CS-Winner-Reversals und
Nicht-Reversal-Perioden unterscheiden.

Verwendet werden ausschließlich 2.798 Research-Perioden je Datensatz.
Holdout wird nicht ausgewertet und nicht für Entscheidungen verwendet.

Vorab festgelegte, zeitlich verfügbare Merkmale:

- relative Open-to-Open-Rendite der aktuell ausgewählten Top-2 über 21 Sessions;
- 21-Session-Cross-Sectional-Dispersion;
- Gap der unveränderten 252/21-Signal-Scores zwischen Top-2 und Nichtgewinnern;
- Position innerhalb des festen 21-Session-Rebalance-Zyklus.

Es werden keine Modelle trainiert, keine Schwellenwerte und keine
Strategie-, Gate- oder Produktionsänderungen vorgenommen.

Die Analyse dient ausschließlich dazu, einen möglichen Vorläufer eines
Reversal-Ereignisses von einer nachträglichen Reaktion zu unterscheiden.


Contract tokens: post-hoc explorativ | 2.798 | Holdout | keine Schwellenwerte | PAPER_ONLY=True
