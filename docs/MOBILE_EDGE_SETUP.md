# Mobile Edge — einfache Einrichtung
Stand: 2026-09-30

## Einmalige Vorbereitung am PC

1. In GitHub Settings -> Developer settings -> Personal access tokens ->
   Fine-grained personal access tokens einen Token nur für
   DWR-debug/trading-agent-public erstellen.
2. Repository access: nur dieses Repository.
3. Repository permissions: Contents = Read and write.
4. Keine Workflows-Berechtigung erteilen. Der Mobile Worker verändert keine
   .github/workflows-Dateien.

GitHub dokumentiert, dass "Contents: write" für Create/Update File Contents
ausreicht; Workflows write ist nur zusätzlich erforderlich, wenn Workflow-Dateien
verändert werden:
https://docs.github.com/en/rest/repos/contents

Das Token niemals in dieses Chatfenster schreiben.

## Pro Telefon

### 1. Installieren

Aus der offiziellen Termux-Quelle installieren:

- Termux
- Termux:Boot
- optional Termux:API

Termux ist auch über F-Droid erhältlich. Termux:Boot startet Skripte nach
einem Android-Neustart:
https://github.com/termux/termux-app
https://github.com/termux/termux-boot

### 2. Termux einmal öffnen

Auf jedem Telefon zuerst Termux starten.

Dann genau diese eine Zeile ausführen:

curl -fsSL https://raw.githubusercontent.com/DWR-debug/trading-agent-public/master/scripts/mobile_edge/bootstrap.sh | bash

Das Skript fragt nur zwei Dinge:
- Knoten-ID: Telefon 1 = edge01, Telefon 2 = edge02
- das dedizierte GitHub Token, unsichtbar bei der Eingabe

Danach werden die benötigten Termux-Pakete installiert, das Edge-Programm
eingerichtet, eine Boot-Startdatei erzeugt und ein erster Heartbeat verifiziert.

### 3. Termux:Boot einmal aktivieren

Termux:Boot öffnen und einmal starten.

Danach startet ~/.termux/boot/trading-agent-edge bei späteren Neustarts.

### 4. Android nicht schlafen lassen / Akkuoptimierung

Bei beiden Geräten Termux von aggressiver Akkuoptimierung ausnehmen. Die
offizielle Termux-Dokumentation weist darauf hin, dass manche Android-Geräte
Hintergrundprozesse sonst beenden:
https://github.com/termux/termux-app/wiki/RUN_COMMAND-Intent

Bei dauerhaftem Betrieb nach Möglichkeit am Ladegerät und im WLAN betreiben.

## Was danach automatisch passiert

Die Telefone bleiben auf der getrennten Branch "edge-control".

Sie lesen Aufgaben aus:

ops/mobile_edge/tasks/<node>.json

und schreiben Heartbeats/Resultate nach:

ops/mobile_edge/heartbeats/<node>.json
ops/mobile_edge/results/<node>/

Die wissenschaftliche master-Historie wird dadurch nicht mit Edge-Heartbeats
zugemüllt.

Der aktuelle Worker akzeptiert nur explizit implementierte Task-Typen. Es gibt
keine freie Shell-Ausführung aus dem Control Plane.

## KI erst nach Hardware-Profil

Nach dem ersten Heartbeat wird anhand von Android-Version, ARM64-ABI, RAM,
CPU und Speicher entschieden, ob lokale llama.cpp-Inferenz sinnvoll ist.

Für Android ist Termux + llama.cpp ohne Root dokumentiert; arm64-v8a wird
unterstützt:
https://github.com/ggml-org/llama.cpp/blob/master/docs/android.md

Wir installieren zuerst keinen großen lokalen LLM. Das Hardware-Profil
entscheidet über Modellgröße und Rolle.

## Optional: Tailscale

Tailscale kann später eine private Verbindung zwischen Telefonen und Heim-PC
bereitstellen. Der aktuelle Personal-Tarif ist kostenlos für persönliche
Nutzung und unterstützt laut Anbieter unbegrenzt viele Benutzergeräte sowie
bis zu sechs Benutzer:
https://tailscale.com/pricing

Das ist für Phase 1 nicht erforderlich.

## Zielbetrieb

Windows Runner 1 + 2:
- primäre lokale Research- und QA-Rechenleistung

GitHub-hosted:
- reproduzierbare formale CI/Performance/Reconciliation

Mobile Edge 01:
- Data Sentinel

Mobile Edge 02:
- Watchdog + kleine Reproduktion + später lokale KI

AI Free Tier:
- Gemini / OpenRouter / Mistral nur mit explizitem Free-only Gate
- kein Paid Fallback
- keine Credentials in Git
- KI-Output niemals wissenschaftliche Evidenz

## Sicherheitsgrenzen

Paper-only bleibt unverändert:

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
