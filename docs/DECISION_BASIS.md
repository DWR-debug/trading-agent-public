## Aktueller Stand

### Was wissen wir?

- Die technische Referenz ist ausschließlich der öffentliche `master` von `DWR-debug/trading-agent-public`.
- Q020 / `T-2026-09-26-046R1-PERFORMANCE` wurde auf dem eingefrorenen, symbol-disjunkten Snapshot formal ausgeführt und als `NO_PROMOTION_EVIDENCE` abgeschlossen. Das Ergebnis bleibt unverändert; es gab keine Promotion und keine Live-Ausführung.
- Q021 wurde als `COMPLETED_DIAGNOSTIC_ONLY` aus der kanonischen Q019/Q020-Evidence durchgeführt und liefert sechs ungerankte Folgehypothesen.
- Q023 hat die offizielle Treasury-Resultat-Timestamp-Frage für 89/89 Events nicht vollständig historisch lösbar gemacht (Q024 = `DATA_INSUFFICIENT`); Q025 hat dagegen die Date-Level-PIT-Grundlage für 89/89 Events validiert.
- Q026 (`T-2026-09-27-048`) ist `DATA_INVALID / NO_SCIENTIFIC_OUTCOME`: die bereits eingefrorene Anforderung verlangte 4.000 Candles, während das feste Universum 3.704 gemeinsame Sessions lieferte. Es wurde keine Performance berechnet.
- T047R1 ist geschlossen und bleibt `NO_PROMOTION_EVIDENCE`; die exakte Richtungsinvertierung wurde nicht weiter optimiert.

### Was wissen wir nicht?

- Ob eine orthogonale, ex ante fixierte Hypothesenfamilie auf einem neuen, symbol-disjunkten Datensatz die unveränderten Evidence-Gates erfüllt.
- Ob die Q026-H2-Fragestellung in einer neuen, sauber präregistrierten Geometrie reproduzierbar testbar ist.
- Ob der bestehende Agent bereits einen vollständigen paper-only Forward-/Shadow-Lifecycle besitzt oder der neue Shadow-Harness ergänzt werden muss.

### Was ändert sich?

Die Forschung öffnet Q020 und T047R1 nicht erneut. Stattdessen laufen Exploration, Infrastruktur und Validierung parallel:
1. unrankter Hypothesenentwurf,
2. paper-only Shadow/Forward-Infrastruktur,
3. anschließend ein neuer, ex ante fixierter und coverage-first geprüfter formaler Kandidat.

### Nächste Aktion

AGENT-008 und AGENT-012 parallel ausführen; danach einen einzelnen formal präregistrierten Kandidaten auf einem frischen, symbol-disjunkten Universum durch Coverage/PIT und erst anschließend Performance prüfen.

### Welche Schutzgrenzen bleiben unverändert?

- `PAPER_ONLY=True`
- `LIVE_TRADING_ENABLED=False`
- `orders_enabled=False`
- `automatic_promotion=False`
- Holdout bleibt für Auswahl unberührt.
- Keine nachträgliche Parameter-, Asset-, Feature-, Horizon-, Threshold- oder Varianten-Selektion.
- Dringlichkeit erhöht Geschwindigkeit und Parallelisierung, niemals Evidenzstandard oder finanzielles Risiko.

## Q018 Source-Feasibility abgeschlossen — 2026-09-26

Q018 ist als Source-Feasibility-Gate abgeschlossen.

- Workflow: `36237329691`
- Artifact: `10904273903`
- Artifact-Digest: `sha256:f8bfe4e1065d3d8a8b82b08fe4f78f6bd3c006bedf71c8cadc4f512d8d308989`
- Result-Fingerprint: `82b07265b29a93547f2b1547227722005cf9d883baf3ee8b6dc50e029742152d`
- Gesamtstatus: `DATA_INSUFFICIENT`
- SEC Form 4: `DATA_INSUFFICIENT` — HTTP 403 aus GitHub Actions.
- FOMC: `DATA_INSUFFICIENT` — HTTP 403 aus GitHub Actions.
- Treasury 10-Year Auction Data: `COVERAGE_VALIDATED`.
- Keine Performanceauswertung, kein Holdout, keine Kandidatenrangfolge, kein Tuning.

Die SEC/Fed-Befunde sind Ausführungs-/Zugriffsprobleme des aktuellen kostenlosen Runners; sie sind keine Behauptung, dass die offiziellen Quellen selbst nicht existieren.

### Nächste Aktion

