# Rolling-WF Kandidaten-Migrations-Nachwirkung — Checkpoint 2026-09-22

## Laufidentität

- Rolling-Control Workflow Run: 35750723097
- Rolling-Control Artifact: 10704817758
- Rolling-Control Artifact-Digest: sha256:9347573690a8c3ec52cd61ba645a1a0bc84858f9095b2c75027a97d10ff4dd22
- Rolling-Control Diagnostic-Fingerprint: 4fbd29349792371765c43fb25dc8264bdf035ee05eaa76f1b215f9e0d9ba85af
- Migration-Aftereffect Workflow Run: 35754677449
- Migration-Aftereffect Artifact: 10707238623
- Migration-Aftereffect Artifact-Digest: sha256:6e52c60b190f0411b30e2d9c716038a5049a916322d32b1e3c63e017c0341f7f
- Migration-Aftereffect Analysis-Fingerprint: 988cae167144d58f1e4baf69e7f311c2c441ef46154c3d5aa2c2acdd29ee5cff
- Research-Basis: 4.500 Candles je Asset
- Universe: benchmark — SPY, QQQ, IWM
- Übergänge: 216
- Migrationen: 119
- Stabile Übergänge: 97

## Definition

Ein Übergang besteht aus zwei benachbarten Rolling-Fenstern desselben Assets, derselben Geometrie und desselben Selection-Profils.

- **Nach Migration:** Der Kandidat ändert sich beim Übergang; das Ziel-Fenster ist das erste OOS-Fenster, in dem der neue Kandidat erstmals eingesetzt wird.
- **Stabiler Kandidat:** Der Kandidat bleibt beim Übergang unverändert; das Ziel-Fenster dient als Vergleichsgruppe.

Ausgewiesen werden die tatsächlichen OOS-Ergebnisse des Ziel-Fensters und zusätzlich die Veränderung des Fensterprofits gegenüber dem unmittelbar vorherigen Fenster.

## Gesamtbefund

| Gruppe | Übergänge | eindeutige Ziel-Fenster | positive Ziel-Fenster | PF-Pass | Median Ziel-Profit EUR | Median Profit-Delta EUR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Nach Migration | 119 | 46 | 37,0 % | 32,8 % | -1,67 | +1,64 |
| Stabiler Kandidat | 97 | 48 | 37,1 % | 30,9 % | -3,06 | -4,39 |

Die positive Ziel-Fenster-Quote ist praktisch identisch. Nach Migration liegt der Medianprofit des Ziel-Fensters jedoch höher und das Median-Delta zum Quellfenster ist positiv, während stabile Übergänge im Median eine Verschlechterung zeigen.

Das ist eine **deskriptive Assoziation**, kein kausaler Nachweis. Das Ziel-Fenster ist gleichzeitig ein neues Marktfenster; die Analyse kann daher keinen isolierten Ursache-Wirkungs-Effekt der Kandidatenänderung identifizieren.

## Asset x Geometrie

| Asset | Geometrie | Gruppe | Übergänge | eindeutige Ziel-Fenster | positive Ziel-Fenster | PF-Pass | Median Ziel-Profit EUR | Median Profit-Delta EUR |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| SPY | Small | Migration | 23 | 9 | 39,1 % | 39,1 % | 0,00 | +1,39 |
| SPY | Small | Stabil | 33 | 13 | 42,4 % | 39,4 % | -2,01 | -3,50 |
| SPY | Large | Migration | 8 | 4 | 50,0 % | 50,0 % | +0,72 | +5,43 |
| SPY | Large | Stabil | 8 | 4 | 0,0 % | 0,0 % | -9,31 | -7,75 |
| QQQ | Small | Migration | 28 | 12 | 39,3 % | 39,3 % | -2,06 | -1,30 |
| QQQ | Small | Stabil | 28 | 13 | 42,9 % | 32,1 % | -1,09 | -3,30 |
| QQQ | Large | Migration | 11 | 4 | 27,3 % | 9,1 % | -3,14 | +3,21 |
| QQQ | Large | Stabil | 5 | 3 | 20,0 % | 20,0 % | -7,64 | -18,37 |
| IWM | Small | Migration | 36 | 13 | 27,8 % | 25,0 % | -6,41 | +4,03 |
| IWM | Small | Stabil | 20 | 12 | 40,0 % | 35,0 % | -4,25 | -3,83 |
| IWM | Large | Migration | 13 | 4 | 53,8 % | 38,5 % | +1,87 | -9,21 |
| IWM | Large | Stabil | 3 | 3 | 33,3 % | 0,0 % | -11,28 | -0,36 |

