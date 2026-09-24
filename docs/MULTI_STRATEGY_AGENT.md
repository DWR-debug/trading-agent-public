# Evidence-Gated Multi-Strategy Agent

## Ziel

Der Agent soll mehrere unabhängig entwickelte und validierte Strategien kombinieren können,
statt von einer einzelnen Strategie abhängig zu sein.

Mehrere Strategien bedeuten nicht automatisch mehr Robustheit. Eine Kombination kann durch
Korrelation, gemeinsame Drawdowns, Kosten und Selection-Bias schlechter werden. Deshalb wird
die Gesamtarchitektur separat validiert.

## Entscheidungsprinzip

Marktdaten → Zustands-/Regimebeobachtung → Strategie-Eignung → Evidenzfilter → Allokation →
Risikokontrolle → Paper-Ausführung.

Die Zustands-/Regimebeobachtung ist eine eigene Forschungsaufgabe. Der aktuelle Allokator macht
keine Behauptung, dass bestimmte Marktmerkmale einen Regimewechsel zuverlässig vorhersagen.

## Evidence Gate

Jede Strategie benötigt einen expliziten evidence-eligible Status.

Eine nicht ausreichend validierte Strategie bekommt keine Exposition, unabhängig davon, wie
attraktiv ihr Signal erscheint.

Sind keine Strategien evidenz-eligible oder ergeben alle gültigen Eignungsscores null, lautet
die Entscheidung: **100 % Cash / keine neue Exposition.**

Der Agent ist damit ausdrücklich nicht verpflichtet, ständig zu handeln.

## Adaptive Allokation

Für jede evidenz-eligible Strategie werden Eignung und Signal-Confidence als Inputs verarbeitet.
Die Gewichtung wird relativ zwischen geeigneten Strategien verteilt und durch einen Gesamt-
Exposure-Cap sowie optionale Strategie-Caps begrenzt.

Die Eignungswerte selbst dürfen später nur aus einer separat validierten Zustands-/Regimekomponente
oder aus klar definierten, strategieinternen Signalen kommen.

Es gibt aktuell keine Behauptung, dass diese Allokationsform bereits einen wirtschaftlichen
Vorteil nachgewiesen hat.

## Forschungsregeln

Eine zukünftige adaptive Strategieauswahl muss mindestens gegen folgende Kontrollen getestet
werden:

1. feste Kombination der gleichen Strategien;
2. unabhängige Einzelstrategien;
3. konservative Cash-Alternative;
4. realistische Kosten und Slippage;
5. neue, vollständig disjunkte Validierungssätze.

Holdout-Ergebnisse dürfen weder zur Gewichtung noch zur Regimeklassifikation verwendet werden.

## Sicherheitsprinzip

Bei Datenfehlern, widersprüchlichen Zuständen oder unzureichender Evidenz muss die Architektur
die Exposition reduzieren oder auf Cash fallen.

Keine Komponente dieses Moduls setzt Live-Trading voraus oder ermöglicht Live-Orders.
