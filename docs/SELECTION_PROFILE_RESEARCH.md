# Selection-Profile Research

## Zweck

Der Selection-Profile-Layer untersucht die Hypothese, dass die bisherige
Optimierung Kandidaten mit zu aggressiven oder randnahen Parametern bevorzugt.

Er verändert nicht:

- Research-Gates
- Gate-Schwellenwerte
- Holdout-Regeln
- Parameterraum
- Backtest-Engine
- Risk-Limits
- Strategielogik
- Paper-Only-Sicherheit

Er verändert ausschließlich die Reihenfolge, in der bereits vollständig
ausgewertete Optimierungskandidaten ausgewählt werden.

## Kontrollierte Profile

### score_max

Kontrollprofil. Es entspricht dem bisherigen Verhalten:

`score DESC`

### boundary_averse

Bevorzugt Kandidaten mit höherer mittlerer Distanz zu den Grenzen des
definierten Parameterraums. Der bestehende Optimizer-Score ist Tie-Breaker:

`parameter_centrality DESC, score DESC`

Die Zentralität wird deterministisch aus Momentum-Lookback, Mean-Reversion-
Window, Threshold, Risiko pro Trade und Hebel berechnet.

### risk_averse

Bevorzugt zuerst niedrigeren Hebel und danach geringeres Risiko pro Trade.
Der bestehende Optimizer-Score ist Tie-Breaker:

`leverage ASC, risk_per_trade ASC, score DESC`

### trade_rich

Bevorzugt Kandidaten mit mehr In-Sample-Trades. Der bestehende Optimizer-Score
ist Tie-Breaker:

`trade_count DESC, score DESC`

## Experimentdesign

Für ein Aktienuniversum:

1. historische Daten einmal vorbereiten;
2. Datenmanifest und Fingerprints als gemeinsame Referenz festhalten;
3. jedes Selection-Profil in einem eigenen Lauf ausführen;
4. pro Profil eigenen Run-Fingerprint, Run-Manifest, Checkpoint und Report speichern;
5. dieselben sieben bestehenden Research-Gates anwenden;
6. Gate-Ergebnisse nicht abschwächen oder umsortieren;
7. nur die dokumentierten Profilunterschiede miteinander vergleichen.

Ein Datenqualitäts- oder technischer Block beendet die Profilserie an dieser
Stelle und bleibt für Resume offen. Ein gültiges Research-Ergebnis mit
Gate-Ablehnung wird als `REJECT` des Profils dokumentiert.

## Interpretation

Ein Profil ist kein Beweis für eine bessere Strategie. Relevant ist, ob die
Veränderung der Auswahlregel die Out-of-Sample-Evidenz gegenüber dem
Kontrollprofil systematisch verändert.

Insbesondere wird geprüft, ob weniger randnahe Kandidaten geringere
In-Sample-Extremwerte und zugleich stabilere WFO-/Rolling-WF-/Robustheits- und
Holdout-Ergebnisse zeigen.

Alle Resultate bleiben Paper-/Simulationsforschung.
