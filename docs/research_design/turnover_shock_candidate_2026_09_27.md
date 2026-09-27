# Turnover-Shock Continuation Candidate — Coverage-First Design

Stand: 2026-09-27  
Präregistrierung: `research/preregistrations/turnover_shock_candidate_2026_09_27.json`  
Status: **Design und Coverage/PIT-Engineering; kein Performance-Trial**

## Hypothese und feste Regel

Ein außergewöhnlich hoher abgeschlossener Tagesumsatz kann auf Informationszufluss
oder vorübergehenden Liquiditätsbedarf hinweisen. Untersucht werden soll ausschließlich
die Post-Shock-Price-Formation/Continuation-Richtung; eine Reversion-Alternative wird
nicht gesucht.

- Signal: aktueller abgeschlossener Tagesbalken.
- `turnover_proxy = close * volume`.
- Referenz: Median der vorherigen 20 abgeschlossenen Tagesbalken.
- Schock: `turnover_proxy / reference >= 2.0`.
- Richtung: long am ersten folgenden XNYS-Handelstag.
- Haltedauer: genau ein XNYS-Handelstag; Bruttoexposure 1.0x.
- Universum: AFL, ALL, AVY, CAH, CINF, CPRT, OXY, PPG, ROP, TROW, TRV, WMB.

Es gibt keine alternativen Schwellen, Referenzfenster, Richtungen, Horizonte,
Leverage- oder Universumsvarianten.

## Coverage- und PIT-Preflight

`automation/turnover_shock_coverage.py` liest ausschließlich die feste
Präregistrierung und verwendet `data.canonical_snapshot.build_frozen_snapshot`,
`data.yahoo_loader.load_yahoo_history` sowie den XNYS-Kalender. Der Coverage-Zeitraum
2011-01-01 bis 2026-09-25, die Anforderung von 4.000 angefragten Balken und 3.500
gemeinsamen Balken sind feste technische Coverage-Geometrie, keine getesteten
Signalparameter oder Performance-/Holdout-Partition.

Der Preflight prüft die fixierte Symbolmenge, vollständige gemeinsame tägliche
XNYS-Sitzungen, positive endliche Schlusskurse und Volumina sowie die Zuordnung jedes
Balkentags zum strikt folgenden XNYS-Handelstag. Er berechnet **keine Schocks,
Signale, Renditen, P&L oder Performancekennzahlen**. Bei Erfolg wird der kanonische
Snapshot vor einer möglichen, separat autorisierten Performance-Studie eingefroren;
Manifest und Datensatz-Fingerprints bleiben Teil der Provenienz. Yahoo stellt für
diese historischen Balken keine Quelleintage bereit. Deshalb liefert der Runner
trotz erfolgreicher Kalender-/Snapshot-Prüfung `DATA_INSUFFICIENT`; die PIT-Daten-
Provenienz ist nicht vollständig reproduzierbar. Ein Snapshot-Fingerprint allein
hebt diese Lücke nicht auf.

Aufruf:

```sh
python -m automation.turnover_shock_coverage
```

Das Ergebnis wird unter `research/runs/turnover_shock_coverage/` abgelegt.
`COVERAGE_VALIDATED` wäre ausschließlich ein Daten-/Kalenderbefund und keine
Performance-Evidenz oder Autorisierung. Mit der derzeit festgelegten Yahoo-Quelle
ist der formale PIT-Gate nicht erfüllbar, solange die Quelle keine Quelleintage
bereitstellt; der Runner stoppt daher mit `DATA_INSUFFICIENT`, auch wenn die übrigen
Coverage-Prüfungen erfolgreich sind. Unvollständige Abdeckung ergibt ebenfalls
`DATA_INSUFFICIENT`; strukturelle Daten- oder PIT-Vertragsverletzungen ergeben
`DATA_INVALID`. In allen Fällen wird Performance gestoppt.

## Grenzen und nächste Freigabe

Es werden keine Holdouts ausgewählt, keine vorhandenen Gates geändert und keine
Research- oder Promotionsentscheidung getroffen. Kein Backtest, keine Live-Ausführung
und keine Order sind Teil dieses Auftrags. Ein möglicher Performance-Trial benötigt
eine eigenständige Präregistrierung und Genehmigung; Agentenoutput und Coverage-Pass
allein sind keine wissenschaftliche Evidenz.

Sicherheit: `PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`,
`orders_enabled=False`, `automatic_promotion=False`.
