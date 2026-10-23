# Project 500 — Ausführungsplan und dauerhafter Handoff

**Version:** 1.0  
**Effective:** 2026-10-23  
**Strategische Priorität:** Primary  
**Finanzielle Ausgaben vor Liquiditätsklärung:** EUR 0  
**Nächste Review:** 2026-10-30  
**30-Tage-Entscheidungsfenster:** bis 2026-11-22 (kein Einkommensversprechen)

## Ziel und Nicht-Ziele

Ziel ist eine realistische, kostengünstige Suche nach einer KI-gestützten Dienstleistung oder einem kleinen Produkt, das ein konkretes Kundenproblem löst und sich gegebenenfalls zu zusätzlichem Einkommen entwickeln kann. Langfristige familiäre Sicherheit darf nicht davon abhängen, dass Trading profitabel wird.

Nicht-Ziele: garantierte Einnahmen, eine „revolutionäre“ Idee behaupten ohne Marktvalidierung, ein großes SaaS-Produkt vor Kundenkontakt bauen, mit bezahlten Tools oder Werbung auf Verdacht starten, Haushaltsrücklagen riskieren, oder einen Trading-Backtest als Einkommen behandeln.

## Kapitalregel

Der Nutzer hat 500 EUR nominales Startkapital genannt. Es ist noch nicht geklärt, ob das Geld frei verfügbar oder die gesamte Rücklage ist. Deshalb gelten vor einer Klärung:

- bestätigtes frei disponierbares Kapital: 0 EUR;
- autorisierte diskretionäre Ausgaben: 0 EUR;
- keine Trading-Einsätze, Darlehen, bezahlten APIs/Software, Werbung oder Registrierungsausgaben aus diesem Betrag;
- vorerst nur kostenlose Recherche, öffentliche Daten, Kundeninterviews ohne bezahlte Tools und Prototypen mit synthetischen oder redigierten Daten.

Der frühere 2.000-EUR-Wert im Trading-Agent-Projekt bleibt eine historische Simulationskonfiguration, keine Aussage über verfügbares Vermögen. Der 500-EUR-Trading-Canary war ebenfalls Simulation und darf nicht mit frei verfügbarem Kapital gleichgesetzt werden.

## Erste Recherche: belastbare Fakten und Aussagegrenzen

1. **KfW Research, 29. Juli 2026:** Rund 20 % der deutschen mittelständischen Unternehmen nutzen KI; Texterzeugung lag bei 14 %, Texterkennung bei 10 %, Data Analytics bei 3 %. In der KfW-Auswertung hängen Adoption und Einsatz stark mit Digitalisierungsgrad, Wissen und Innovationsaktivität zusammen. Das ist ein Anlass, nach praxisnahen Umsetzungsproblemen zu suchen, aber kein Beweis dafür, dass ein neues Angebot zahlende Kunden findet.  
   Quelle: https://www.kfw.de/%C3%9Cber-die-KfW/Newsroom/Aktuelles/News-Details_902336.html

2. **KfW-Digitalisierungsbericht Mittelstand 2025, veröffentlicht 23. April 2026:** 30 % der Unternehmen hatten zuletzt Digitalisierungsprojekte durchgeführt; die Aktivität sank auf Vor-Corona-Niveau. Dies stützt vorsichtige, kostentransparente Piloten statt groß angelegter Vorab-Implementierungen.  
   Quelle: https://www.kfw.de/%C3%9Cber-die-KfW/Newsroom/Aktuelles/News-Details_891136.html

3. **TED Search API / EU Public Procurement Data:** Offizielle veröffentlichte EU-Vergabebekanntmachungen können anonym durchsucht und als XML abgerufen werden. Das macht einen öffentlichen Prototyp technisch günstig möglich, deckt jedoch nicht automatisch alle deutschen lokalen Portale oder vertraulichen Vergabeunterlagen ab.  
   Quellen: https://docs.ted.europa.eu/api/latest/search.html und https://data.europa.eu/en/PPDS

