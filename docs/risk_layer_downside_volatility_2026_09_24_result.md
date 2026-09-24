# Risk-Layer Downside-Volatility — Ergebnis 2026-09-24

## Forschungsfrage

Geprüft wurde die einzige extern motivierte Risikometrik-Intervention nach dem
4/4-Gegenbefund der Total-Volatility-Folgerendite: 63-Session-Downside-
Volatility statt 63-Session-Total-Volatility bei identischem 10%-Ziel.

Downside-Volatility wurde mit der festen Nullschwelle als
sqrt(mean(r² * I[r<0])) * sqrt(252) berechnet. Es gab keinen Schwellenwert-,
Fenster- oder Definitionssuchlauf.

## Ergebnis

| Validierung | Rapid-Delayed verbessert | Rapid-Onset verbessert | Research-DD nicht schlechter | Rolling-PF nicht schlechter |
|---|---|---|---|---|
| 1 | Nein | Nein | Nein | Ja |
| 2 | Nein | Nein | Nein | Ja |
| 3 | Nein | Nein | Nein | Ja |
| 4 | Nein | Nein | Nein | Ja |

Replikationszahlen:

- Rapid-Delayed-Rate verbessert: **0/4**
- Rapid-Onset-Active-Rate verbessert: **0/4**
- Research-DD nicht schlechter: **0/4**
- Research-Rolling-PF nicht schlechter: **4/4**

Die Intervention verfehlte damit alle Timing- und Drawdown-Kriterien der
Preregistration. Der Rolling-PF war zwar in allen vier Familien etwas höher,
aber das genügt nicht für den vorab definierten Nachweis.

## Größenordnung

| Validierung | Return-Differenz 31? nein: Downside-Volatility minus Total-Volatility | DD-Differenz | Rolling-PF-Differenz |
|---|---:|---:|---:|
| 1 | +9,514 %-Pkt. | +2,067 %-Pkt. | +0,0056 |
| 2 | +7,897 %-Pkt. | +2,596 %-Pkt. | +0,0097 |
| 3 | +9,309 %-Pkt. | +2,596 %-Pkt. | +0,0111 |
| 4 | +21,676 %-Pkt. | +1,978 %-Pkt. | +0,0157 |

Die Downside-Volatility-Variante produziert damit in allen vier Familien
höhere Research-Rendite als der Total-Volatility-Control, aber zugleich auch
höhere maximale Research-Drawdowns. Genau dieser Trade-off verhindert eine
Übernahme.

## Fachliche Schlussfolgerung

Die externe Hypothese von Wang & Yan (2021), dass Downside-Volatility in ihren
Daten stärkeres Return-Timing liefern kann, repliziert sich in unserem
Fixed-Candidate-ETF-Universum nicht. Der Rolling-PF gewinnt konsistent etwas,
aber die eigentlich gesuchte Rapid-Drawdown-Reaktion und der Drawdown selbst
verschlechtern sich.

Zusammen mit 31-vs-63, EWMA(0,94), Shock Guard und dem 1/5/20/60-Horizon-
Profil ist damit die Risk-Layer-Volatility-Familie als universelle Lösung
weitgehend abgegrenzt:

- Fensterverkürzung: nicht unterstützt
- EWMA-Forecast: nicht unterstützt
- Ein-Tages-Shock-Ergänzung: nicht unterstützt
- Downside-Volatility: nicht unterstützt

Es gibt daher keinen belastbaren Grund, die bestehende 63-Session-Total-
Volatility-Referenz weiter durch lokale Risikometrikvarianten zu optimieren.

## Konsequenz

Die bestehende Risk-Layer-Referenz bleibt unverändert. Der Produktionskandidat
bleibt BLOCKED.

Der Forschungsfokus wechselt jetzt auf die **zugrunde liegende Signal-/Portfolio-
Architektur und die Entstehung des Research-Drawdowns**, nicht auf weitere
Volatilitätsmetriken.

Der nächste technische Pflichtpunkt ist zusätzlich Issue #55: die Live-
Validierungspipeline muss Asset-Kalender timestamp-basiert statt positional
ausrichten, damit neue unabhängige Validierungen nicht an stillen Kalender-
Differenzen scheitern.

## Externe Einordnung

Wang & Yan (2021) definieren Downside-Volatility aus negativen Tagesrenditen
und berichten stärkeres Return-Timing in ihrem Untersuchungsuniversum.
Die vorliegende Studie ist ein unabhängiger Gegencheck und kein Transfer des
dortigen Ergebnisses.

Quelle: Wang & Yan (2021), Downside risk and the performance of volatility-
managed portfolios, Journal of Banking & Finance 131, 106198,
doi:10.1016/j.jbankfin.2021.106198.

## Provenienz

- PR #62: Research: fixed downside-volatility risk-layer control
- Run: 35967492892
- Artifact: 10794543588
- Artifact-Digest: sha256:2d044a9318c8c1101ae054331695f9a65230729d639bd2d632cd6b7d03087d47
- Experiment-Fingerprint: cf73052691dba0220e08a8b0ef15de1fbe175f2e694b6e7bb22c38774f645700
- vollständige Testsuite: bestanden
- ARM64 Research Smoke: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- Holdout nicht berichtet oder verwendet