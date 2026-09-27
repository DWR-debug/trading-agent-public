# Technische Review: autonomer Paper-Forward-Loop und Windows-Betrieb

**Task:** AGENT-020 / Issue #354  
**Taskvertrag:** `TRADING_AGENT_TASK_V1`, `task_id=AGENT-020`  
**Prüfdatum:** 2026-09-27  
**Reviewmodus:** report-only; keine Code-, Evidence-, Gate- oder Promotion-Änderung  
**Geprüfter PR:** #352, Merge-Commit `a1536a2531ff8341b2ab25a8cdd0012a22e3e3ba`  
**Verifizierter Checkout:** `master` / `origin/master`, Commit `6d557b58a2d7c1af6a5dc66090ccb2fcb2852221`

## Ergebnis

**Technisches Gesamturteil: bedingt belastbar als interaktiver Paper-Prozess; nicht
ausreichend gehärtet für unbeaufsichtigten Dauerbetrieb auf einem Windows-PC.**

Der Loop hat eine sinnvolle sichere Grundarchitektur: Er lädt nur öffentliche,
abgeschlossene Binance-Candles, persistiert den Zustand pro Update durch
Dateiaustausch, prüft gespeicherte Eingaben/Fingerprints und rekonstruiert das
Portfolio aus den Candle-Daten. Ein Neustart kann eine gültige laufende Session
fortsetzen, wenn der State und die Kandidatendatei vorhanden sind und der
Datenfeed die Lücke innerhalb des Abruffensters schließt.

Die Grenzen sind operativ relevant: Ein Fehler nach ausgeschöpften Feed-Retries
beendet den Prozess; ein fehlender State löst einen neuen Bootstrap statt eines
erkennbaren Resume-Fehlers aus; und parallele Prozesse werden nicht verhindert.
Das Windows-Runbook startet den Prozess interaktiv und richtet keinen
Autostart-/Restart-Supervisor ein. Damit ist der Loop für beobachteten
Paper-Betrieb nutzbar, aber seine autonome Kontinuität hängt weiterhin an
Betreiber, PC, Stromversorgung, Netzwerk und korrekter Dateiverwaltung.

## Geprüfter Umfang

- `automation/paper_forward_loop.py`
- `automation/paper_forward_market_feed.py`
- `automation/paper_forward_shadow.py`
- `data/binance_loader.py`
- `docs/PAPER_FORWARD_SHADOW_MODE.md`
- `docs/PAPER_FORWARD_WINDOWS_RUNBOOK.md`
- `scripts/check_github_runner.ps1`
- `.github/workflows/paper-forward-self-hosted-validation.yml`
- fokussierte Tests unter `tests/test_paper_forward_{loop,market_feed,shadow,mtm}.py`

Der PR ist in den geprüften `master`-Checkout eingeflossen. Der PR-Merge-SHA war
im lokalen, flach geklonten Git-Verlauf nicht vorhanden; PR-Metadaten bestätigen
den oben genannten Merge-Commit. Die Dateien des gemergten Features sind im
Checkout vorhanden.

## Positive Kontrollen

### Persistenz, Resume und Input-Integrität

`start_session` legt eine Session nur an, wenn die State-Datei noch nicht
existiert. `update_session` liest den vorhandenen State, validiert Safety-Werte,
Kandidat, Candles, Status, Fingerprints und rekonstruiertes Portfolio und
akzeptiert nur unveränderte Overlap-Candles sowie lückenlose Anhänge. Dadurch
werden beschädigte oder inkonsistente Zustände abgelehnt statt still
weitergerechnet. Der State wird in ein eindeutiges temporäres File im selben
Verzeichnis geschrieben und anschließend mit `os.replace` ausgetauscht.

Die Tests belegen Resume und Idempotenz auf der Zustandsmaschinenebene:
identische Candles erzeugen keine zweite Verarbeitung, ein geänderter
historischer Candle wird abgelehnt, und ein manipulierter MTM-State wird
zurückgewiesen. Ein Abbruch mit Ctrl+C lässt eine `RUNNING`-State-Datei zurück,
die grundsätzlich fortsetzbar ist.

### Polling und Datenfeed

Die Standardwartezeit ist intervalbasiert und auf 30 bis 900 Sekunden begrenzt.
Der Feed entfernt offene Candles und sortiert die abgeschlossenen Daten.
Der vorhandene Binance-Loader nutzt einen öffentlichen Market-Data-Endpunkt
ohne API-Key und versucht temporäre HTTP-, Netzwerk- und Timeout-Fehler bis zu
viermal mit Backoff erneut. Der Shadow-Update-Pfad selbst erzwingt
Kontinuität und lehnt Vendor-Revisionen bereits beobachteter Candles ab.

