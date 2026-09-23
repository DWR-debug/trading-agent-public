# Parameter-Free Shock Guard — Ergebnis 2026-09-23

## Ergebnis

Die präregistrierte, parameterfreie Shock-Guard-Intervention wurde auf vier
unabhängigen Validierungsfamilien ausschließlich im Research geprüft.

Intervention:
`effective_vol = max(trailing_63_session_realized_vol, abs(previous_unscaled_portfolio_return) * sqrt(252))`

Der 700-Return-Holdout wurde weder berichtet noch zur Entscheidung verwendet.

| Validierung | Rapid-Delayed verbessert | Rapid-Onset verbessert | Research-DD nicht schlechter | Rolling-PF nicht schlechter |
|---|---|---|---|---|
| 1 | Ja | Ja | Nein | Nein |
| 2 | Nein | Nein | Nein | Nein |
| 3 | Nein | Nein | Nein | Nein |
| 4 | Ja | Nein | Nein | Nein |

Replikationszahlen:

- Rapid-Delayed-Rate verbessert: 2/4
- Rapid-Onset-Active-Rate verbessert: 1/4
- Research-DD nicht schlechter: 0/4
- Research-Rolling-PF nicht schlechter: 0/4

Der präregistrierte Erfolg wird damit nicht erreicht. Die Intervention senkt
die Risiko-/Rolling-Qualität nicht nur nicht ausreichend, sondern verschlechtert
sie in allen vier Sätzen bei mindestens einem zentralen Research-Kriterium.

## Fachliche Schlussfolgerung

Die direkte Ein-Tages-Shock-Ergänzung ist kein tragfähiger universeller Ersatz
für die bestehende 63-Session-Risk-Layer. Eine aggressive Reaktion auf einzelne
Vorperioden-Schocks erzeugt in diesem Setup zusätzliche De-Risking-Tage und
verschlechtert dadurch die Research-Rendite-/PF-Struktur.

Keine weitere Shock-Guard-Abstufung, kein frei gewählter Shock-Faktor und keine
Parameteroptimierung werden daraus abgeleitet.

## Aktueller Forschungsfokus

Die verbleibende Aufgabe ist Root-Cause-Diagnose statt weiteres Risk-Layer-Tuning.
Die bestehende Portfolio-Regime-/Sleeve-Interaktionsdiagnose wird deshalb auf
alle vier unabhängigen Validierungsfamilien erweitert.

## Provenienz

- PR #51: Research: parameter-free shock-aware risk-layer ablation
- Run: 35872919840
- Artifact: 10755758939
- Artifact-Digest: sha256:1c68c0426d3fcd8be3c869f681690f0a0c60440ef6b69dd8454960cc535d2225
- Experiment-Fingerprint: ef751b4492a397b54f0d5633e7750df5565c3ba1ba74fb334debff7e40647b05
- Volltests: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- Holdout nicht zur Auswahl verwendet