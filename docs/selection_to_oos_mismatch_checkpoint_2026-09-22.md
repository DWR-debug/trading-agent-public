# Selection-to-OOS-Mismatch — Checkpoint 2026-09-22

## Laufidentität

- Source Rolling-Control Workflow Run: 35750723097
- Source Rolling-Control Artifact: 10704817758
- Source Rolling-Control Artifact-Digest: sha256:9347573690a8c3ec52cd61ba645a1a0bc84858f9095b2c75027a97d10ff4dd22
- Source Rolling-Control Diagnostic-Fingerprint: 4fbd29349792371765c43fb25dc8264bdf035ee05eaa76f1b215f9e0d9ba85af
- Selection-to-OOS Workflow Run: 35757944587
- Selection-to-OOS Artifact: 10709300786
- Selection-to-OOS Artifact-Digest: sha256:0114cc64631dc5e1d75ce96795c816381080d9933fd432ce851d5ae46a78445f
- Selection-Control Diagnostic-Fingerprint: b1cf471e26b95a9dfcb2238b3189e36f51fd04d9c5db83628e4cd78389878a8a
- Selection-to-OOS Analysis-Fingerprint: 025196b611712cdce3ae4244da9430f29a9da16a7a313efd3a2c8378db1dc27f
- Research-Basis: 4.500 Candles je Asset
- Universe: benchmark — SPY, QQQ, IWM
- Evaluationen: 240 = 60 Marktfenster × 4 Selection-Profile
- eindeutige Marktfenster: 60
- Parameterraum: 1.280 Kandidaten

## Fragestellung

Geprüft wird, wie stark die Trainings-/Selection-Qualität des tatsächlich ausgewählten Kandidaten mit dessen unmittelbar folgendem OOS-Ergebnis zusammenhängt.

Der diagnostische Layer verändert weder Parameterraum noch Selection-Profile noch Research-Gates. OOS wird niemals zur Auswahl verwendet.

Der Profil-Rang des ausgewählten Kandidaten ist per Definition 1 und deshalb nicht als unabhängige Qualitätsvariable interpretierbar.

Der informative Querschnittsmaßstab ist der **Raw-Score-Rang** des ausgewählten Kandidaten innerhalb aller 1.280 Trainingskandidaten. Zusätzlich werden Selection-Score, Abstand zum Profil-Zweitplatzierten, Abstand zum Raw-Score-Besten und Trainingsmetriken archiviert.

## Gesamtbefund

| Kennzahl | Wert |
| --- | ---: |
| positive OOS-Fenster | 37,1 % |
| PF-Pass | 32,5 % |
| Median OOS-Profit | -2,75 € |
| Median Training-Profit | +32,88 € |
| Median Raw-Score-Rang | 45 |
| Median Selection-Score | 14,47 |
| Median Selected-vs-Best-Raw-Score-Gap | -22,45 |

Die Trainingsseite wirkt deutlich stärker als die unmittelbar folgende OOS-Seite: Der Median des Trainingsprofits liegt bei +32,88 €, der Median des OOS-Profits bei -2,75 €.

Das ist ein deutlicher Selection-to-OOS-Mismatch. Er ist jedoch kein kausaler Nachweis für Overfitting oder eine einzelne technische Ursache.

## Training positiv vs. OOS positiv

| Beziehung | Anzahl | Quote |
| --- | ---: | ---: |
| Training positiv → OOS positiv | 70 | 29,2 % |
| Training positiv → OOS nicht positiv | 102 | 42,5 % |
| Training nicht positiv → OOS positiv | 19 | 7,9 % |
| Training nicht positiv → OOS nicht positiv | 49 | 20,4 % |

Der größte Block ist damit **Training positiv → OOS nicht positiv**. Die Trainingspositivität des ausgewählten Kandidaten bestätigt sich im unmittelbar folgenden OOS-Fenster häufig nicht.

## Selection-/Rank-Zusammenhang

