# Mobile Edge Worker Konzept — Trading Agent
Stand: 2026-09-30

## Ziel

Zwei alte Android-Telefone werden als kostenlose, dauerhafte Edge-Knoten genutzt.
Sie ersetzen weder die deterministische Research-Engine noch die beiden Windows
Self-Hosted Runner. Ihre Aufgabe ist billige Dauerbeobachtung, kleine
Vorverarbeitung, Health/Watchdog-Funktionen und später kleine lokale KI.

Die wissenschaftliche Wahrheit bleibt ausschließlich in den deterministischen
Research-Pipelines, Evidence-Artefakten und dem Trial Ledger.

## Architektur

Windows Runner 1 + 2
  -> primäre lokale Research-/QA-Kapazität

GitHub-hosted Runner
  -> reproduzierbare CI, formale Performance-Gates, immutable Reconciliation

Mobile Edge 01
  -> Data Sentinel + Heartbeat + leichte Vorverarbeitung

Mobile Edge 02
  -> Watchdog + unabhängige Reproduktion kleiner Checks + später lokale KI

edge-control branch
  -> getrennte Control Plane für Mobile Tasks, Heartbeats und Resultate
  -> niemals wissenschaftlicher Evidence- oder Produktionspfad

master
  -> unverändert wissenschaftlicher Truth Source
  -> keine Mobile-Heartbeat-Commits auf master

## Phase 1 — morgen

Nur diese Komponenten:

1. Termux
2. Termux:Boot
3. optional Termux:API
4. ein dediziertes Fine-grained GitHub Token für
   DWR-debug/trading-agent-public mit nur "Contents: read/write"
5. das mitgelieferte Bootstrap-Skript

Das Token darf nicht in Git, Chat, Issues oder Logs geschrieben werden.
Das Bootstrap-Skript speichert es ausschließlich lokal in einer Datei mit
Berechtigung 600.

Termux:Boot startet nach Android-Neustart das Edge-Programm wieder. Die
offizielle Termux-Dokumentation empfiehlt dafür ~/.termux/boot/ und optional
termux-wake-lock. Termux kann ohne Root genutzt werden. Siehe:
https://github.com/termux/termux-boot
https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md

## Mobile Rollen

### Edge 01 — Data Sentinel

- sammelt öffentliche Daten-/Quellen-Metadaten
- prüft Erreichbarkeit und HTTP-Status
- erzeugt Hashes/kleine Manifeste
- meldet Änderungen an die Edge-Control-Plane
- keine Performance-Bewertung

### Edge 02 — Watchdog / Reproducer

- Heartbeat
- überprüft GitHub-/Control-Plane-Erreichbarkeit
- reproduziert kleine deterministische Python-Checks
- später lokale Inferenz kleiner quantisierter Modelle
- keine Promotion, keine Order-Ausführung

Die Rollen werden nur logisch unterschieden; fällt ein Telefon aus, kann das
andere die Basisfunktionen übernehmen.

## Phase 2 — nach erfolgreichem Hardware-Profil

Nach dem ersten Heartbeat entscheidet die Orchestrierung anhand von:

- Android-Version
- ARM ABI
- RAM
- CPU-Modell
- verfügbarer Speicher
- Ladezustand / Stromversorgung

ob lokale LLM-Inferenz sinnvoll ist.

Für Android unterstützt llama.cpp aktuelle ARM64/arm64-v8a-Builds; Termux
kann dafür ohne Root verwendet werden. Der Kontext sollte zunächst klein
gehalten werden, weil große Kontexte den RAM-Verbrauch stark erhöhen können:
https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md

Wir installieren ein Modell daher erst nach dem Hardware-Profil und wählen die
kleinste für die Aufgabe ausreichende Variante.

## Phase 3 — private Edge-Netzwerk-Schicht

Optional verbinden wir Telefone und Heim-PC zusätzlich per Tailscale. Der
aktuelle Personal-Tarif ist kostenlos und unterstützt laut Anbieter unbegrenzt
viele Benutzergeräte; das kostenlose Personal-Angebot ist für persönliche
Nutzung gedacht:
https://tailscale.com/pricing

Vorteile:

- kein Port-Forwarding
- sichere private Verbindung
- späterer Zugriff auf einen lokalen Modellserver
- einfacher Fernwartungsweg

Tailscale ist Zusatz, nicht Voraussetzung für Phase 1.

## Kostenlose KI-Strategie

Die KI wird in drei Rollen eingesetzt:

1. Scout — neue Hypothesen und Frontier-Ideen
2. Adversary — Gegenargumente, Fehler- und Leak-Suche
3. Local Edge — kleine lokale Modelle für billige Vorarbeit

### Primäre externe Free-Tier-Kandidaten

Gemini:
- Google dokumentiert aktuell kostenlose API-Nutzung für bestimmte Gemini-
  Modelle, darunter Gemini 3.7 Flash.
- Für den Free Tier weist Google darauf hin, dass Daten zur Verbesserung der
  Produkte verwendet werden können.
- Für sensible Daten werden diese kostenlosen Zugänge daher nicht genutzt.
Quelle:
https://ai.google.dev/gemini-api/docs/pricing

OpenRouter:
- aktueller Free-Plan: 25+ kostenlose Modelle
- 50 Requests/Tag
- keine Kreditkartenzahlung im Free-Plan
Quelle:
https://openrouter.ai/pricing

Mistral:
- aktueller Free-Plan enthält begrenzte Nutzung von Le Chat/Vibe und
  Mistral Studio sowie aktuell ausgewiesene API-Gutschriften.
Quelle:
https://mistral.ai/pricing/

Für die Automatisierung gilt weiterhin: kein Paid Fallback, keine automatische
Promotion und kein KI-Output als wissenschaftlicher Beweis.

## Operator-Aufwand

Nach der Einrichtung soll der normale Betriebsaufwand gegen null gehen.

Der Benutzer muss nur:

- die zwei Telefone dauerhaft mit Strom versorgen,
- WLAN aktiv lassen,
- Termux/Termux:Boot von aggressiver Akkuoptimierung ausnehmen,
- bei einem Android-Update einmal den Heartbeat-Status prüfen.

Die Geräte können nachts weiterlaufen. Bei thermischer oder batteriebedingter
Belastung wird die lokale KI automatisch zurückgestellt; Heartbeat/Watchdog
bleiben priorisiert.

## Was niemals auf dem Telefon gespeichert wird

- Broker-Schlüssel
- Live-Trading-Credentials
- Private Research-Geheimnisse
- Chat-Inhalte
- persönliche Dokumente
- kostenpflichtige API-Credentials

Das Mobile-System bleibt paper-only und unterstützt ausschließlich Forschung,
Datenbeobachtung und Infrastruktur.
