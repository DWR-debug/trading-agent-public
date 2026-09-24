# Multi-Strategie-Architektur – Forschungsauftrag

## Ziel

Der Agent soll mehrere unabhängig entwickelte und validierte Strategien kombinieren können, statt von einer einzelnen Strategie abhängig zu sein.

Die zentrale Hypothese lautet nicht, dass jede Marktsituation zuverlässig vorhersehbar ist. Ziel ist eine **evidenzgesteuerte adaptive Architektur**, die aus mehreren komplementären Strategien die aktuell zulässige Exposition bestimmt und bei unzureichender Evidenz defensiv bleiben kann.

## Architekturprinzip

Marktdaten → Zustands-/Regimeanalyse → Kandidatenstrategien → Evidenzfilter → Strategie-Allokation → Portfolio-Risikokontrolle → Paper-Ausführung → Monitoring → Kapital-/Gewinnbuchführung.

Jede Stufe muss separat testbar sein.

## Wissenschaftliche Regeln

Eine Strategie darf nur dann als adaptive Kandidatenstrategie verwendet werden, wenn ihr eigener Research-/Holdout-Pfad belastbare Evidenz geliefert hat.

Eine Regime- oder Zustandslogik ist selbst eine Forschungs-Hypothese. Sie erhält keine Sonderbehandlung und muss unabhängig validiert werden.

Die adaptive Auswahl darf nicht anhand von Holdout-Ergebnissen kalibriert werden.

Die Gesamtarchitektur muss zusätzlich gegenüber einer festen Gleichgewichtung bzw. einer fest vorgegebenen Kombination getestet werden, damit ein vermeintlicher Vorteil der dynamischen Auswahl nicht lediglich Selection-Bias widerspiegelt.

## Sicherheitsprinzip

Bei widersprüchlichen Signalen, unzureichender Evidenz, Datenfehlern oder überschrittenen Risiko-Grenzen gilt fail-closed:

**Exposition reduzieren oder nicht handeln.**

Der Agent erhält keine Pflicht, jederzeit eine Strategie zu aktivieren.

## Forschungsziel

Gesucht wird nicht die Strategie mit der höchsten isolierten Rendite, sondern die Kombination, die unter den festgelegten Sicherheits- und Robustheitsgrenzen die nachhaltigste, realistisch entnehmbare Ertragsfähigkeit des Gesamtportfolios unterstützt.

Die konkrete Strategieanzahl, Allokationslogik und Regimeerkennung werden erst durch präregistrierte Experimente festgelegt.