4. **Starke Konkurrenz im Ausschreibungsmonitoring:** Aktuelle Anbieter veröffentlichen bereits kostenlose oder günstige Einstiegsangebote. Vergabeautomat nennt einen Free-Plan sowie Starter für 39 EUR/Monat; Auftrag One nennt Free sowie „Lokal“ für 49 EUR/Monat und „Pro“ für 99 EUR/Monat; Homeport AI nennt sein Ausschreibungsmonitor-Modul ab 390 EUR/Monat bei jährlicher Zahlung. Das sind Anbieterangaben, keine unabhängige Marktpreiserhebung. Ein generischer Ausschreibungsmonitor ist daher kein ungeprüfter Favorit; er bräuchte eine klar abgegrenzte Zielbranche oder einen nachgewiesenen Zusatznutzen jenseits von Suchalarmen.  
   Quellen: https://vergabeautomat.de/preise, https://auftragone.com/preise, https://homeport.ai/ausschreibungsmonitor

5. **BVMW, November 2025:** Die Empfehlungen zur KI-Implementierung betonen klare Ziele, Datenqualität und die Ausrichtung auf ein konkretes betriebliches Problem. Dies passt zu kleinen, menschlich geprüften Prozesspiloten und spricht gegen „KI um der KI willen“.  
   Quelle: https://www.bvmw.de/uploads/topics/Internet-und-Digitalisierung/Downloads/Impulspapier-KI-Implementierung-11-2025.pdf

### Aussagegrenze

Quellen belegen, dass KI-Anwendung und öffentliche Daten vorhanden sind und es Konkurrenzprodukte gibt. Sie belegen **nicht** unsere Zahlungsbereitschaft, die Kundenakquise, die individuelle Lieferfähigkeit oder irgendeine Erfolgswahrscheinlichkeit. Diese Lücken werden mit direkten Gesprächen und einem kleinen Test geprüft.

## Drei initiale Hypothesen (alle noch UNVALIDIERT)

Die vorläufige Reihenfolge bezieht sich nur auf die Kosten der Falsifikation und den Umfang eines ersten Piloten; sie ist weder Umsatzprognose noch Erfolgsranking.

### H1 — Ein enger Dokumenteneingang-zu-Arbeitsliste-Service

**Hypothese:** Kleine technische Dienstleister, Wartungs-/Montagebetriebe oder spezialisierte Händler verlieren regelmäßig Zeit, wenn Anfrage-E-Mails und angehängte PDFs in eine strukturierte Angebots-/Arbeitsvorbereitung übertragen werden müssen. Ein KI-unterstützter, menschlich geprüfter Dienst könnte strukturierte Entwürfe, fehlende Angaben und Rückfragen liefern, ohne verbindliche Angebote, Buchungen oder technische Sicherheitsentscheidungen autonom freizugeben.

**Was wir noch nicht wissen:** Wie oft geschieht der Vorgang? Wie viel Zeit kostet er? Ist er schmerzhaft genug, dass ein Betrieb dafür zahlt? Welche Software nutzt er bereits? Können wir die Sicherheit/Genauigkeit mit verfügbarer Expertise garantieren?

**Billigster Test:** Mit synthetischen Beispielen ein Ergebnis-Mock-up erstellen und 8–10 passende Betriebe zu ihrem letzten realen Prozess befragen. Zuerst Problem und Aufwand ermitteln, nicht eine Lösung verkaufen. Keine echten personenbezogenen oder vertraulichen Kundenunterlagen in öffentliche KI-Tools hochladen.

**Stop-Kriterien:** Kein wiederkehrender Schmerz, keine klare Zeit-/Qualitätswirkung, existierende Software löst das Problem ausreichend, oder Daten-/Qualitätsrisiken sind nicht mit einem menschlichen Freigabeschritt beherrschbar.

### H2 — Ein manuell geprüfter „Bid/No-Bid“-Kurzbericht für eine einzelne Nische

**Hypothese:** Eine eng definierte Anbietergruppe braucht nicht noch einen allgemeinen Alarmdienst, sondern eine kurze, nachvollziehbare Prüfung, warum eine bestimmte Ausschreibung zu ihrem Angebot passt oder nicht passt, welche Fristen gelten und welche Angaben noch fehlen.

