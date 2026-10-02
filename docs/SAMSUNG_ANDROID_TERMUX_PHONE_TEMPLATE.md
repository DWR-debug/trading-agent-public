# Samsung Android / Termux phone-resource integration template

Stand: 2026-10-02

## Zweck

Dieses Dokument ist die wiederverwendbare Vorlage fuer weitere Samsung-/Android-Geraete im Trading-Agent-OS.

S10 ist die Referenzimplementierung, aber die OS-Integration darf nicht von einem bestimmten Samsung-Modell, einer bestimmten Modellfamilie oder einem Windows-Prozess abhaengen. Das Geraet gilt erst als nutzbar, wenn sein eigener Termux-/ARM64-Runtimepfad live nachgewiesen wurde.

## Geraeteprofil

Vor Inbetriebnahme werden nur diese Eigenschaften parametrisiert:

- \`PHONE_RESOURCE_ID\`: stabile interne Kennung, z. B. \`S10\`, \`S11\`
- \`PHONE_RUNNER_NAME\`: GitHub-Runnername, z. B. \`S11-TERMUX\`
- \`PHONE_RUNNER_LABEL\`: eindeutiges GitHub-Label, z. B. \`s11-phone\`
- \`PHONE_ARCH\`: erwartete Architektur; ARM64/aarch64 fuer den vorgesehenen Android-Pfad
- \`PHONE_RUNTIME\`: \`Termux + proot-distro/Ubuntu\`
- \`PHONE_ROLE\`: bounded research / QA / Evidence-Critic-Unterstuetzung
- \`PHONE_INTERFACE\`: ausschliesslich lokales/loopback S10-kompatibles Interface

Geraetemodell, IMEI, Seriennummern, private IPs, Tokens und andere Geheimnisse werden nicht in Repository-Receipts oder Konfigurationsdateien geschrieben.

## Standardpfad

1. Termux installieren/aktualisieren und \`proot-distro\` verfuegbar machen.
2. Ubuntu-Userland erzeugen.
3. Python, curl, ca-certificates, git und tar installieren.
4. Den GitHub Actions ARM64 Runner vorbereiten.
5. Den Runner mit einem eindeutigen Geraetenamen und Label registrieren; der Registrierungstoken wird nur interaktiv lokal eingegeben.
6. Termux-Wake-Lock aktivieren und Runner starten.
7. Der Workflow \`S10 Phone Research Worker\` bzw. dessen generischer Nachfolger laedt exakt den Ziel-Commit.
8. Der lokale Inferenz-Stack wird bounded wiederhergestellt: llama.cpp auf \`127.0.0.1\`, fester kleiner GGUF-Worker, feste Reproduzierbarkeitsparameter.
9. Runtime-Probe, Interface-Smoke und der feste Evidence-Critic-Benchmark werden ausgefuehrt.
10. Erst bei \`UTILITY_ACCEPTED\` darf die Ressource fuer bounded Forschung geroutet werden.

## Akzeptanzvertrag

Eine Telefonressource ist technisch akzeptiert, wenn mindestens nachgewiesen ist:

- Termux/Ubuntu-Userland laeuft;
- ARM64/aarch64 ist bestaetigt;
- ein lokaler Interface-Endpunkt ist vorhanden;
- der Endpunkt ist loopback-only;
- ein bounded Smoke Request beantwortet wird;
- ein fester 36-Faelle-Evidence-Critic-Lauf vollstaendig typisiert und reproduzierbar ist;
- die sechs Option-Order-Checks bleiben invarianten;
- Seed/Threads/Temperature/Top-K sind fest und receipt-faehig;
- keine Credentials in Receipts landen;
- \`PAPER_ONLY=True\`, \`LIVE_TRADING_ENABLED=False\`, \`ORDERS_ENABLED=False\`, \`AUTOMATIC_PROMOTION=False\`.

Die technische Akzeptanz sagt nichts ueber Trading-Performance aus. Das Telefon darf keine wissenschaftliche Evidence, keine Performance-Autorisierung, keine Kandidatenselektion, kein Ranking, keine Promotion und keine Live-Ausfuehrung erzeugen.

## Wiederverwendung fuer S11/S12/...

Fuer das naechste Samsung-Geraet wird nicht ein neuer Integrationspfad entwickelt. Stattdessen werden nur die vier Ressourcenfelder aus dem Profil gesetzt und die bestehende Runner-/Runtime-Prozedur wiederverwendet.

Der lokale Stack darf ein anderes kompatibles Modell nutzen, wenn dessen Interface und Reproduzierbarkeit separat verifiziert werden. Eine Modellwahl ist kein wissenschaftliches Ergebnis und darf nicht als solches in den Research-Ledger einfliessen.

## S10 als Referenz

S10 ist derzeit die Referenzimplementierung dieses Templates:

- Runner: \`S10-TERMUX\`
- Label: \`s10-phone\`
- Architektur: ARM64
- lokaler Bridge-Port: \`127.0.0.1:8765\`
- lokaler llama.cpp-Port: \`127.0.0.1:8080\`
- Utility Acceptance Contract: \`2026-10-02-R3\`

Bei zukuenftigen Geraeten bleiben Protokoll, Governance und Receipt-Struktur gleich; nur Geraeteidentitaet und lokale Ressourcenparameter werden ersetzt.

## Schnelle Fehlerdiagnose

\`TERMUX_NOT_CONFIRMED\` -> Userland/Python pruefen.

\`RUNNER_OFFLINE\` -> Termux offen halten, Wake-Lock setzen, \`run.sh\` neu starten.

\`INTERFACE_NOT_REACHED\` -> lokalen Stack/Bridge auf \`127.0.0.1\` pruefen.

\`BENCHMARK_NOT_ACCEPTED\` -> keine Forschung routen; Receipt und konkrete Vertragsverletzung pruefen.

\`UTILITY_ACCEPTED\` -> Ressource ist fuer bounded technische/Review-Aufgaben verwendbar.

## Kanonische Dateien

- \`docs/S10_TERMUX_PHONE_INTEGRATION.md\`
- \`scripts/samsung_termux_phone_runner_template.sh\`
- \`automation/s10_probe.py\`
- \`automation/s10_runtime.py\`
- \`automation/s10_acceptance.py\`
- \`ops/s10_runtime_status.json\`

Die Vorlage ist bewusst generisch: S10 bleibt eine Instanz, kein Sonderfall in der Orchestrierungslogik.
