# Sleeve-Aggregations-Ablation — Ergebnis 2026-09-23

## Fragestellung

Die Untersuchung prüfte auf vier bereits abgeschlossenen, vollständig symbol-disjunkten
Validierungsdatensätzen, ob die feste 50/50-Aggregation selbst ein wiederkehrender
Treiber der beobachteten Research-Risiko-/Rolling-Failures ist.

Auswertung ausschließlich auf den jeweiligen 2.798 Research-Returns.
Der 700-Return-Holdout wurde weder berichtet noch für Entscheidungen verwendet.

## Vorab festgelegte Varianten

- Trend-only: 100% Trend / 0% Cross-Sectional
- Current mix: 50% Trend / 50% Cross-Sectional
- Cross-Sectional-only: 0% Trend / 100% Cross-Sectional

Unverändert: SMA 50/200 Trend, 12-1 CS Momentum Top-2, PIT-Semantik,
10% annualisiertes Realized-Volatility-Budget über 63 Sessions,
Base/1,5x/2x-Kosten.

## Base-Kosten — Research-Ergebnisse

| Validierung | Variante | Research Return | Research DD | Rolling PF | Rolling Avg DD | profitable Fenster |
|---|---|---:|---:|---:|---:|---:|
| 1 | Trend-only | -8,66% | 23,94% | 0,982 | 12,43% | 2/5 |
| 1 | 50/50 | +42,30% | 16,81% | 1,075 | 12,62% | 4/5 |
| 1 | CS-only | +68,04% | 16,20% | 1,097 | 12,99% | 5/5 |
| 2 | Trend-only | +40,77% | 18,29% | 1,072 | 14,42% | 3/5 |
| 2 | 50/50 | +4,90% | 24,87% | 1,017 | 16,78% | 2/5 |
| 2 | CS-only | -7,97% | 30,72% | 0,996 | 17,78% | 1/5 |
| 3 | Trend-only | +2,93% | 20,78% | 1,016 | 12,37% | 4/5 |
| 3 | 50/50 | +14,39% | 21,27% | 1,032 | 15,34% | 4/5 |
| 3 | CS-only | +17,15% | 23,92% | 1,035 | 16,37% | 4/5 |
| 4 | Trend-only | +11,45% | 20,25% | 1,032 | 15,15% | 3/5 |
| 4 | 50/50 | +37,92% | 19,50% | 1,064 | 15,47% | 4/5 |
| 4 | CS-only | +40,70% | 18,81% | 1,065 | 15,52% | 4/5 |

## Vorab definierte Entscheidung

- Trend-only dominiert 50/50 auf Research-DD und Rolling-PF in 1/4 Sätzen.
- CS-only dominiert 50/50 auf beiden Kriterien in 2/4 Sätzen.
- 50/50 ist in 0/4 Sätzen gleichzeitig schlechter als beide Single-Sleeves
  bei Research-DD und Rolling-PF.

Die präregistrierte 3/4-Replikationsschwelle für einen universellen
Aggregationskontrast wird nicht erreicht.

Entscheidungsbefund: no_universal_aggregation_contrast.

## Wissenschaftliche Einordnung

Der Vierfachbefund spricht gegen die Hypothese, dass die feste 50/50-Mischung
allein der universelle Ursprung der Failure-Gates ist.

Gleichzeitig bleibt die Kombination in einzelnen Datensätzen sichtbar
kontextabhängig: Satz 2 wird vom Trend-only-Control deutlich weniger belastet,
während in Satz 1 der CS-only-Control besser abschneidet. Das ist ein
nichtuniverseller Kontextbefund und kein belastbarer Grund für nachträgliche
Gewichtsoptimierung.

Die evidenzbasierte Konsequenz bleibt daher:
keine Gewichtsanpassung, keine Parameteroptimierung, keine Gate-Änderung.

## Provenienz

- PR #44, Research: Pre-registered sleeve aggregation ablation
- Run: 35868801320
- Artifact: 10754210829
- Artifact-Digest: sha256:66bed2768cce7a7ef9f8a1d0ab937eb00273f4b45cfedc721ac9239feef2e21e
- Ergebnis-Fingerprint: f8f8c18e004dc3bd6eda4851d4d9b384f38994b921e92dbed93bb8dcf9caf125
- Volltests im Ablationslauf: bestanden
- Paper-only Safety: bestanden

## Sicherheitsvertrag

- PAPER_ONLY=True
- LIVE_TRADING_ENABLED=False
- keine Orders
- keine Produktionsänderung
- Holdout nicht zur Auswahl verwendet