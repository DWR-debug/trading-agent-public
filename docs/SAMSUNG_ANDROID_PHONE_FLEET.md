# Samsung Android Phone Fleet — Betriebsmodell

Stand: 2026-10-02

## Zweck

Mehrere Samsung-Telefone werden als getrennte ARM64/Termux-Ressourcen betrieben. Jedes Telefon erhält einen eigenen GitHub-Runnernamen und ein eigenes eindeutiges Label. Die technische Acceptance bleibt für alle Geräte identisch, wird aber nur bei Onboarding oder expliziter Revalidierung ausgeführt.

## Reservierte Slots

Die Datei `ops/android_phone_resources.json` enthält drei vorbereitete Slots:

- `SAMSUNG-PHONE-01` → `samsung-phone-01`
- `SAMSUNG-PHONE-02` → `samsung-phone-02`
- `SAMSUNG-PHONE-03` → `samsung-phone-03`
- `SAMSUNG-PHONE-04` → `samsung-phone-04`
- `SAMSUNG-PHONE-05` → `samsung-phone-05`

Ein Slot wird nur dann benutzt, wenn auf dem Telefon ein Runner mit genau diesem Label online ist. Die Planung unterscheidet zusätzlich nach Receipt-Status: ein unbekanntes/nicht akzeptiertes Gerät bekommt Acceptance; ein bereits akzeptiertes Gerät bekommt Utility-Arbeit. Damit werden vorbereitete oder offline Geräte nicht künstlich beschäftigt.

## Onboarding

1. Auf dem Telefon Termux und `proot-distro` bereitstellen.
2. Die generische Vorlage `scripts/samsung_termux_phone_runner_template.sh` in das lokale Repository kopieren oder aus dem Repository ausführen.
3. `PHONE_RESOURCE_ID`, `PHONE_RUNNER_NAME` und `PHONE_RUNNER_LABEL` passend zu einem freien Slot setzen.
4. `prepare` und `register` ausführen. Das GitHub-Registrierungstoken wird ausschließlich interaktiv lokal eingegeben und danach aus der Shell entfernt.
5. `start` ausführen und das Telefon am Strom lassen; `termux-wake-lock` wird vom Template genutzt, sofern verfügbar.

Für eine erste technische Acceptance ist kein Modellname im Repository erforderlich. Der lokale bounded Stack kann den Standard-Qwen-Worker verwenden oder einen kompatiblen Worker setzen. Modellwahl und Gerätemodell sind keine wissenschaftlichen Ergebnisse.

## Automatisierung

`.github/workflows/android-phone-fleet-worker.yml` ist die generische Fleet-Spur. Sie läuft alle sechs Stunden sowie manuell und plant nur Geräte ein, deren eindeutiger Runner online ist. Das Routing nutzt die Standardlabels `self-hosted`, `linux`, `ARM64` plus das individuelle Geräte-Label. Akzeptierte Geräte erhalten dabei die kleine Utility-Review-Spur statt des vollständigen 36-Fälle-Benchmarks.

Nach erfolgreicher Acceptance erzeugt die Receipt-Synchronisation einen gerätespezifischen Status unter `ops/android_phone_runtime_status/`. Utility-only Läufe ergänzen diesen Status, ohne eine gültige Acceptance zurückzunehmen. Der Status ist ein technischer Capability-Nachweis und keine Research-Evidence.

## Technische Akzeptanz

Die erstmalige technische Acceptance besteht aus dem vollständig typisierten 36-Fälle-Evidence-Critic-Lauf mit sechs Option-Order-Checks, Loopback-Grenze, festen Reproduzierbarkeitsparametern und den unveränderten Governance-Invarianten. Danach werden für den Regelbetrieb kleine bounded Utility-/QA-Aufgaben verwendet. Eine erneute 36-Fälle-Acceptance erfolgt nur bei expliziter Revalidierung oder nach einem technischen Integritätsereignis. Ein Offline-Telefon wird fail-closed behandelt.

GitHub dokumentiert für self-hosted Runner die Standardlabels `linux` und `ARM64` und erlaubt zusätzliche benutzerdefinierte Labels; ein Job bleibt in der Warteschlange, wenn kein passender Online-Runner vorhanden ist. Die Fleet-Planung filtert Offline-Geräte deshalb bereits vor der eigentlichen Job-Erstellung. citeturn612040search0turn612040search2

## Rolle im Trading-Agent-OS

Telefonressourcen sind bounded Compute/QA-Unterstützung. Sie dürfen weder Performance autorisieren noch Holdouts auswählen, Kandidaten ranken, Promotion auslösen oder Live-Orders ausführen.

Weitere Research-Unterstützung wird erst nach technischer Acceptance und nur innerhalb der bestehenden Orchestrierungs- und Provenienzverträge geroutet. Für zusätzliche Geräte gilt ein kontrollierter Kapazitätstest: zunächst genau ein neues Gerät, anschließend nur bei messbarem zusätzlichem Nutzen gegenüber der vorhandenen Compute-Kapazität.