Q019 — Treasury Auction Signal Contract. Die einzige source-feasible Q018-Familie wird jetzt objektiv auf Signal-Parsing, Point-in-Time-Mapping und deterministische Ereignisabdeckung geprüft. Das ist kein Performance-Trial und keine nachträgliche Optimierung.

## Q019 abgeschlossen / Q020 präregistriert — 2026-09-26

Q019 hat den präregistrierten Treasury-10Y-Signal-/PIT-Vertrag erfolgreich bestanden.

- Workflow: `36238205065`
- Artifact: `10905325799`
- Artifact-Digest: `sha256:0e2ec08566b3300b577bb23a1f238b577e3083d0e8985c7466e748310b456325`
- Result-Fingerprint: `13072dbed7d60684f4a4fb8a3de69555cae83c66f3cfdfb603b9ed2a4b1c225b`
- 89/89 Rohzeilen validiert
- 89/89 Events auf den ersten folgenden XNYS-Handelstag gemappt
- 0 terminal events, 0 Fehler
- 88 abgeleitete Signale
- keine Performanceauswertung, kein Holdout, kein Tuning, keine Promotion

### Was bedeutet das für Performance-Evidenz?

Wir haben aus T041/T044/T045 reale Performance-Messungen, aber deren präregistrierte Evidence-Gates wurden nicht bestanden. Das ist etwas anderes als „keine Daten“. Q019 selbst durfte aufgrund seiner Präregistrierung überhaupt keine Performance berechnen.

Damit existiert für den Treasury-Mechanismus bisher weder ein positiver noch ein negativer Performance-Nachweis. Es existiert jetzt jedoch ein sauberer Daten-/Signal-/PIT-Vertrag, auf dessen Basis eine eigenständige Performanceprüfung zulässig ist.

### Q020 — Treasury Auction Performance Design

Q020 ist jetzt `PREREGISTERED_DESIGN_ONLY` und verwendet ein neues vollständig symbol-disjunktes Universum:
`ACN, AMT, APD, BK, CME, CTAS, GPC, LLY, MCO, NOC, ROST, SHW`.

Die Trading-Regel ist vorab fixiert: erster XNYS-Tag nach `record_date`, Signal +1 = gleichgewichtete Long-Position, −1 = gleichgewichtete Short-Position, 0 = flat; ein Event-Tag lang; 1,0x Gross Exposure; kein Leverage. Alle zentralen Risiko-, Kosten-, Rolling-, OOS- und Holdout-Gates bleiben unverändert.

**Nächste Aktion:** zuerst frische OHLCV-Coverage auf diesem Universum. Erst bei Coverage-Pass wird der Snapshot eingefroren und eine formale Performance-Ausführung autorisiert.

Sicherheitszustand bleibt unverändert:
`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`, `automatic_promotion=False`.

## Q020 Coverage Repair bestanden — 2026-09-26

Der Coverage-only Repair-Successor `T-2026-09-26-046R1` hat den Datenvertrag erfolgreich bestanden.

- Workflow: `36240853419`
- Artifact: `10905489440`
- Artifact-Digest: `sha256:f0c5066b879cdc391263e57535ec1e72badbbddfc9c46f27ced51d491c3240a0`
- 12/12 Symbole verfügbar: `ACN, AMT, APD, TGT, CME, CTAS, GPC, LLY, MCO, NOC, ROST, SHW`
- 3.704 gemeinsame Handelstage
- eingefrorenes gemeinsames Fenster: 3.500 Candles
- Snapshot-Fingerprint: `70cff5df1b92f4f7db2ea09bdc9999abff93dd4230ad4ea5df6e5da204076ef8`
- Coverage-Fingerprint: `703f9fb9d1cd21618d0acdcbe8dff3267c99b91afb6841d7110eb09a93f04600`
- Performance: nicht ausgeführt
- Holdout: nicht verwendet
- Selection: nicht verwendet
- Promotion: nicht erfolgt

Die technische Reparatur blieb auf Coverage beschränkt. `BK` wurde durch `TGT` ersetzt, weil `BK` im initialen Yahoo-Lauf technisch nicht ladbar war; die Ersetzung wurde nicht anhand von Performance ausgewählt. Die erhöhte Roh-Anforderungszahl von 4.000 ist nun ausdrücklich als Acquisition Headroom von der Mindestabdeckung von 3.500 getrennt.

### Nächste Aktion

Separate, unveränderliche Q020-Performance-Autorisierung erstellen, die exakt an diesen eingefrorenen Snapshot gebunden ist. Erst danach darf die bereits präregistrierte Fixed-Rule-Performance-Ausführung starten.

Sicherheitszustand bleibt unverändert:
`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`, `automatic_promotion=False`.
