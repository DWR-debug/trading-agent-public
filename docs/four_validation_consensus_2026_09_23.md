# Vierfacher unabhängiger Validierungs-Konsens — 2026-09-23

## Ergebnis

Die unveränderte tägliche Forschungsarchitektur wurde inzwischen in vier vollständig
symbol-disjunkten ETF-Familien unter demselben festgeschriebenen Protokoll geprüft.

| Satz | Trend-Sleeve | Cross-Sectional-Sleeve | Run | Artifact |
|---|---|---|---:|---:|
| 1 | DIA, EEM, LQD, IEF, VNQ, USO, FXE, TIP | XLK, XLF, XLE, XLV, XLI | 35865847394 | 10751817990 |
| 2 | VTI, VEA, VTV, VUG, XLB, XLP, XLU, XLY | XBI, KRE, XME, XOP, XRT | 35839443616 | 10740188093 |
| 3 | MDY, IJH, EWA, EWJ, EWG, BND, SHY, HYG | IYR, IYT, KIE, IHF, IWC | 35851876264 | 10745697729 |
| 4 | SCHB, VO, VB, VXF, VXUS, VGK, IAU, AGG | KBE, KCE, IYZ, IHI, XHB | 35867637587 | 10753545703 |

Alle vier Läufe sind COMPLETED; alle vier Kandidatenberichte sind BLOCKED.

## Formale Gate-Konsistenz

| Gate | 1 | 2 | 3 | 4 | Failures |
|---|---:|---:|---:|---:|---:|
| Research Drawdown | FAIL | FAIL | FAIL | FAIL | 4/4 |
| Rolling Profit Factor | FAIL | FAIL | FAIL | FAIL | 4/4 |
| Rolling Average Drawdown | FAIL | FAIL | FAIL | FAIL | 4/4 |
| Holdout Drawdown | FAIL | FAIL | PASS | FAIL | 3/4 |
| Rolling Profitable Window Ratio | PASS | FAIL | PASS | PASS | 1/4 |
| Holdout Profit Factor | PASS | FAIL | PASS | PASS | 1/4 |
| OOS/IS Return Ratio | PASS | PASS | PASS | PASS | 0/4 |
| Holdout Return > 0 | PASS | PASS | PASS | PASS | 0/4 |
| 1.5x Cost Holdout >= 0 | PASS | PASS | PASS | PASS | 0/4 |
| 2x Cost Holdout >= 0 | PASS | PASS | PASS | PASS | 0/4 |
| Total-Return-Sensitivity >= 0 | PASS | PASS | PASS | PASS | 0/4 |

Der wiederkehrende Risikobefund ist damit selbst repliziert. Die Evidenz hängt
nicht mehr an einer einzelnen Asset-Familie oder einem einzelnen historischen
Zeitfenster.

## Kennzahlen

| Kennzahl | Satz 1 | Satz 2 | Satz 3 | Satz 4 |
|---|---:|---:|---:|---:|
| Research Return | +42,30% | +4,90% | +14,39% | +37,92% |
| Research DD | 16,81% | 24,87% | 21,27% | 19,50% |
| Research PF | 1,075 | 1,017 | 1,032 | 1,064 |
| Holdout Return | +29,78% | +10,32% | +18,48% | +27,30% |
| Holdout DD | 12,01% | 16,43% | 12,75% | 16,03% |
| Holdout PF | 1,194 | 1,069 | 1,119 | 1,163 |
| OOS/IS | 0,704 | 2,106 | 1,284 | 0,720 |
| Research Rolling PF | 1,075 | 1,017 | 1,032 | 1,064 |
| Research Rolling Average DD | 12,62% | 16,78% | 15,34% | 15,47% |
| Profitables Research-Rolling | 4/5 | 2/5 | 4/5 | 4/5 |

Über die vier Sätze liegt der arithmetische Mittelwert des Research-Drawdowns
bei 20,61%, des Rolling-PF bei 1,047 und des Rolling-Average-DD bei 15,05%.

## Einordnung

1. Die Holdout-Rendite bleibt in allen vier unabhängigen Sätzen positiv.
2. Die robusten Risiko-/Rolling-Gates versagen dagegen systematisch.
3. Der zusätzliche vierte Satz ändert die Richtung des Befunds nicht.
4. Der zuvor festgestellte Wechsel der dominanten Sleeve bleibt bestehen; es
   gibt keine replizierte universelle Ein-Sleeve-Ursache.
5. Die 63-Session-/10%-Vol-Schicht reduziert Exposition, beseitigt aber die
   gemeinsame Failure-Struktur nicht.

Der Konsens rechtfertigt keine nachträgliche Änderung von Parametern, Kosten,
Gates oder Asset-Auswahl. Der Kandidat bleibt ein Research-Kandidat und BLOCKED.

## Nächste zulässige Forschung

Vor einer Intervention soll nur eine Hypothese umgesetzt werden, die aus einem
replizierten Kontrast ableitbar und vorab vollständig definierbar ist. Eine
Änderung wird nicht aus dem Holdout-Ergebnis ausgewählt. Ohne einen solchen
Kontrast bleibt die Architektur unverändert und die Evidenzbasis wird
stattdessen durch unabhängige Validierung oder eine klar abgegrenzte neue
Forschungsfrage erweitert.

## Sicherheits- und Provenienzvertrag

Alle vier Untersuchungen sind Research-only:
- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- orders_enabled=False
- keine Produktionsmutation
- keine Parameteroptimierung
- keine Selection nach Ergebnissichtung
- keine Gate-Änderung

Quellen:
- Satz 1: Run 35865847394 / Artifact 10751817990 / Report-Fingerprint 95affef48ff044217c1de99717fbf69db141b9f7dad2802c88ba17fd0232ef72
- Satz 2: Run 35839443616 / Artifact 10740188093 / Report-Fingerprint 6d8fc3bdb07570548a8d7df8387c6575a868c7ddf07254a0c1787282de871070
- Satz 3: Run 35851876264 / Artifact 10745697729 / Report-Fingerprint ab8687cdca2333bbe1842cd2f128e541456fa0dd78982a126c937bd21a655ee6
- Satz 4: Run 35867637587 / Artifact 10753545703 / Artifact-Digest sha256:a065e6fe43c0e575baa360bfd33167b46e597230dad838d2f6e0194eb83dccc8 / Report-Fingerprint fa1d758b2d2caeada2d275f1f0d2fe598e35725269f1ec93aa9bd934c0a255a1