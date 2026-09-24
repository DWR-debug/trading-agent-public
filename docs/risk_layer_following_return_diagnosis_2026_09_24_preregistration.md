# Risk-Layer Following-Return Diagnosis — Pre-Registration 2026-09-24

## Motivation

Die bisherigen Controls konnten weder die 63-Session-Länge noch eine schnellere
Volatilitätsschätzung als universelle Erklärung des Rapid-Drawdown-Lags bestätigen.
Die Literatur zu Volatility-Managed Portfolios beschreibt den ökonomischen Nutzen
von Volatility Timing gerade dann, wenn höhere Risikozustände nicht durch
proportional höhere nachfolgende erwartete Renditen kompensiert werden.

Quelle: Moreira & Muir (2017), Volatility-Managed Portfolios, Journal of Finance
72(4), 1611–1644, doi:10.1111/jofi.12513.

Diese Diagnose prüft daher nicht eine neue Strategie, sondern die empirische
Voraussetzung des bestehenden Risk-Layers.

## Präregistrierte Diagnose

Der bestehende 63-Session-/10%-Risk-Layer wird unverändert simuliert.
Für jede Research-Periode t wird die **unskalierte** Rendite der unmittelbar
folgenden Periode t+1 betrachtet.

Zwei Zustände werden verglichen:

- De-Risk-Zustand: Scale(t) < 1
- Voll-Risiko-Zustand: Scale(t) = 1

Vorab definierte Kennzahlen:

1. Mittelwert der folgenden unskalierten Netto-Rendite.
2. Anteil positiver folgender unskalierter Netto-Renditen.

Ein Datensatz unterstützt die bestehende Volatility-Timing-Prämisse nur dann,
wenn **beide** folgenden Beziehungen gelten:

- mittlere Folgerendite nach De-Risking <= mittlere Folgerendite nach Voll-Risiko
- positive Folgerenditenrate nach De-Risking <= positive Rate nach Voll-Risiko

Das ist ein deskriptiver Vorwärtskontrast, kein Kausalitätsnachweis.

## Replikationsregel

- günstige Beziehung in >=3/4: die empirische Timing-Prämisse ist repliziert
- ungünstige Beziehung in >=3/4: die Timing-Prämisse wird empirisch widersprochen
- sonst: kein replizierter Zusammenhang

Es wird aus diesem Diagnoseergebnis noch keine neue Produktionsregel abgeleitet.

## Datenbasis

- vier vollständig symbol-disjunkte immutable Validierungsfamilien
- 2.798 Research-Returns je Familie
- 2.797 Research-Übergänge je Familie
- 20 bestehende Rolling-Fenster bleiben die Evidenzbasis, werden aber nicht
  als Auswahlkriterium für die Diagnose verwendet
- Holdout weder berichtet noch verwendet
- keine neue Datenakquisition

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- keine Parameteroptimierung
- keine Gate-Änderung
- keine Asset-Auswahl