### Sicherheitsgrenzen

Die vier Paper-only-Invarianten werden am Laufzeitpfad geprüft und im State
festgehalten. In den geprüften Komponenten gibt es keinen Broker-Client,
Account-Credential-, Order-, Research-Evidence-, Gate- oder Promotion-Pfad.
Das Validierungsworkflow-Token ist auf `contents: read` begrenzt. Die
Dokumentation ordnet den Self-hosted GitHub-Runner korrekt von der lokalen
Paper-Forward-Ausführung getrennt ein.

## Technische Befunde

### F-01 – Mittleres Risiko: Feed-Fehler beenden den Loop, und lange Ausfälle
werden nicht automatisch aufgeholt

**Nachweis:** `run_loop` ruft `run_once` direkt ohne Fehlerbehandlung,
Wiederholungswartezeit oder Neustartkontrolle auf. Der Binance-Loader hat zwar
begrenzte Retries; wenn diese erschöpft sind, propagiert der Fehler bis zum
Loop und beendet den Prozess. Der Standardwert von `fetch_limit` ist 100
(maximal 1.000). Nach einer längeren Offline-Zeit kann das geladene Fenster
Candles nach dem letzten gespeicherten Candle enthalten, ohne unmittelbar
daran anzuschließen. `update_session` lehnt diese Lücke korrekt fail-closed
ab, der Dauerprozess endet dadurch aber ebenfalls.

**Auswirkung:** Ein vorübergehender API-/Netzwerkfehler oder ein PC-Ausfall kann
manuelle Wiederaufnahme erfordern. Bei einem Ausfall, der das Abruffenster
überschreitet, reicht ein Neustart mit Standardwerten nicht zuverlässig zum
Resume; die Session bleibt an der Kontinuitätsprüfung stehen. Der sichere
Reject verhindert erfundene Zwischenstände, ersetzt aber keine
Betriebswiederherstellung.

**Empfehlung:** Den Loop mit einer klar begrenzten, sichtbaren Retry-/Backoff-
Strategie für temporäre Feedfehler betreiben, ohne ungültige Updates zu
verschlucken. Für Gap-Recovery einen expliziten, begrenzten historischen
Catch-up-Pfad oder eine dokumentierte manuelle Recovery-Prozedur vorsehen, die
alle Zwischen-Candles validiert und den bestehenden State nicht zurücksetzt.
Der Prozessstatus und der letzte erfolgreiche Candle-Zeitpunkt sollten
operatorseitig sichtbar sein.

### F-02 – Mittleres Risiko: Fehlender State wird als neue Session initialisiert

**Nachweis:** `run_once` behandelt `not state.exists()` als regulären
Erststart und ruft `start_from_binance` auf. Derselbe Pfad wird auch vom
endlosen Loop verwendet. Es gibt kein separates Initialisierungs-Flag oder
einen zusätzlichen Marker, der erkennt, dass diese State-Datei zuvor schon
existiert hat.

**Auswirkung:** Wird der State versehentlich gelöscht, verschoben oder wird
beim Neustart ein falscher Pfad angegeben, startet der Prozess eine frische
Session aus der Kandidatendatei und einer neuen Warm-up-Historie. Das ist kein
Resume der alten Session; ein neuer Run-/Candle-Verlauf kann als Fortsetzung
fehlinterpretiert werden. Die `run_id` hängt vom Kandidaten-Fingerprint und
dem ersten Warm-up-Candle ab und ist daher nicht zwingend verschieden. Die
alte Session wird nicht überschrieben, wenn sie nur verschoben wurde, ist aber
nicht mehr mit dem angegebenen Pfad verbunden.

**Empfehlung:** Initialisierung und Resume als getrennte Betriebsaktionen
ausweisen. Nach erfolgter Initialisierung sollte ein fehlender State ohne
expliziten neuen Startauftrag fail-closed enden; Session-ID und letzter
bekannter Zeitstempel sollten in einer unabhängigen, ebenfalls persistenten
Betriebsmarkierung oder einem kontrollierten Backup nachvollziehbar bleiben.

### F-03 – Mittleres Risiko: Keine Instanzsperre für Read-modify-write

**Nachweis:** `run_loop` reserviert oder sperrt den State-Pfad nicht. Zwei
gleichzeitig gestartete Instanzen können denselben State lesen, unabhängig
Candles/Portfolio berechnen und jeweils atomar ersetzen. Der State-Austausch
ist gegen Teil-Dateien geschützt, aber nicht gegen konkurrierende Updates.
Auch der Receipt-Schreiber verwendet einen festen temporären Namen
(`.<receipt>.tmp`) und besitzt keine Konkurrenzsperre.