**Quellen-/Technikvorteil:** TED bietet öffentliche Such-/Download-Schnittstellen. Originalquelle und Funddatum können bei jedem Treffer verlinkt werden.

**Wettbewerbsrisiko:** Es existieren bereits Gratisdienste und Abos ab 39–99 EUR pro Monat sowie höherpreisige Analyseprodukte. Wir sollten nur weitergehen, wenn Gespräche einen konkreten Nischenbedarf belegen, der von vorhandenen Tools nicht ausreichend bedient wird.

**Billigster Test:** 10 Interviews in genau einer Berufs-/Anbietergruppe; daraus manuell höchstens fünf beispielhafte, quellverlinkte Kurzberichte erstellen, zunächst anhand öffentlich zugänglicher Bekanntmachungen. Keine Aussage als Rechts-/Vergabeberatung, keine unbelegten „Gewinnchancen“, keine automatische Angebotsabgabe.

**Stop-Kriterien:** generische Alerts reichen aus; kein nachweisbarer Vorteil gegenüber Free-Tarifen; Datenabdeckung oder Aktualität nicht zuverlässig; niemand will einen konkreten Pilotpreis diskutieren.

### H3 — Kleiner KI-Workflow-Audit mit einem messbaren Vorher/Nachher

**Hypothese:** Kleine Unternehmen haben bereits einzelne KI-Werkzeuge, aber keinen klar eingegrenzten Arbeitsablauf, der messbar Zeit spart. Wir identifizieren einen einzigen Prozess, dokumentieren einen sicheren manuellen Ablauf und demonstrieren einen kleinen, kontrollierten Prototypen statt allgemeiner KI-Beratung.

**Differenzierung:** Keine generische „KI-Strategie“, kein behaupteter Expertenstatus. Ein Prozess, ein Ergebnisformat, ein vorher definierter Nutzenmaßstab und ein menschlicher Freigabeschritt.

**Billigster Test:** Kurze Interviews; erfragen, welcher wiederkehrende Vorgang zuletzt manuell erledigt werden musste und wie Erfolg gemessen würde. Kostenlose, begrenzte Demonstration mit synthetischen Daten. Erst dann über einen bezahlten Pilot sprechen.

**Risiko:** Breiter Wettbewerbsmarkt; Vertrauen und Glaubwürdigkeit entscheiden; das Angebot muss auf einer tatsächlichen, begrenzten Fähigkeit beruhen. Keine Behauptung, professionelle Rechts-, Steuer-, Sicherheits- oder Datenschutzberatung zu ersetzen.

## Die ersten 14 Tage

### Tage 1–3: Zielgruppe und Interviewfragen festlegen

- Gemeinsam eine erste Zielgruppe nach Zugänglichkeit und Prozesswiederholung auswählen; berufliche Erfahrung des Nutzers nicht voraussetzen.
- Für H1–H3 identische Kernfragen erstellen.
- Einen öffentlichen Quellen- und Wettbewerbsvergleich pro Hypothese ergänzen.
- Ein synthetisches Demo-Beispiel für H1 erstellen; kein produktionsreifes System bauen.

### Tage 4–7: Kundenproblem prüfen

- Mindestens 8–10 Gespräche anstreben, wenn erreichbare Personen dies ermöglichen.
- Fragen: „Welche Aufgabe wiederholt sich häufig?“, „Wie haben Sie den letzten Fall gelöst?“, „Wie viele Minuten/Stunden kostet sie?“, „Was läuft schief?“, „Welche Alternative nutzen Sie?“, „Haben Sie schon für eine Lösung gezahlt?“
- Kein Pitch vor der Bedarfsermittlung. Ergebnisse mit anonymisierten Notizen und klarer Trennung zwischen Zitat, Interpretation und Annahme dokumentieren.
- Kein Gespräch oder „Interesse“ als Zahlungsbeweis zählen.

### Tage 8–14: Entscheidung und kleiner Test

