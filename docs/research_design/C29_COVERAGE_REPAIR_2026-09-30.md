# C29 Coverage Repair Successor — 2026-09-30

Der ursprüngliche Trial `T-2026-09-30-C29-COVERAGE-PIT` wurde nicht als Forschungs- oder
Performanceergebnis gewertet. Sein Preflight stoppte korrekt vor Datenerfassung, weil das
fixierte Universum mit dem später registrierten C29R1-Reparaturuniversum überlappte.

Dieser Successor ist daher ein neuer Coverage/PIT-Vertrag mit eigener Trial-ID:
`T-2026-09-30-C29-COVERAGE-PIT-R1`.

Das neue Universum (`ROP,NVR,ODFL,CPRT,FICO,AOS,ECL,VRSN`) wurde ausschließlich aufgrund
der maschinell festgestellten Symbol-Disjointness gewählt; Performancewerte oder Holdout
Informationen werden dafür nicht verwendet.

Der Successor darf Coverage und PIT validieren, aber keine Performance, Holdout-Auswahl,
Parameter-/Asset-/Threshold-/Horizon-Suche, Promotion oder Live-Ausführung auslösen.

Erfolgskette:
Repair pre-registration → Coverage → PIT mutation → separate future performance authorization.

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