**Auswirkung:** Bei zwei Instanzen kann ein späterer Austausch den Fortschritt
der anderen Instanz überschreiben. Je nach Timing führt das zu verlorenem
Fortschritt, erneuter Verarbeitung oder einem später fail-closed erkannten
Candle-Gap. Der feste Receipt-Temp-Pfad kann parallel ebenfalls kollidieren.
Die Behauptung eines einzelnen Runner-Prozesses ist keine technische
Exklusivsperre für den lokalen Paper-Forward-Prozess.

**Empfehlung:** Vor State-/Receipt-Änderungen eine plattformübergreifende
exklusive Prozesssperre auf dem State-Pfad erwerben und bei belegter Sperre
klar abbrechen. Die Sperre muss bei Prozessende freigegeben werden. Tests
sollten zwei konkurrierende Starts/Updates und den Sperrfreigabepfad prüfen.

### F-04 – Niedriges Risiko: Resume hängt unnötig von der externen
Kandidatendatei ab

**Nachweis:** `run_loop` lädt die Kandidatendatei vor dem Eintritt in die
Schleife zwingend und verwendet deren Intervall für die Pollingzeit. Ist
bereits ein State vorhanden, lädt `run_once` den Kandidaten dagegen aus dem
State und ignoriert `candidate_path` für das Update.

**Auswirkung:** Ein vorhandener gültiger State allein reicht für den Start
nicht, wenn die ursprüngliche Kandidatendatei fehlt oder nicht mehr lesbar
ist. Wird versehentlich eine andere gültige Kandidatendatei übergeben, pollt
der Loop nach deren Intervall, während der Feed weiter mit dem im State
gespeicherten Kandidaten arbeitet. Das kann unnötig häufiges oder zu seltenes
Polling erzeugen.

**Empfehlung:** Beim Resume Polling-Intervall aus dem validierten State
ableiten. Falls die Kandidatendatei weiterhin als unabhängige
Betreiberbestätigung benötigt wird, deren Fingerprint mit dem gespeicherten
Kandidaten vergleichen und bei Abweichung fail-closed abbrechen.

### F-05 – Betriebsgrenze: Windows-Runbook startet keinen unbeaufsichtigten
Dienst

**Nachweis:** `PAPER_FORWARD_WINDOWS_RUNBOOK.md` dokumentiert einen
interaktiven PowerShell-Aufruf. Es gibt in den geprüften Dateien keine
Windows-Service-, Task-Scheduler-, Autostart-, Restart- oder Logging-
Konfiguration für `paper_forward_loop.py`. `scripts/check_github_runner.ps1`
prüft nur den Status des GitHub-Actions-Runner-Prozesses/-Dienstes und startet
nicht den Paper-Forward-Loop. Der Hosted-Validation-Workflow führt einen
begrenzten Smoke-Test auf `windows-latest` aus; er ist kein persistenter
Ausführungsdienst für den lokalen Prozess.

**Auswirkung:** Der dokumentierte Betrieb funktioniert, solange die
interaktive Sitzung, Python-Umgebung, Dateien, Stromversorgung und
Netzwerkverbindung verfügbar bleiben. Abmelden, Schlafmodus, Neustart oder
ein nicht behandelter Prozessfehler unterbrechen die Beobachtung. Ein
manueller Neustart kann den State erhalten, ist aber keine automatische
Wiederanlaufgarantie.

**Empfehlung:** Falls unbeaufsichtigter Betrieb gewünscht ist, eine separate
Windows-Betriebsaufgabe für Start bei Boot/Anmeldung, Restart bei Fehler,
definiertes Shutdown-Verhalten und begrenzte Logs dokumentieren und testen.
Diese Aufgabe muss den bestehenden paper-only-Pfad verwenden und darf keine
Broker-, Order- oder Promotion-Integration einführen. Alternativ sollte die
Dokumentation den Betrieb ausdrücklich als interaktiv und betreuerabhängig
kennzeichnen.

### F-06 – Niedrige Provenienzgrenze: Receipt und State sind kein gemeinsamer Commit

**Nachweis:** `update_from_binance` persistiert zuerst den aktualisierten
Shadow-State über `update_session` und schreibt anschließend optional den
Feed-Receipt in eine separate Datei.

