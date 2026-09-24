# Risk-Layer EWMA(0,94) — Ergebnis 2026-09-24

## Fragestellung

Geprüft wurde ein einzelner, extern fixierter Volatilitäts-Forecast-Control:
RiskMetrics-style EWMA mit lambda=0,94 gegen die bestehende 63-Session-
Stichprobenvolatilität, jeweils mit demselben 10%-Jahresziel.

Der Control wurde ausschließlich auf den vier immutable, vollständig
symbol-disjunkten Validierungsfamilien im Research ausgeführt.

## Ergebnis

| Validierung | Rapid-Delayed verbessert | Rapid-Onset verbessert | Research-DD nicht schlechter | Rolling-PF nicht schlechter |
|---|---|---|---|---|
| 1 | Nein | Nein | Ja | Nein |
| 2 | Nein | Nein | Ja | Nein |
| 3 | Nein | Nein | Nein | Nein |
| 4 | Ja | Ja | Nein | Nein |

Replikationszahlen:

- Rapid-Delayed-Rate verbessert: **1/4**
- Rapid-Onset-Active-Rate verbessert: **1/4**
- Research-DD nicht schlechter: **2/4**
- Research-Rolling-PF nicht schlechter: **0/4**

Die präregistrierte Timing-Schwelle von mindestens 3/4 wird klar verfehlt.
Zusätzlich verschlechtert sich der Research-Rolling-PF in allen vier
Validierungsfamilien gegenüber dem 63-Session-Control.

## Fachliche Schlussfolgerung

Eine schnellere, exponentiell gewichtete Volatilitätsschätzung allein löst
den replizierten Rapid-Drawdown-Timing-Befund nicht. In diesem Setup führt sie
zugleich nicht zu einem stabileren Rolling-PF.

Das Ergebnis begrenzt damit die Risikomanagement-Hypothese weiter: Weder die
Fensterlänge noch ein schnellerer Standard-Volatilitätsforecast noch ein
direkter Ein-Tages-Shock-Term liefern einen universellen Robustheitsnachweis.

Keine EWMA-Übernahme, kein lambda-Suchlauf und keine fünfte Validierung.

## Nächster Schritt

Statt weitere Volatilitätsschätzer zu testen, wird der bestehende 63-Session-
Risk-Layer selbst auf seine **nachgelagerte Renditeinformation** untersucht:
Wenn De-Risking sinnvoll ist, sollte ein aktiver De-Risk-Zustand auf der
folgenden Periode systematisch andere Returns zeigen als ein vollständig
risikogewichteter Zustand. Das ist eine reine Diagnose und verändert noch keine
Portfolio-Logik.

## Externe Einordnung

Moreira und Muir (2017) dokumentieren Vorteile von Volatility Timing, weil
Volatilitätsanstiege nicht proportional durch erwartete Renditen kompensiert
werden. Der nächste Diagnose-Schritt prüft deshalb, ob dieses notwendige
empirische Verhältnis in unserem Fixed Candidate überhaupt sichtbar ist.

Quelle: Moreira & Muir, Volatility-Managed Portfolios, Journal of Finance
72(4), 1611–1644, doi:10.1111/jofi.12513.

RiskMetrics dokumentiert lambda=0,94 als täglichen EWMA-Zerfallsfaktor.

## Provenienz

- PR #56: Research: fixed EWMA 0.94 risk-layer control
- Run: 35965853227
- Artifact: 10794346460
- Artifact-Digest: sha256:0cc7ab98bf8ba76c1388b0ff7c660f68c7a20dbcef474be703cd1b1b54e2d93a
- Experiment-Fingerprint: 8c64de5123e90aad638899fbbfeca485df8a099c99465fdcd533be896e2e029e
- Volltests: bestanden
- ARM64 Research Smoke: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- Holdout nicht berichtet oder verwendet