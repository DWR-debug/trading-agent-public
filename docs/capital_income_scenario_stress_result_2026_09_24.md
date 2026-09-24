# Capital Income Scenario Stress — Ergebnis 2026-09-24

**Study-ID:** CAPITAL-INCOME-STRESS-2026-09-24  
**Status:** `archived_diagnostic`  
**Workflow Run:** 35989864728  
**Artifact:** 10803478746  
**Artifact SHA-256:** c05fc46dae6a086153b067d263ac6f86c988cf9dd42e1e4b00dd754f9d2fd407  
**Report-Fingerprint:** 733c22814e1e3b539d9853a073c3016c48d7075e41a1c1a67d75c1dbcacab2b1

## Design

- 6 vollständig vorab definierte synthetische 252-Perioden-Szenarien
- 3 vollständig vorab definierte Entnahmepolitiken
- keine Optimierung, kein Forecast und keine Auswahl nach Ergebnis
- Startkapital 500 EUR
- Ausschüttungsintervall 21 Perioden
- zusätzliche deterministische Gegenprobe mit umgekehrter Reihenfolge derselben Renditen

Die Szenarien sind methodische Kontrollen und keine historischen Strategiepfade.

## Ergebnisse

| Szenario | Policy | Auszahlung EUR | Endkapital EUR | Max DD |
|---|---|---:|---:|---:|
| Flat | Full Payout | 0,00 | 500,00 | 0,00 % |
| Flat | Balanced Capitalization | 0,00 | 500,00 | 0,00 % |
| Flat | Protected Income | 0,00 | 500,00 | 0,00 % |
| Steady Growth | Full Payout | 50,60 | 500,00 | 0,80 % |
| Steady Growth | Balanced Capitalization | 33,35 | 518,13 | 0,52 % |
| Steady Growth | Protected Income | 23,17 | 529,40 | 0,77 % |
| Volatile Growth | Full Payout | 29,99 | 499,58 | 1,60 % |
| Volatile Growth | Balanced Capitalization | 19,72 | 510,11 | 1,10 % |
| Volatile Growth | Protected Income | 4,15 | 526,14 | 1,06 % |
| Early Drawdown | Full Payout | 52,89 | 500,00 | 18,98 % |
| Early Drawdown | Balanced Capitalization | 32,26 | 521,54 | 18,98 % |
| Early Drawdown | Protected Income | 18,05 | 536,68 | 18,98 % |
| Late Drawdown | Full Payout | 159,89 | 405,08 | 21,49 % |
| Late Drawdown | Balanced Capitalization | 108,64 | 453,86 | 20,65 % |
| Late Drawdown | Protected Income | 128,06 | 439,33 | 21,49 % |
| Whipsaw | Full Payout | 1,92 | 497,08 | 0,98 % |
| Whipsaw | Balanced Capitalization | 1,12 | 497,88 | 0,82 % |
| Whipsaw | Protected Income | 0,00 | 498,99 | 0,60 % |

## Sequence Risk

Die umgekehrte Renditereihenfolge verändert die Ausschüttungen teils sehr stark.
Im Early-Drawdown-Szenario beträgt die Abweichung gegenüber der chronologischen
Reihenfolge beim Full-Payout-Modell rund **−106,99 EUR**; beim Balanced-Capitalization
Modell rund **−76,39 EUR**. Im spiegelbildlichen Late-Drawdown-Szenario kehren
sich diese Differenzen entsprechend um.

Damit ist experimentell gezeigt, dass ein Entnahmemodell nicht nur von der
Gesamtrendite, sondern auch stark von deren zeitlicher Anordnung abhängt.

## Forschungsbedeutung

Der Test ist **keine Renditeprognose** und macht keinen realen Strategiepfad
wirtschaftlich belastbar. Er zeigt vielmehr, dass das Familien-/Entnahmekapital
als eigener Risikopfad modelliert werden muss.

Die sinnvolle nächste Kopplung ist deshalb die gleiche Kapital-/Entnahmelogik auf
vollständig erhaltenen historischen Return-Serien bereits verifizierter
Strategiepfade anzuwenden und dabei Mindestkapital, Ausschüttung, Drawdown,
Sequence Sensitivity und Kosten-Stress gemeinsam zu gate-en.

## Sicherheit

Der Workflow bestätigte Paper-Only:
`PAPER_ONLY=True`, `LIVE_TRADING_ENABLED=False`, `orders_enabled=False`.

Die vollständige Suite bestand mit **557 Tests**.
