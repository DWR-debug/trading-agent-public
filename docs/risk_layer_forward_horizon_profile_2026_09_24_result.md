# Risk-Layer Forward-Horizon Profile — Ergebnis 2026-09-24

## Befund

Der 4/4-Gegenbefund der unmittelbaren Folgerendite bleibt über längere
Horizonte bestehen. Verglichen wird jeweils die unskalierte kumulierte
Netto-Rendite ab t+1 nach dem Zustand des bestehenden 63-Session-/10%-
Risk-Layers bei t.

| Horizont | günstig | ungünstig | gemischt/unklar |
|---|---:|---:|---:|
| 1 Tag | 0/4 | 4/4 | 0/4 |
| 5 Tage | 0/4 | 4/4 | 0/4 |
| 20 Tage | 0/4 | 3/4 | 1/4 |
| 60 Tage | 0/4 | 4/4 | 0/4 |

Die Beziehung wird als ungünstig klassifiziert, wenn sowohl die mittlere
kumulierte Folgerendite als auch die positive Renditerate nach De-Risking
über dem Vollrisiko-Zustand liegen.

Damit ist der Gegenbefund nicht auf die unmittelbare Folgerperiode begrenzt.
Auch bei 5 und 60 Tagen liegt die ungünstige Beziehung in allen vier
Validierungsfamilien vor; bei 20 Tagen in 3/4.

## Größenordnung

| Validierung | 1 Tag Mean-Diff | 5 Tage Mean-Diff | 20 Tage Mean-Diff | 60 Tage Mean-Diff |
|---|---:|---:|---:|---:|
| 1 | +0,009 %-Pkt. | +0,072 %-Pkt. | +0,468 %-Pkt. | +0,824 %-Pkt. |
| 2 | +0,010 %-Pkt. | +0,076 %-Pkt. | -0,036 %-Pkt. | +0,369 %-Pkt. |
| 3 | +0,022 %-Pkt. | +0,057 %-Pkt. | +0,427 %-Pkt. | +1,510 %-Pkt. |
| 4 | +0,059 %-Pkt. | +0,256 %-Pkt. | +0,968 %-Pkt. | +2,230 %-Pkt. |

Die Mediane zeigen dieselbe Richtung in allen vier Datensätzen und bei allen
vier Horizonten. Die 20-Tage-Ausnahme in Validierung 2 betrifft nur den
Mittelwert; die Kombination aus Median und positiver Rate bleibt dort
ungünstig.

## Fachliche Schlussfolgerung

Die Hypothese eines ausschließlich kurzfristigen Mean-Reversion-Effekts wird
damit nicht bestätigt. Das bestehende De-Risking ist im Fixed Candidate nicht
nur am nächsten Tag, sondern auch über 5 und 60 Tage nicht mit niedrigeren
nachfolgenden unskalierten Renditen verbunden.

Dieser Befund ist weiterhin rein deskriptiv und nicht kausal. Zustandsbildung
und zukünftige Renditen sind endogen gekoppelt; außerdem sind Forward-Horizonte
überlappend.

Für die weitere Forschung ist deshalb sinnvoller, die **Risikometrik selbst**
zu verändern als dieselbe Total-Volatility-Logik weiter zu beschleunigen.
Externe Forschung von Wang & Yan (2021) berichtet, dass Downside-Volatility-
Managed Portfolios gegenüber Total-Volatility-Managed Portfolios stärkeres
Return-Timing aufweisen können, weil Downside-Volatilität zukünftige Returns
negativ prognostizieren kann. Das ist eine Hypothese für unser Universum,
kein übertragener Nachweis.

Quelle: Wang & Yan (2021), Downside risk and the performance of volatility-
managed portfolios, Journal of Banking & Finance 131, 106198,
doi:10.1016/j.jbankfin.2021.106198.

## Konsequenz

Keine Änderung der bestehenden 63-Session-/10%-Risk-Layer auf Basis dieses
Diagnosebefunds. Keine Inversion und kein Leverage-Flip.

Der nächste zulässige Control ist eine einzige, extern motivierte
Downside-Volatility-Intervention mit derselben 63-Session-Historie und
demselben 10%-Ziel. Keine Schwellenwertsuche, kein alternatives Downside-
Fenster und kein Holdout-Selection.

## Provenienz

- PR #60: Research: profile risk-layer forward returns by horizon
- Run: 35966861806
- Artifact: 10794218742
- Artifact-Digest: sha256:07b63055dae48b9f346fbe613e410355855fd7feff68032e3170c14a7b340d21
- Diagnostic-Fingerprint: a8179c3b2082084c6efa32c168a808d550dd8d42f4efcd71fdb13530b7295286
- vollständige Testsuite: bestanden
- ARM64 Research Smoke: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- Holdout nicht berichtet oder verwendet