| Merkmal | Pearson | Spearman | n |
| --- | ---: | ---: | ---: |
| Raw-Score-Rang vs. OOS-Profit | -0,050 | -0,087 | 240 |
| Selection-Score vs. OOS-Profit | +0,001 | +0,089 | 240 |
| Runner-up-Score-Gap vs. OOS-Profit | +0,089 | +0,132 | 240 |
| Selected-vs-Best-Raw-Score-Gap vs. OOS-Profit | +0,050 | +0,085 | 240 |
| Training-Profit vs. OOS-Profit | -0,096 | +0,032 | 240 |
| Training-PF vs. OOS-Profit | +0,076 | +0,125 | 240 |
| Training-Trade-Count vs. OOS-Profit | -0,109 | -0,191 | 240 |

Auf Ebene der 240 Evaluationen gibt es damit **keinen starken linearen oder monotonen Zusammenhang** zwischen besserem Raw-Score-Rang und anschließendem OOS-Profit.

Zur Vermeidung von Scheinsicherheit wurde zusätzlich ein marktfensterbalancierter Blick verwendet, der die vier Profile pro Asset/Geometrie/Fenster zu einer Beobachtung zusammenfasst. Dort ergibt sich für Raw-Score-Rang vs. OOS-Profit:

- Pearson: -0,090
- Spearman: -0,040
- n = 60 Marktfenster

Auch die Trainingsprofit-vs.-OOS-Beziehung bleibt dort schwach und negativ:

- Pearson: -0,271
- Spearman: -0,232

Die Korrelationen sind deskriptiv und nicht kausal.

## Raw-Score-Rang-Bänder

| Band | Rang | Evaluationen | positive OOS | PF-Pass | Median OOS-Profit | Median Training-Profit |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Top 1 % | 1–13 | 83 | 41,0 % | 36,1 % | -1,44 € | +134,63 € |
| Top 5 % ohne Top 1 % | 14–64 | 45 | 42,2 % | 35,6 % | 0,00 € | +44,91 € |
| Top 10 % ohne Top 5 % | 65–128 | 9 | 33,3 % | 33,3 % | -2,81 € | +48,22 € |
| außerhalb Top 10 % | 129–1280 | 103 | 32,0 % | 28,2 % | -4,57 € | -11,17 € |

Es gibt somit einen gewissen Unterschied zwischen sehr guten und deutlich schlechteren Trainings-Rängen, aber **keine monotone Stufung**, die eine einfache Regel „je höher der Trainingsrang, desto besser OOS“ rechtfertigen würde.

Außerdem überlappen die vier Selection-Profile dieselben Marktfenster; die Evaluationen innerhalb eines Fensters sind daher nicht unabhängig.

## Selection-Profile

| Profil | Median Raw-Score-Rang | positive OOS | PF-Pass | Median OOS-Profit |
| --- | ---: | ---: | ---: | ---: |
| boundary_averse | 201 | 43,3 % | 40,0 % | -2,64 € |
| risk_averse | 21 | 41,7 % | 36,7 % | -0,67 € |
| score_max | 1 | 40,0 % | 35,0 % | -1,98 € |
| trade_rich | 629 | 23,3 % | 18,3 % | -4,78 € |

Die Profile produzieren deutlich unterschiedliche Selection-Ränge und OOS-Verteilungen. Diese Zahlen sind eine **deskriptive Gegenüberstellung**, keine neue Selection-Regel und keine abschließende Bewertung der Profile.

Auffällig ist insbesondere, dass Profile mit sehr unterschiedlichen Trainingsrängen nicht entsprechend stark unterschiedliche OOS-Qualität erzeugen.

## Asset x Geometrie

| Asset | Geometrie | Median Raw-Score-Rang | positive OOS | PF-Pass | Median OOS-Profit |
| --- | --- | ---: | ---: | ---: | ---: |
| IWM | Small | 23 | 30,0 % | 26,7 % | -6,47 € |
| IWM | Large | 87 | 40,0 % | 25,0 % | -4,13 € |
| QQQ | Small | 43 | 40,0 % | 35,0 % | -2,28 € |
| QQQ | Large | 43 | 35,0 % | 25,0 % | -1,30 € |
| SPY | Small | 53 | 41,7 % | 40,0 % | -0,69 € |
| SPY | Large | 109 | 35,0 % | 35,0 % | -3,21 € |