- Nur die Hypothese weiterverfolgen, bei der mehrere voneinander unabhängige Gesprächspartner einen konkreten wiederkehrenden Engpass beschreiben und die Alternative diesen nicht ausreichend löst.
- Ein kleines, von Menschen geprüftes Ergebnis manuell liefern; nur synthetische/redigierte Daten, sofern Datenschutz- und Verarbeitungsbedingungen nicht geklärt sind.
- Einen definierten Pilotumfang und eine transparente Preisfrage testen, ohne Erfolg zu versprechen.
- Wenn keine Hypothese ausreichend Nachfrage zeigt: dokumentiert stoppen oder die Zielgruppe ändern; noch kein Geld ausgeben.

## Arbeits-/Kontaktentwurf für Kundeninterviews

> Guten Tag, ich untersuche gerade, wie kleine Unternehmen einen bestimmten wiederkehrenden Büroprozess erledigen und wo dabei unnötiger Zeitaufwand entsteht. Ich entwickle noch keine fertige Software und möchte Ihnen zunächst nichts verkaufen. Dürfte ich Ihnen drei bis fünf kurze Fragen zu einem konkreten Ablauf stellen? Besonders hilfreich wäre ein Beispiel aus der letzten Woche: Was musste manuell übertragen, geprüft oder nachverfolgt werden, wie lange hat es gedauert und welche Lösung nutzen Sie heute? Ich interessiere mich für ehrliche Erfahrungen – auch wenn der Prozess bereits gut gelöst ist.

Dieser Text ist ein Entwurf. Es wurden keine Kontakte angeschrieben.

## Messregeln

Für jede Hypothese werden geführt: Belegquelle, Datum, Zielsegment, bestehende Alternativen, tatsächliche Gesprächszahl, Häufigkeit/Schwere des Problems, beobachteter Aufwand, Zahlungs-/Preisreaktion, Unsicherheiten, Datenschutz-/Rechtsrisiken, Testkosten und Stop/Continue-Entscheidung.

Nicht als Erfolg zählen: Website-Klicks ohne weiterführendes Verhalten, höfliches Lob, KI-generierte Marktbehauptungen, fertiger Code ohne Käufer, oder ein unverbindliches „könnte interessant sein“.

## Zuständigkeiten und Grenzen

- KI: Webrecherche, Quellenvergleich, hypothetische Marktmodelle, Interviewfragen, synthetische Demos, Prototyp-Code, kritische Gegenprüfung und Entscheidungsmemos.
- Nutzer: Auswahl der erreichbaren Zielgruppe, reale Gespräche und finale Geschäftsentscheidungen; keine Annahme über berufliche Expertise oder verfügbare Kontakte.
- Vor zahlender Geschäftstätigkeit: tatsächliche rechtliche, steuerliche, gewerbliche und vertragliche Voraussetzungen prüfen; keine Rechts-/Steuerberatung behaupten.
- Ausgaben: keine vor bestätigter Kapitalverfügbarkeit und gesonderter Entscheidung.
- Trading-Agent: sekundär; alle bestehenden Sicherheitsgrenzen bleiben verbindlich: PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, ORDERS_ENABLED=False, AUTOMATIC_PROMOTION=False.

## Erfolg bis Tag 30

Erfolg ist eine ehrliche, nach Quellen und Gesprächen nachvollziehbare Entscheidung: eine klar abgegrenzte, vom Markt gestützte Pilotidee weiterzuverfolgen, die Hypothese zu überarbeiten oder sie zu beenden. Eine Einnahme oder ein bezahlter Kunde ist ein Ziel, keine Garantie. Es werden keine Versprechen über Umsatz, Erfolgschancen oder dauerhafte finanzielle Sicherheit gemacht.

## Nächste Aktualisierung

Nach der ersten Nutzerklärung zur Kapitalverfügbarkeit: bestätigten Geldbetrag für mögliche Experimente festhalten (oder weiter bei EUR 0 bleiben), die drei Hypothesen nach den ermittelten Belegen aktualisieren und die ersten konkreten Zielgruppeninterviews vorbereiten. Dieses Dokument ist der dauerhafte Handoff für jeden neuen `trading agent`-Chat.
