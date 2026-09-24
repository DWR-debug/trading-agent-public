### 2t. Open/Close Gap-Reversal — Trial 021 Ergebnis — 2026-09-24

Trial T-2026-09-24-021 wurde auf einem vollständig symbol-disjunkten U.S.-Aktienuniversum vollständig und reproduzierbar ausgeführt. Die Daten-, Safety-, Präregistrations- und Integritätsprüfungen bestanden; der eigentliche Research-/Holdout-Control wurde vollständig gerechnet.

- Workflow-Run: 36010070504
- 8 Assets: JNJ, KO, PG, WMT, XOM, CVX, MCD, PEP
- 3.500 Candles/Asset, 3.498 Returns, Research/Holdout 2.798/700
- vollständige Testsuite: 617 bestanden
- Paper-only, Universums-Disjointness, Präregistrierung und Ergebnisintegrität: bestanden
- Report-Fingerprint: 8af136b92c4c114d16fe6951d609f20939c15c840d9952c878e5de15d9cdb2da
- Code-Commit: 24a47f77306d76b930b81a73e96ed5748d1bf88d

### Fachlicher Befund

Basis-Szenario:

- Research: -99,97% Return, 99,97% Drawdown, PF 0,217
- Research-Rolling: 0/5 profitable Fenster
- Holdout: -88,12% Return, 88,16% Drawdown, PF 0,210
- OOS/Research-Ratio: 0,00
- Gap-Reversal-Edge: Research negativ, Holdout gering positiv
- Turnover: 5.595 Research / 1.399,75 Holdout

Kostenstress verschlechtert den Befund weiter:

- 1,5x Kostenstress: Holdout -95,86%, PF 0,102
- 2x Kostenstress: Holdout -98,56%, PF 0,054

Alle elf präregistrierten Entscheidungschecks werden verfehlt. Insbesondere gibt es keinen positiven Research-/Holdout-Portfolioertrag, keine ausreichende Drawdown-/PF-Stabilität, keine profitable Rolling-Historie, kein OOS/IS-Signal und keine Kostenrobustheit.

### Entscheidung

NO_SUPPORT / archived_rejected.

Der Control wird nicht in die Produktion integriert. Es erfolgt keine Varianten-, Schwellenwert-, Asset- oder Kostenoptimierung innerhalb dieser Research-Familie. Die Gap-Reversal-Familie gilt damit als methodisch geprüft und für weitere direkte Tuning-Versuche geschlossen.

Dauerhafte Evidenzablage:
- docs/open_close_gap_reversal_trial021_result.md
- research/checkpoints/open_close_gap_reversal_trial021_result.json
- research/evidence/trial_ledger.json

Der nächste Forschungsschritt muss eine orthogonale Alpha-Familie prüfen.