**Auswirkung:** Schlägt das Receipt-Schreiben fehl, ist der State bereits
fortgeschrieben, während der Aufrufer einen Fehler erhält und der Loop
terminiert. Bei einem Receipt-Pfad wie im Runbook kann der Receipt somit
hinter dem State zurückbleiben. Der State selbst bleibt gültig und ein
Neustart kann fortsetzen; die beiden Dateien stellen aber keine atomare
gemeinsame Provenienz dar.

**Empfehlung:** Den Receipt an die resultierende State-Fingerprint-/Zeitmarke
binden und den zweistufigen Commit im Betriebsvertrag ausdrücklich abbilden.
Ein Receipt-Fehler muss sichtbar bleiben, darf aber nicht den Eindruck
erzeugen, der State sei nicht aktualisiert worden.

## Bewertung der angeforderten Prüfpunkte

| Prüfpunk | Bewertung |
|---|---|
| Neustart/Resume | **Bedingt bestanden** – State-Prüfung und Resume sind für vorhandenen gültigen State belegt; fehlender Kandidat verhindert Resume (F-04), fehlender State kann still neu initialisieren (F-02). |
| Polling | **Grundsätzlich bestanden** – intervalbasierter Poll mit 30–900 Sekunden; nach Fehler kein äußerer Retry (F-01). |
| Fehler/Folgefehler | **Teilweise bestanden** – Loader hat begrenzten Backoff und State-Update fail-closed; Loop endet bei ausgeschöpften Retries/Gaps, Receipt kann nach State-Commit fehlschlagen (F-01, F-06). |
| Zustandsintegrität | **Teilweise bestanden** – Validierung, Recompute und atomarer einzelner State-Austausch sind stark; fehlender State und konkurrierende Prozesse bleiben ungesichert (F-02, F-03). |
| Sichere Beendigung | **Bedingt bestanden** – Ctrl+C lässt den letzten State unangetastet und ein `RUNNING`-State ist fortsetzbar; kein Supervisor/Shutdown-Management ist eingerichtet (F-05). |
| PC-/Runner-Abhängigkeit | **Klar getrennt, aber lokal betreuerabhängig** – der Loop läuft unabhängig vom GitHub-Runner; ein dauerhafter lokaler Betrieb setzt PC, Python, Dateien und Netzwerk voraus (F-05). |
| Broker-/Order-/Promotion-Pfade | **Bestanden nach statischer Prüfung** – in den geprüften Forward-Komponenten nicht vorhanden; Safety-Invarianten bleiben streng. |
| Praktischer Dauerbetrieb | **Eingeschränkt** – interaktiver Dauerlauf ist möglich, unbeaufsichtigter, selbstheilender Windows-Betrieb ist nicht eingerichtet. |

## Ressourcen- und Verifikationsgrenzen

- Der fokussierte Engineering-Testlauf
  `python -m pytest -q tests/test_paper_forward_shadow.py tests/test_paper_forward_market_feed.py tests/test_paper_forward_loop.py tests/test_paper_forward_mtm.py`
  bestand mit **15 Tests** in 0,13 Sekunden auf Checkout
  `6d557b58a2d7c1af6a5dc66090ccb2fcb2852221`.
- Der Testlauf nutzte keine Live-Marktdaten und führte keine deterministische
  Research-Berechnung oder wissenschaftliche Selektion aus.
- GitHub Actions-/Runner-Liveinformationen und der Status eines konkreten
  Windows-PCs waren in dieser Umgebung nicht zugänglich. Der aktuelle
  Repository-Status dokumentiert eine QA-Architektur mit einem beanspruchten
  Runner-Prozess; das ist keine Live-Prüfung der Erreichbarkeit.
- Copilot-CLI war für diese Review verfügbar. Cloud-Agent-Entitlement,
  Self-hosted-Runner-Livezustand und lokale Windows-Service-Konfiguration
  wurden nicht als verfügbar angenommen oder verwendet. Paid usage: keine.
- Der Windows-spezifische Ablauf wurde statisch anhand des Runbooks und des
  PowerShell-Skripts geprüft; der Python-Testlauf fand nicht auf Windows statt.

## Sicherheits- und Scope-Abschluss

Die Review nimmt keine Code-, Research-, Evidence-, Gate-, Holdout-,
Parameter-, Asset-, Promotion- oder Live-Ausführungsänderung vor. Die
Sicherheitsinvarianten bleiben:

```text
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
orders_enabled=False
automatic_promotion=False
```

Die Befunde sind technische Betriebsrisiken und keine wissenschaftliche
Evidenz oder Promotionentscheidung. Die Review-Datei ist der einzige
vorgesehene Handoff-Artefaktpfad für Issue #354.
