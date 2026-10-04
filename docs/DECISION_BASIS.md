# Trading Agent — Aktuelle Decision Basis

## Kanonischer Nordstern
Unser übergeordnetes Ziel ist die Entwicklung eines wissenschaftlich validierten, reproduzierbaren und risikogesteuerten Trading Agent, der erst nach ausreichender Evidenz und formaler Autorisierung für nachhaltigen realisierten P&L-Cashflow in Betracht kommt, mit variabler Familienunterstützungs-Entnahme, erforderlicher Reinvestition, Kapitalerhalt und vollständiger Auditierbarkeit.
Kanonischer Projektvertrag: research/governance/project_north_star.json.

Stand (UTC): 2026-10-04T10:40:00Z
Technische Code-Basis: 0899b0fbf9f3528411488789caf435b732c8005d
Aktueller Master (docs/governance): aae45cf2dd8d4ff13a91ce3479b867e1c64df982
Repository: DWR-debug/trading-agent-public

## Übergeordnetes Ziel
Entwicklung eines autonomen, risiko- und evidenzgesteuerten Trading Agent, der erst nach ausreichender wissenschaftlicher Validierung für wiederkehrend entnehmbares Einkommen in Betracht kommt.
Priorität: Kapitalerhalt → kontrollierbares Risiko → robuste OOS-/Holdout-Evidenz → Regelmäßigkeit/Planbarkeit → effiziente Rendite → langfristig entnehmbares Einkommen innerhalb der Sicherheitsgrenzen.
Reales verfügbares Kapital: 0 EUR. Referenzkapital: 2.000 EUR ausschließlich simulativ.

## Aktuelle Evidenzgrenze
Der aktuelle formale Stand ist PERFORMANCE_COMPLETED_NO_ARM_PASSED_ALL_13_GATES für T-2026-10-01-H06P2R3-PERFORMANCE-01. Es gibt damit derzeit keinen promotionsfähigen Kandidaten.
H06 besitzt replizierte PIT-/Coverage-Evidenz, aber PIT-Evidenz ist keine Performance- oder Promotion-Autorisierung. Frühere negative und diagnostische Resultate bleiben unverändert und werden nicht nachträglich optimiert.

## Forschungsrichtung
Der wiederkehrende wissenschaftliche Engpass ist Robustheit, nicht bloß Ideendichte. Mehrere Mechanismen haben positive Renditebeiträge gezeigt, erfüllten aber nicht alle unveränderten Risiko-/Robustheitsgates.
Neue Information soll mechanistisch orthogonal sein. Drawdown, Co-Movement, Konzentration und Kosten werden als eigene Forschungsfragen behandelt. Coverage/PIT kommt vor Performance; immutable Reconciliation vor Interpretation; negative Evidenz bleibt erhalten.

## Aktive Forschungsbahnen
Q125-F1: SEC-MIDAS-Publikationsuhr/Vintage-PIT nach dem behobenen Quellpfadfehler.
Q119/Q120/Q122: Treasury-/CFTC-Quellen und historische Veröffentlichungs-/PIT-Semantik.
I22 und Q104 I19/I20: SEC/XBRL/13F-Informationskanäle mit Akzeptanzzeit, Historienabdeckung und Revisionsschutz.
Q124/Q126/Q127/Q128/Q129/Q130: Discovery-/PIT-Feasibility, noch keine Performancefreigabe.
Evidence-Critic: reproduzierbare Model-Metrics-/Runtime-Acceptance.

## Ressourcen
Die bestehende Kapazität ist für den aktuellen Engpass ausreichend: GitHub-hosted deterministische Compute-Lanes, zwei Windows-Self-hosted Research-Lanes, S10 als bounded Utility-Worker und kostenlose AI-Pfade nur bei nachgewiesener Zugänglichkeit.
Weitere Samsung-Geräte werden nur als kontrollierter Kapazitätstest eingebunden; ein messbarer zusätzlicher Forschungsdurchsatz ist Voraussetzung für weitere Geräte.

