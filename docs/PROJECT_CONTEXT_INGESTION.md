# Chat-Kontext-Import und Kontextpflege

## Zweck

Dieses Dokument beschreibt, wie noch vorhandene Chats in den dauerhaften Projektkontext überführt werden,
ohne technische oder wissenschaftliche Tatsachen zu vermischen.

## Unterstützte Quellen

Der bisher verfügbare Kontext ist in `docs/CHAT_CONTEXT_2026_09_24.md` als Ausgangsbestand dokumentiert.

1. Chat-Evidenz, die in der aktuellen Unterhaltung zugänglich ist.
2. Vorherige Projektzusammenfassungen oder Kontextinformationen, die in der Unterhaltung verfügbar sind.
3. Vom Benutzer bereitgestellte Chat-Exporte, Transkripte oder relevante Ausschnitte.
4. Repository-Diskussionen wie PR-/Issue-Kommentare, soweit sie tatsächlich abgerufen werden können.

Ein vollständiger Zugriff auf alle historischen Chatverläufe des Kontos ist nicht vorausgesetzt.

## Klassifikation jedes Imports

Jeder neue Inhalt wird einer der folgenden Klassen zugeordnet:

- **TECHNICAL_FACT** — überprüfbare technische Tatsache; maßgebliche Prüfung gegen GitHub.
- **PROJECT_DECISION** — gemeinsam festgelegte Entwicklungsentscheidung.
- **RESEARCH_HYPOTHESIS** — frühere oder neue Forschungsannahme.
- **RESEARCH_EVIDENCE** — Ergebnis eines tatsächlich ausgeführten Experiments.
- **DESIGN_PRINCIPLE** — langfristige Architektur-/Governance-Regel.
- **IDEA_ONLY** — diskutierte Möglichkeit ohne formale Umsetzung.

## Prioritätsregel

Ein Chat darf einen Repository-Fakt nicht einfach überschreiben.

Beispiel:
„Workflow X läuft auf Commit A“ aus einem alten Chat wird als historische Aussage behandelt.
Steht der aktuelle Workflow nachweislich auf Commit B, ist B die technische Gegenwart; die alte Aussage
bleibt bei Bedarf als historische Kontextinformation erhalten.

Umgekehrt darf ein technischer Repository-Fakt nicht die gemeinsame Zielsetzung oder eine bewusst
getroffene Projektentscheidung löschen.

## Empfohlene Importstruktur

Für größere Chatimporte:

### Quelle
Datum / Chat / Themenbereich

### Aussage
Belastbare Kurzfassung oder kurzer Originalausschnitt.

### Typ
TECHNICAL_FACT / PROJECT_DECISION / RESEARCH_HYPOTHESIS /
RESEARCH_EVIDENCE / DESIGN_PRINCIPLE / IDEA_ONLY

### Status
AKTUELL / ÜBERHOLT / WIDERLEGT / OFFEN

### Verknüpfung
Betroffene Trial-ID, Datei, Commit, PR oder Dokumentation.

### Kommentar
Warum diese Information für die heutige Architektur noch relevant ist.

## Umgang mit langen historischen Chats

Nicht jede Chatzeile muss dauerhaft gespeichert werden.

Priorität haben:

- langfristige Projektziele;
- Sicherheitsregeln;
- methodische Entscheidungen;
- verworfene Ansätze und deren Gründe;
- wichtige architektonische Entscheidungen;
- Erkenntnisse, die spätere Forschungsfragen beeinflussen;
- Hinweise auf Dateien, Runs, Artefakte und Branches.

Reine Gesprächsfloskeln oder bereits vollständig reproduzierbare technische Details müssen nicht dupliziert werden.

## Regel gegen Rückwirkungs-Bias

Ein späterer Chat darf keinen historischen Trial nachträglich „besser“ machen.

Insbesondere:

- kein nachträgliches Tuning;
- keine rückwirkende Parameterwahl;
- keine Holdout-Auswahl;
- keine Umbenennung eines verworfenen Trials in einen Erfolg.

Historische Chatbeobachtung darf eine **neue**, klar getrennte Hypothese motivieren;
sie darf nicht den alten Trial stillschweigend verändern.