Die Heterogenität nach Asset und Geometrie bleibt bestehen. Für IWM Small beträgt beispielsweise die Spearman-Korrelation zwischen Raw-Score-Rang und OOS-Profit +0,248, während sie für SPY Small -0,244 und für QQQ Large -0,373 beträgt. Die Gruppen sind klein; insbesondere Large enthält nur fünf eindeutige Marktfenster je Asset.

Für IWM Small ist zudem die Korrelation zwischen Training-Profit und OOS-Profit deutlich negativer:

- Pearson: -0,375
- Spearman: -0,372
- n = 60 Evaluationen

Das spricht dafür, dass der Selection-to-OOS-Mismatch nicht in allen Markt-/Geometrie-Kombinationen gleich ausgeprägt ist.

## Fachliche Einordnung

Die bisherige Evidenzkette lässt sich durch diesen Layer präzisieren:

**Horizon → Zeitphasen → Rolling-Geometrie → Volatilität → Marktstruktur → Asset-Interaktion → Kandidatenmigration → Selection-to-OOS**

Der neue Layer liefert drei wesentliche Ergebnisse:

1. **Kandidatenwechsel allein erklärt den Engpass nicht.** Das wurde bereits durch die Migrations-Nachwirkungsanalyse nicht bestätigt.

2. **Die reine Trainings-Ranghöhe erklärt den unmittelbar folgenden OOS-Erfolg nur sehr schwach.** Der Raw-Score-Rang korreliert insgesamt nur schwach mit dem OOS-Profit; die marktfensterbalancierte Spearman-Korrelation liegt nahe null.

3. **Die Trainingsqualität selbst zeigt einen deutlichen Mismatch zum nächsten OOS-Fenster.** Besonders die 42,5-%-Quote „Training positiv → OOS nicht positiv“ zeigt, dass ein gutes Trainingsergebnis häufig nicht in das nächste OOS-Fenster übertragen wird.

Damit ist die Selection-Schicht ein plausibler weiterer Untersuchungsbereich, aber die Daten stützen **keine einfache Lösung durch „besseren“ Trainingsscore oder eine starre Rangschwelle**.

## Nächster Entwicklungsschritt

Der nächste sinnvolle Layer ist daher ein **Selection-Stability-/Robustness-Control** auf den Trainingsdaten selbst.

Geprüft werden sollten insbesondere:

- Rangstabilität des ausgewählten Kandidaten über interne Teilfenster des Training-Samples
- Top-k-Mitgliedschaft über interne Teilfenster
- Parameterstabilität des ausgewählten Kandidaten
- normalisierter Selection-Abstand gegenüber konkurrierenden Kandidaten
- Übereinstimmung bzw. Divergenz der vier Selection-Profile

Erst wenn solche **Training-only-Stabilitätsmerkmale** messbar mit anschließendem OOS-Verhalten zusammenhängen, sollte daraus eine mögliche Änderung der Selection-Mechanik abgeleitet werden.

Die OOS-Daten bleiben dabei ausschließlich Outcome für die Diagnose; sie dürfen nicht in die neue Selection-Regel einfließen.

## Reproduzierbarkeit und Sicherheit

Die Analyse basiert ausschließlich auf dem unveränderten, immutable archivierten Research-Datensatz des Rolling-Control-Laufs.

Die Selection-to-OOS-Control-Reproduktion hat den bestehenden Rolling-Control-Befund auf Window-, Summary- und Gate-Ebene unverändert bestätigt.

- Full Test Suite: 285 Tests bestanden
- Paper-Only: True
- Live-Trading: False
- Orders: False
- keine Änderung an Strategy
- keine Änderung am Parameterraum
- keine Änderung an Research-Gates
- kein OOS-basiertes Selection-Leakage