## Externe Hypothesenquellen
Die aktuelle 2026-Literatur liefert neue, aber unvalidierte Anhaltspunkte zu zustandsabhängiger Predictability, Options-Order-Imbalance/Liquidität, SEC-MIDAS-Marktstruktur und Earnings-Timing. Diese Quellen sind Hypothesen-/Feasibility-Input, keine Evidenz für unseren Agenten.

## Kritischer Forschungsmodus bis 2026-10-25
Die Kandidatensuche priorisiert jetzt ausdrücklich mechanistisch und informationell orthogonale Quellen statt weiterer Varianten bereits ausgeschöpfter Price-only-Momentum-/Trendlinien.
Vor jeder künftigen Performance-Autorisierung muss ein preregistrierter Robustheits-Screen mindestens Rendite, Drawdown, Profit Factor, Rolling-Stabilität, OOS/IS-Verhältnis, Kostenstress, Turnover, Exposure, Konzentration, Markt-Korrelation, Underwater-Anteil und Regime-/Symbolbeiträge sichtbar machen.
Ein vollständiger 13/13-Performance-Pass erzeugt keine Promotion. Er erzeugt stattdessen zwingend die sofortige, unveränderte unabhängige Replikation gemäß vorab festgelegtem Replikationsvertrag. Fehlt dieser Vertrag, fail-closed.
Kanonischer Kontrollvertrag: research/governance/critical_research_quality_control.json.

## Externe Trading-Agent-Prior-Art — 2026-10-04
Die systematische Prüfung öffentlicher Trading-Agent-/Quant-Agent-Ansätze bestätigt mehrere bestehende Architekturentscheidungen und liefert drei konkrete Hardening-Richtungen: (1) agent-facing historische Kontexte strikt cutoff-/PIT-gebunden und bei retrospektiven Agent-Aufgaben optional asset-/datumsblind darstellen, (2) Replay-Parität zwischen Backtest und Paper/Forward über einen gemeinsamen State-/Decision-Vertrag absichern, und (3) ungültige/unlesbare Agent-Entscheidungen explizit als REVIEW_REQUIRED/INVALID quarantänisieren statt stillschweigend als neutrale/HOLD-Ausgabe zu interpretieren. Diese Punkte sind Integritäts-/Engineering-Kontrollen, keine neuen Handelssignale.
Die Referenzsysteme sind `TauricResearch/TradingAgents`, `virattt/ai-hedge-fund`, `microsoft/RD-Agent`, `AI4Finance-Foundation/FinRobot`, `microsoft/qlib`, sowie AlphaAgent/Alpha-GPT/AlphaForge als Alpha-Research-Prior-Art. Externe Performance- oder Promotionsaussagen werden nicht übernommen.

## Nächste Schritte
1. Aktuelle Coverage-/PIT-Feasibility-Gates weiter abarbeiten.
2. Die drei prior-art-basierten Integrity-Hardening-Punkte nur dort implementieren, wo ein bestehender Code-/Task-Vertrag sie ohne semantische Annahmen eindeutig aufnehmen kann; keine speculative Integration.
3. S10 in reale bounded Research-Support-Aufgaben einbinden und den Nutzen per Receipt messen.
4. Orthogonale Kandidaten erst nach dem neuen Robustheits-/Replikationsvertrag in die Performance-Spur überführen.
5. Einen gültigen 13/13-Performance-Lauf immutable reconciliieren und unmittelbar die unabhängige Replikation anstoßen.
6. Zusätzliche Hardware nur bei messbarem Parallelisierungsgewinn.

## Unveränderliche Grenzen
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
Kostenpflichtige Agent-/API-Nutzung bleibt 0 USD. AI-Ausgaben sind keine wissenschaftliche Evidenz und keine Autorisierung.
