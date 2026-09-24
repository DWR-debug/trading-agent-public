# Trial 017 — Political Event Intelligence

## Pilotstand

Der historische Pilot verwendet ausschließlich internationale Ereignisse mit
beiden Actor-Country-Codes befüllt und mindestens 3 erwähnenden Artikeln. Diese
Qualitätsregel folgt einem dokumentierten GDELT-Analysebeispiel; sie ist für den
Pilot fest und wird nicht optimiert.

## Point-in-Time

Die tägliche GDELT-Archivdatei verwendet das 58-Spalten-Format; DATEADDED ist dabei das vorletzte Feld und wird als UTC-Timestamp verarbeitet. Ein Ereignis am Handelstag D wird mit dem ersten
Markttag strikt nach D verbunden. Fällt D auf ein Wochenende oder einen
Marktfeiertag, wird der letzte Schluss vor D als Ausgangspunkt für die nächste
Marktbewegung verwendet. Die Performance des Ereignistags wird nicht als
Auswahlkriterium verwendet.

Der Fünf-Tage-Horizont ist der fünfte Markt-Tag strikt nach D.

## Controls

Der Bericht enthält zusätzlich eine Marktbasis über alle verfügbaren
Handelstage und die Differenz der Ereignistagsmittelwerte zur Marktbasis.
Damit wird nicht nur „Konflikttage gegen Nicht-Konflikttage“ betrachtet.

## Forschungsstatus

Der Pilot ist ein deskriptiver Control. Er darf weder Produktionsparameter
noch die Portfolioallokation verändern. Ein positives Ergebnis ist noch kein
handelbarer Edge.