Die Asset-/Geometrie-Aufteilung ist heterogen. Insbesondere IWM Small zeigt nach Migration keine höhere positive Quote oder PF-Pass-Quote, obwohl das Profit-Delta im Median positiv ist. Viele Gruppen haben nur drei bis dreizehn eindeutige Ziel-Fenster; diese Werte sind daher keine belastbaren stabilen Regeln.

## Selection-Profile

| Profil | Gruppe | Übergänge | positive Ziel-Fenster | PF-Pass | Median Ziel-Profit EUR |
| --- | --- | ---: | ---: | ---: | ---: |
| boundary_averse | Migration | 25 | 44,0 % | 44,0 % | -0,13 |
| boundary_averse | Stabil | 29 | 41,4 % | 34,5 % | -2,87 |
| risk_averse | Migration | 39 | 35,9 % | 30,8 % | -1,44 |
| risk_averse | Stabil | 15 | 53,3 % | 46,7 % | +0,36 |
| score_max | Migration | 41 | 36,6 % | 31,7 % | -2,52 |
| score_max | Stabil | 13 | 46,2 % | 38,5 % | 0,00 |
| trade_rich | Migration | 14 | 28,6 % | 21,4 % | -4,60 |
| trade_rich | Stabil | 40 | 25,0 % | 20,0 % | -4,91 |

Auch die Profilaufteilung ist nicht einheitlich. Das risk_averse-Profil zeigt beispielsweise bei stabilen Kandidaten bessere Zielwerte als nach Migration, während trade_rich nur kleine Unterschiede aufweist.

## Parameterbezogene Nachwirkung

| Parameter | Wechselzahl | positive Ziel-Fenster | PF-Pass | Median Ziel-Profit EUR | Median Profit-Delta EUR |
| --- | ---: | ---: | ---: | ---: | ---: |
| risk_per_trade | 22 | 54,5 % | 50,0 % | +2,84 | +8,36 |
| leverage | 0 | n/a | n/a | n/a | n/a |
| momentum.lookback | 76 | 32,9 % | 31,6 % | -1,98 | +1,51 |
| mean_reversion.window | 75 | 32,0 % | 26,7 % | -3,14 | +3,39 |
| mean_reversion.threshold | 62 | 40,3 % | 38,7 % | -1,06 | +6,09 |

Parametergruppen überlappen, weil ein Übergang mehrere Parameter gleichzeitig ändern kann. Die risk_per_trade-Gruppe umfasst nur 22 Übergänge und wird deshalb nicht als eigenständige Evidenz für eine Parameteränderung interpretiert.

## Fachliche Einordnung

Der gezielte Test widerlegt eine einfache Hypothese, nach der Kandidatenwechsel das unmittelbar folgende OOS-Fenster systematisch verschlechtern.

Gleichzeitig zeigt er keinen stabilen Performancevorteil durch Migrationen: Die positive Fensterquote ist praktisch gleich, die Asset-/Geometrieergebnisse sind heterogen und mehrere Teilgruppen sind klein.

Damit wird die bisher stärkste Spur präzisiert:

**Kandidatenmigration ist diagnostisch relevant, aber Migration allein erklärt den Rolling-WF-Engpass nicht.**

Die Kombination aus häufiger Migration, Assetabhängigkeit und stark unterschiedlichen Ergebnissen je Marktstruktur bleibt eine plausible Forschungsrichtung; sie rechtfertigt jedoch weiterhin keine automatische Änderung von Parameterraum, Selection-Profilen oder Gates.

## Reproduzierbarkeit und Sicherheit

Die Analyse verwendete ausschließlich das archivierte Rolling-Control-Artifact. Es wurden keine neuen Marktdaten geladen, keine Backtests durchgeführt und keine Optimierungen ausgeführt.

Paper-Only: True
Live-Trading: False
Orders: False
