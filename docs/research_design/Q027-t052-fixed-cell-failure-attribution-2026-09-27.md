# Q027 — T052 Fixed-Cell Failure Attribution

Stand: 2026-09-27

## Zweck

Q027 zerlegt den bereits abgeschlossenen T052-Befund rein diagnostisch.
Es werden die vier ex ante festgelegten Universe/Sleeve-Zellen gemeinsam
betrachtet. Es gibt keine Rangfolge und keine Auswahl.

Quelle ist ausschließlich der unveränderte T052-Resultatdatensatz aus
Workflow 36338219883 / Artifact 10938097809 mit Fingerprint
a0a1dc33ce281e7addcf9cf924881b6a30797c1a744d4160fbff91d3384b1b09.

## Auswertung

Für jede der vier Zellen wird die vollständige Liste der nicht bestandenen
Gates ausgegeben. Zusätzlich wird gezählt, in wie vielen der vier Zellen jedes
Gate versagt.

Die Diagnose beantwortet nur:
- Welche Failure-Gates sind über alle vier Zellen gemeinsam?
- Welche Failure-Gates treten nur in einem Teil der Zellen auf?
- Bleibt die Failure-Signatur zwischen T049 und T050 strukturell ähnlich?

Sie verwendet keine neuen Marktinformationen, keine Parameterwahl und keinen
Holdout zur Auswahl.

## Vorläufige Diagnose aus dem festen Resultat

In der vollständigen Vier-Zellen-Evidence treten fünf Failure-Gates in allen
vier Zellen auf:
- research_drawdown_lte_10pct
- rolling_average_drawdown_lte_10pct
- oos_to_is_return_ratio_gte_0_25
- holdout_profit_factor_gte_1_10
- holdout_drawdown_lte_10pct

Weitere Failure-Gates treten nur in einem Teil der Zellen auf:
- holdout_return_positive: 2/4
- stress_1_5x_holdout_nonnegative: 2/4
- stress_2x_holdout_nonnegative: 2/4
- research_profit_factor_gte_1_10: 2/4
- total_return_sensitivity_holdout_nonnegative: 1/4

Damit ist die unmittelbare Folgefrage nicht die Auswahl einer Zelle, sondern
die mechanistische Erklärung der gemeinsamen Drawdown-, Stabilitäts- und
Holdout-Probleme.

## Nächster zulässiger Schritt

Eine neue Diagnose darf T052 nicht retunen. Der nächste Design-/Forschungsschritt
ist eine mechanistische Attribution auf:
1. Drawdown-Verteilung und Extremphasen,
2. Research-to-Holdout-Regimewechsel,
3. Cross-Sleeve-Gemeinsamkeiten,
4. Kosten-/Sensitivity-Beiträge,
5. Markt-/Sektor-Konzentration innerhalb der fixen Sleeves.

Erst daraus dürfen neue, vollständig ex ante definierte Hypothesen abgeleitet werden.

## Governance

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
