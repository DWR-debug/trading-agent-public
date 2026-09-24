# Trial-/Selection-Ledger und PBO/DSR-Evidenz

Der Research-Prozess besitzt jetzt ein explizites Ledger für durchgeführte
Experimente. Ziel ist, Selection Bias nicht nur konzeptionell, sondern als
Teil der dauerhaften Evidenzhistorie zu behandeln.

## Grundprinzip

Jeder Research-Versuch erhält eine unveränderliche `trial_id` und dokumentiert:

- Hypothese und Research-Familie;
- Daten- und Holdout-Scope;
- Suchumfang;
- deklarierte unabhängige Trials;
- Selection-Methode und Selection-Familie;
- verfügbare PSR-/DSR-/PBO-Evidenz;
- Safety-Status.

Nicht bekannte Größen bleiben `null`. Sie werden nicht aus der Anzahl von
Parametern oder PRs rekonstruiert.

## DSR

Die vorhandene DSR-Implementierung kann jetzt über das Ledger explizit mit
der tatsächlich ausgewerteten Trial-Familie verbunden werden.

Ein DSR-Wert darf nur eingetragen werden, wenn die Trial-Sharpe-Familie und die
deklarierte Zahl unabhängiger Trials vorliegen.

## PBO

Das Ledger enthält einen Consumer für bereits berechnete CSCV-Splits. Für jeden
Split wird der OOS-Rang des IS-Gewinners in die Logit-Größe umgerechnet; PBO ist
der Anteil negativer Logits.

Die CSCV-Aufteilung selbst bleibt bewusst außerhalb dieses Consumers. Damit ist
nicht vorgetäuscht, dass eine beliebige Zeitreihe automatisch eine korrekte
CSCV-Partition erzeugt.

Die Literatur beschreibt DSR als Korrektur für Selection Bias und
Nicht-Normalität und CSCV/PBO als explizite Overfit-Diagnostik. citeturn230838search0turn230838search1

## Keine automatische Freigabe

PBO/DSR sind Evidenz- und Diagnostikgrößen. Sie ersetzen weder
Holdout-/Rolling-/Robustheits-Gates noch den BLOCKED-Status eines Kandidaten.

Ein fehlender Trial-Sharpe-Satz führt zu `ready=False`, nicht zu einer
Schätzung oder Annahme.
