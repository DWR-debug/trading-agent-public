# Third Validation Failure-/Risk-Diagnose — 2026-09-23

Die dritte vollständig disjunkte Candidate-Validation ist technisch erfolgreich abgeschlossen, aber der unveränderte Kandidat bleibt BLOCKED. Dieser Control untersucht ausschließlich die Ursache der wiederkehrenden Risiko-/Rolling-Failure-Struktur.

## Quelle

- Workflow-Run: 35851876264
- Artifact: 10745697729
- Artifact-Digest: sha256:b6a408b41abb218d285e06af4b91f66da3ed4ce431aef72907ca5873ffa2c731
- Report-Fingerprint: ab8687cdca2333bbe1842cd2f128e541456fa0dd78982a126c937bd21a655ee6

## Fixe Analyse

- unveränderte 50/50-Sleeve-Gewichte
- unverändertes 10%-Vol-Budget
- Trend: SMA 50/200 + inverse Volatilitätsgewichtung
- Cross-Sectional: 12-1, 252/21/21, Top-2 Long-only
- identische Point-in-Time-/Open-to-Open-Semantik
- keine Parameter-, Signal-, Sleeve-, Asset- oder Gate-Änderung

## Analyseebenen

- fünf feste Research-Fenster
- Portfolio-, Trend- und Cross-Sectional-Return / DD / PF
- Sleeve-Korrelation
- Median- und Minimum-Vol-Budget-Skalierung
- kumulierte Asset-Beiträge je Fenster
- exakte Maximum-Drawdown-Phase

Die Interpretation wird aus den gemessenen Daten abgeleitet und nicht vorab als Cross-Sectional- oder Trend-Failure festgeschrieben.

## Forschungsregel

Auch ein positiver Holdout ersetzt keine Risiko-/Rolling-Gates. Ein möglicher Interventionsentwurf ist erst nach dieser Ursachenanalyse und als separate, vorab festgelegte Hypothese zulässig.

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine echte Orderausführung