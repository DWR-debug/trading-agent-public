# Samsung Android / Termux phone-resource integration template

Stand: 2026-10-02

## Zweck

Dies ist die wiederverwendbare Integrationsvorlage fuer weitere Samsung-/Android-Geraete im Trading-Agent-OS. S10 ist die Referenzimplementierung; neue Telefone erhalten keinen eigenen wissenschaftlichen oder architekturellen Sonderpfad.

## Ressourcenprofil

Vor Inbetriebnahme werden nur diese Felder parametrisiert:

- PHONE_RESOURCE_ID: stabile interne Kennung, z. B. SAMSUNG-PHONE-01
- PHONE_RUNNER_NAME: eindeutiger GitHub-Runnername, z. B. SAMSUNG-PHONE-01-TERMUX
- PHONE_RUNNER_LABEL: eindeutiges GitHub-Label, z. B. samsung-phone-01
- PHONE_MODEL: optionaler lokaler Modell-/Aliaswert; nicht als Research-Ergebnis verwenden
- PHONE_INTERFACE_PATH: lokale Descriptor-Datei, Standard ~/.trading-agent/phone_interface.json
- PHONE_ARCH: erwartete Architektur ARM64/aarch64
- PHONE_RUNTIME: Termux + proot-distro/Ubuntu

Geraetemodell, IMEI, Seriennummern, private IPs, Registrierungstokens, API-Keys und andere Geheimnisse werden nicht in Repository-Receipts oder Konfigurationsdateien geschrieben.

## Standard-Onboarding

1. Termux und proot-distro bereitstellen.
2. Das Skript scripts/samsung_termux_phone_runner_template.sh verwenden.
3. PHONE_RESOURCE_ID, PHONE_RUNNER_NAME und PHONE_RUNNER_LABEL auf einen freien Slot setzen.
4. prepare ausfuehren.
5. runtime ausfuehren. Das richtet einen bounded lokalen llama.cpp/Qwen-Stack ein und bleibt auf Loopback begrenzt.
6. register ausfuehren. Das GitHub-Registrierungstoken wird interaktiv lokal eingegeben und nicht gespeichert.
7. start ausfuehren und Termux mit Wake-Lock aktiv lassen.

Die ersten drei vorbereiteten Fleet-Slots stehen in ops/android_phone_resources.json. Sie sind fuer drei physisch getrennte Telefone gedacht und nutzen die eindeutigen Labels samsung-phone-01, samsung-phone-02 und samsung-phone-03.

## Referenzvertrag


Die S10-Referenzinstanz bleibt technisch reproduzierbar unter den bekannten lokalen Loopback-Endpunkten `127.0.0.1:8765` (Bridge) und `127.0.0.1:8080` (lokaler Inferenzdienst). Die gemeinsame Acceptance-Spezifikation ist Version `2026-10-02-R3`.

## Technische Acceptance

Ein neues Telefon wird erst als nutzbare Ressource akzeptiert, wenn live nachgewiesen ist:

- Termux/Ubuntu-Userland laeuft;
- ARM64/aarch64 ist bestaetigt;
- lokaler Interface-Endpunkt ist vorhanden;
- Endpunkt ist loopback-only;
- bounded Smoke Request funktioniert;
- fester 36-Faelle-Evidence-Critic-Lauf ist vollstaendig typisiert;
- sechs Option-Order-Checks bleiben invariant;
- Seed 271828, Threads 1, Temperature 0 und Top-K 1 sind der feste Runtime-Vertrag;
- keine Credentials landen in Receipts;
- PAPER_ONLY=True, LIVE_TRADING_ENABLED=False, ORDERS_ENABLED=False und AUTOMATIC_PROMOTION=False bleiben unveraendert.

Die Acceptance ist ausschliesslich ein Capability-/Utility-Nachweis. Sie ist keine Trading-Evidence, keine Performance-Autorisierung, keine Kandidatenselektion und keine Promotion.

## Automatisches Routing

Die generische Spur .github/workflows/android-phone-fleet-worker.yml laeuft alle sechs Stunden und kann manuell gestartet werden. Der Planungsjob prueft vor der Matrix-Erzeugung, welche konfigurierten eindeutigen Runner-Labels online sind. Offline-Geraete erzeugen dadurch keine wartenden Android-Jobs.

Nach jedem abgeschlossenen Fleet-Lauf synchronisiert .github/workflows/android-phone-fleet-receipt-sync.yml den technischen Status unter ops/android_phone_runtime_status/. Nur ein aktueller ANDROID_PHONE_UTILITY_ACCEPTED-Receipt setzt eligible=true.

## GitHub-Routingprinzip

Self-hosted Runner werden ueber die Standardlabels self-hosted, linux und ARM64 sowie ein zusaetzliches eindeutiges Geraetelabel adressiert. Das erlaubt mehrere gleichartige ARM64-Telefone ohne Vermischung der Ressourcen.

## S10 als Referenzinstanz

S10 bleibt separat in .github/workflows/s10-phone-worker.yml und ops/s10_runtime_status.json verankert. Der generische Fleet-Pfad ist fuer zusaetzliche Geraete gedacht und soll die S10-Instanz nicht duplizieren.

Bei zusaetzlichen Geraeten bleiben Protocol, Receipt-Struktur, Governance und Safety-Invarianten gleich. Nur Ressourcenidentitaet und lokale Hardware-/Runtimeparameter unterscheiden sich.

## Fehlerdiagnose

TERMUX_NOT_CONFIRMED -> Userland/Python pruefen.
RUNNER_OFFLINE -> Termux offen halten, Wake-Lock setzen, run.sh neu starten.
INTERFACE_NOT_REACHED -> lokalen Stack/Bridge auf 127.0.0.1 pruefen.
ANDROID_PHONE_UTILITY_NOT_ACCEPTED -> keine Research-Routing-Freigabe erteilen; konkrete Acceptance-Pruefung und Receipt analysieren.
ANDROID_PHONE_UTILITY_ACCEPTED -> Ressource ist fuer bounded technische/Review-Aufgaben verwendbar.

## Kanonische Dateien

- docs/SAMSUNG_ANDROID_TERMUX_PHONE_TEMPLATE.md
- docs/SAMSUNG_ANDROID_PHONE_FLEET.md
- scripts/samsung_termux_phone_runner_template.sh
- ops/android_phone_resources.json
- ops/android_phone_runtime_status/
- .github/workflows/android-phone-fleet-worker.yml
- .github/workflows/android-phone-fleet-receipt-sync.yml
- automation/evidence_critic_benchmark.py
- automation/s10_local_stack.py als aktuelle lokale Stack-Implementierung der Referenzinstanz

Die Vorlage ist bewusst generisch. S10 bleibt eine Referenzinstanz und kein Sonderfall der wissenschaftlichen Orchestrierungslogik.
