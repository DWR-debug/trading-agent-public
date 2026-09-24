# Risk-Layer EWMA(0.94) — Pre-Registration 2026-09-24

## Motivation

Die Vierfach-Regime-/Sleeve-Diagnose zeigt keinen universellen Single-Sleeve-
Verursacher. Gleichzeitig ist die Volatilitäts-/Risk-Layer-Frage weiterhin
offen. Eine etablierte Alternative zur einfachen gleichgewichteten historischen
Volatilität ist eine exponentiell gewichtete Volatilität.

RiskMetrics dokumentiert für die tägliche Volatilitätsprognose explizit
EWMA mit Zerfallsfaktor lambda = 0,94. Die Methode gewichtet jüngere Renditen
stärker und ist damit konzeptionell auf schnell wechselnde Volatilität
ausgerichtet. Quelle: J.P. Morgan/Reuters RiskMetrics Technical Document,
Fourth Edition (1996), Chapter 5; siehe auch MSCI-Archiv.

- https://www.msci.com/documents/10199/5915b101-4206-4ba0-aee2-3449d5c7e95a
- https://www.msci.com/research-and-insights/paper/1996-riskmetrics-technical-document

## Präregistrierte Einzelintervention

- Control: bestehende 63-Session-Stichprobenvolatilität
- Intervention: RiskMetrics-style EWMA-Varianz mit lambda = 0,94
- Jahresziel: unverändert 10%
- Annualisierung: sqrt(252)
- Zero-mean-Tagesrenditen wie im RiskMetrics-Ansatz
- Warm-up: 63 beobachtete unskalierte Portfolio-Returns
- danach rekursive EWMA-Aktualisierung

Es gibt **keinen lambda-Suchlauf**. 0,94 wird ausschließlich als extern
dokumentierter Tageswert verwendet und nicht aus unseren Daten geschätzt.

## Unverändert

- Fixed Candidate
- Trend-/Cross-Sectional-Signale
- 50/50 Sleeve-Gewichte
- PIT-Semantik
- Kostenmodell
- De-Risk-only Verhalten
- bestehende Research-Gates
- vier vollständig symbol-disjunkte Validierungsfamilien
- fünf Research-Rolling-Fenster je Familie

## Daten- und Entscheidungsgrenze

Es werden nur die vier bereits archivierten, vollständig unabhängigen
Validierungsartefakte verwendet: 20 Research-Fenster und 2.798 Research-
Returns je Familie.

Der 700-Return-Holdout wird weder berichtet noch für irgendeine Auswahl oder
Entscheidung verwendet.

## Erfolgskriterien

Timing gilt nur dann als repliziert verbessert, wenn beide Kriterien in mindestens
3 von 4 Datensätzen besser werden:

1. Rapid-Delayed-or-Never-Rate sinkt.
2. Rapid-Onset-Active-Rate steigt.

Zusätzlich müssen in mindestens 3 von 4 Datensätzen Research-Drawdown und
Research-Rolling-PF nicht schlechter sein als beim 63-Session-Control.

Entscheidungsregel:

- alle Bedingungen >=3/4: fünfte unabhängige Validierung mit exakt EWMA(0,94)
- Timing >=3/4, aber Risiko nicht ausreichend: Trade-off; keine fünfte Validierung
- Timing nicht >=3/4: Hypothese nicht unterstützt

Keine nachträgliche Änderung von lambda, Warm-up oder Erfolgsschwellen.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Orders
- keine Produktionsänderung