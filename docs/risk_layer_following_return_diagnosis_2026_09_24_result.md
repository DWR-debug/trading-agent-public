# Risk-Layer Following-Return Diagnose — Ergebnis 2026-09-24

## Ergebnis

Die bestehende 63-Session-/10%-Risk-Layer wurde auf vier vollständig
symbol-disjunkten Validierungsfamilien ausschließlich im Research untersucht.
Für jede Research-Periode t wurde die unskalierte Rendite der unmittelbar
folgenden Periode t+1 nach dem Zustand bei t verglichen.

| Validierung | De-Risk-Beobachtungen | Vollrisiko-Beobachtungen | Folgerendite-Differenz De-Risk minus Vollrisiko | Positive-Rate-Differenz |
|---|---:|---:|---:|---:|
| 1 | 1.189 | 1.608 | +0,00899 %-Pkt. | +5,76 %-Pkt. |
| 2 | 2.359 | 438 | +0,01010 %-Pkt. | +26,54 %-Pkt. |
| 3 | 1.281 | 1.516 | +0,02249 %-Pkt. | +7,45 %-Pkt. |
| 4 | 1.737 | 1.060 | +0,05926 %-Pkt. | +13,05 %-Pkt. |

Die präregistrierten beiden Beziehungen waren in **4/4** Datensätzen
gleichgerichtet und ungünstig für die bestehende Volatility-Timing-Prämisse:

- mittlere Folgerendite nach De-Risking > nach Vollrisiko: 4/4
- positive Folgerenditenrate nach De-Risking > nach Vollrisiko: 4/4
- günstige Beziehung: 0/4
- ungünstige Beziehung: 4/4

## Fachliche Einordnung

Dieser Befund ist ein **deskriptiver Vorwärtszusammenhang, kein
Kausalitätsnachweis**. Der De-Risk-Zustand wird aus vorheriger Volatilität
abgeleitet und ist daher endogen zu den Marktbedingungen. Die Richtung kann
unter anderem mit kurzfristiger Mean-Reversion bzw. Erholung nach
Volatilitätsschüben zusammenhängen.

Er ist dennoch relevant, weil die notwendige empirische Voraussetzung eines
klassischen Volatility-Timing-Mechanismus in unserem Fixed Candidate nicht
sichtbar ist: höhere Risikozustände gehen in diesen Daten gerade nicht mit
niedrigeren nachfolgenden Returns einher.

Moreira & Muir (2017) dokumentieren Volatility Timing als wirtschaftlich
vorteilhaft, wenn Volatilitätsänderungen nicht proportional durch erwartete
Renditeänderungen kompensiert werden. Die vorliegende Diagnose zeigt, dass
dieser Zusammenhang im nächsten Tagesabschnitt unseres Kandidaten nicht in
dieser Richtung vorliegt.

Quelle: Moreira & Muir (2017), Volatility-Managed Portfolios, Journal of Finance
72(4), 1611–1644, doi:10.1111/jofi.12513.

Literatur zu längeren Anlagehorizonten weist zudem darauf hin, dass die
Interaktion von Volatility Timing und schneller Return-Mean-Reversion
horizontabhängig sein kann. Deshalb folgt als Diagnose kein sofortiger
Strategieeingriff, sondern ein fixer 1/5/20/60-Tage-Horizontvergleich.

Quelle: Cooper & Priestley (2019), Should Long-Term Investors Time Volatility?,
Journal of Financial Economics 131(3), 507–527, doi:10.1016/j.jfineco.2018.09.011.

## Konsequenz

Keine Änderung der 63-Session-/10%-Risk-Layer, keine Inversion der Risk-Layer
und keine Anpassung von Gates oder Gewichten auf Basis dieses Diagnosebefunds.

Die nächste Untersuchung misst rein deskriptiv, ob der Gegenbefund nur kurzfristig
auftritt oder über 5, 20 und 60 Tage anhält.

## Provenienz

- PR #58: Research: diagnose following returns after de-risking
- Run: 35966356467
- Artifact: 10794845117
- Artifact-Digest: sha256:c4aa1e748fed8af7a723209bb32cfc19cd1f106b8c705bc9023e6e10695431ba
- Diagnostic-Fingerprint: 5b2da80c34487f7a8ae3f7e6c0fd8f82306b4b5d1dcefef60985e2fb4bd8f6a9
- vollständige Testsuite: bestanden
- ARM64 Research Smoke: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- Holdout nicht berichtet oder verwendet