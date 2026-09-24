# Vierfach-Regime-/Sleeve-Interaktionsdiagnose — Ergebnis 2026-09-23

## Befund

Die negative Research-Portfolioperformance tritt in nur 6 von 20 festen
Research-Rolling-Fenstern auf. Die sechs negativen Fenster verteilen sich auf
3 gemeinsame Sleeve-Schwächen, 1 reine Trend-Schwäche und 2 reine
Cross-Sectional-Schwächen.

| Größe | Befund |
|---|---:|
| negative Portfolio-Fenster | 6/20 |
| gemeinsame Sleeve-Schwäche | 3/6 = 50,0% |
| reine Trend-Schwäche | 1/6 = 16,7% |
| reine Cross-Sectional-Schwäche | 2/6 = 33,3% |
| mittlerer De-Risk-Anteil in negativen Fenstern | 81,08% |
| mittlerer De-Risk-Anteil in positiven Fenstern | 49,05% |
| mittlere Sleeve-Renditekorrelation in negativen Fenstern | 0,608 |

Die negativen Fenster sind damit nicht universell einer einzelnen Sleeve
zuzuordnen. In der Hälfte der negativen Fenster sind beide Sleeves zugleich
negativ; die andere Hälfte verteilt sich auf jeweils einseitige Schwäche.

Bemerkenswert ist der deutlich höhere De-Risk-Anteil in negativen Fenstern
(81,08% gegenüber 49,05% in positiven Fenstern). Das ist jedoch rein
deskriptiv und beweist keine Ursache. Die De-Risking-Skalierung kann eine
Reaktion auf die bereits eingetretene Verschlechterung sein.

## Einordnung

Der Befund begrenzt die Interpretation des bisherigen Robustheitsproblems:
Es gibt keinen replizierten universellen Single-Sleeve-Verursacher und keinen
eindeutigen Nachweis, dass die Risk Layer allein die negativen Fenster
erzeugt.

Die externe Literatur stützt zugleich die Trennung von Volatilitätsmessung
und Zustands-/Regimeerkennung: aktuelle Arbeiten finden Vorteile von
Regime-Switching-Modellen bei der Volatilitätsprognose, weisen aber darauf hin,
dass die tägliche Out-of-Sample-Überlegenheit nicht in jedem Setting eindeutig
ist. Ein einfacher 63-Tage-Schätzer sollte daher nicht ohne Kontrolle durch
eine komplexere Zustandslogik ersetzt werden.

Quellen:
- Ding, Kambouroudis & McMillan (2025), Forecasting realised volatility using regime-switching models, doi:10.1016/j.iref.2025.104171.
- Moreira & Muir (2017), Volatility-Managed Portfolios, Journal of Finance 72(4), 1611–1644, doi:10.1111/jofi.12513.

## Konsequenz für das Projekt

Keine Änderung an Sleeve-Gewichten, Parametern, Gates oder Produktionslogik.

Der nächste Forschungsschritt wird auf die Frage fokussiert, ob eine
literaturbasierte, fest definierte Volatilitätsprognose die bestehende
63-Session-Schätzung informativer ersetzt. Dafür wird ausschließlich der
Research-Teil der vier bestehenden unabhängigen Validierungen verwendet.

## Provenienz

- PR #53: Research: four-set portfolio regime and sleeve interaction diagnosis
- Run: 35873900569
- Artifact: 10756691469
- Artifact-Digest: sha256:dc33243914e0f356f8b073062f2d25b818fcbb30ac868086aade4571bda21037
- Diagnostic-Fingerprint: 0c201d027ea8ae4b4a2daf39d834820f92638b2bb53d1b2c898e021974716955
- vollständige Testsuite: bestanden
- ARM64 Research Smoke: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- Holdout nicht berichtet oder zur Entscheidung verwendet