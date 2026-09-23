# Forschungsprotokoll

Die Research-Engine verwendet einen festen Ablauf, damit Auswahl und finale Validierung zeitlich getrennt bleiben.

## Datenaufteilung

Die neuesten 10 % des Datensatzes bilden einen unangetasteten finalen Holdout.

- Optimizer sieht nur die ersten 90 %.
- Walk-Forward und Rolling-Walk-Forward sehen nur die ersten 90 %.
- Erst nachdem der Walk-Forward-Kandidat ausgewählt wurde, wird er auf dem Holdout geprüft.
- Forschung und Holdout werden im Report mit getrennten Zeitgrenzen und SHA-256-Fingerprints dokumentiert.

Damit kann der finale Holdout nicht zur Parameterwahl verwendet werden.

## Ausführungsmodell

Für Research werden explizit folgende Kostenannahmen protokolliert:

- Fee: 0,10 % pro ausgeführter Seite
- Slippage: 0,05 % pro Seite

Der Robustheits-Stresstest multipliziert beide Annahmen mit 1,5.

## Sensitivität und Robustheit

Die Robustheitsprüfung verändert einzelne Strategieparameter lokal und prüft, ob die positive OOS-Leistung auf mehrere benachbarte Einstellungen verteilt ist. Zusätzlich wird das Kostenmodell gestresst.

## Randomisierung

Für den finalen Holdout wird bei mindestens 10 Trades zusätzlich eine deterministische Sign-Permutationsdiagnose mit 1000 Versuchen und festem Seed gespeichert.

Dieser Wert ist ausdrücklich **kein eigenständiges Research-Gate**. Er dient als Diagnose, weil eine Sign-Permutation nur bestimmte Nullannahmen über die Trade-Verteilung untersucht.

## Harte Research-Gates

Ein Kandidat muss sieben Gates bestehen:

1. Datenqualität
2. Baseline-Backtest
3. Walk-Forward
4. Rolling Walk-Forward
5. Robustheit
6. Overfit
7. finaler Holdout

Bei einem Fehlschlag lautet der Status BLOCKED. Ein BLOCKED-Ergebnis darf nicht als validiertes Research-Ergebnis geschrieben werden.

Die Gates sind Mindesthürden, kein Beweis zukünftiger Profitabilität.

Die permanente autonome Research-Schleife bleibt separat deaktiviert.
