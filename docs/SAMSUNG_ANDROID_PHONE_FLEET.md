# Samsung Android Phone Fleet — Betriebsmodell

Stand: 2026-10-02

## Zweck

Mehrere alte Samsung-Telefone werden als getrennte ARM64/Termux-Ressourcen betrieben. Jedes Telefon erhält einen eigenen GitHub-Runnernamen und ein eigenes eindeutiges Label. Die gleiche technische Acceptance bleibt für alle Geräte identisch.

## Reservierte Slots

Die Datei `ops/android_phone_resources.json` enthält drei vorbereitete Slots:

- `SAMSUNG-PHONE-01` → `samsung-phone-01`
- `SAMSUNG-PHONE-02` → `samsung-phone-02`
- `SAMSUNG-PHONE-03` → `samsung-phone-03`

Ein Slot wird nur dann tatsächlich benutzt, wenn auf einem Telefon ein Runner mit genau diesem Label online ist. Dadurch erzeugen vorbereitete, aber noch nicht vorhandene Telefone keine wartenden Jobs.

## Onboarding

1. Auf dem Telefon Termux und `proot-distro` bereitstellen.
2. Die generische Vorlage `scripts/samsung_termux_phone_runner_template.sh` in das lokale Repository kopieren oder aus dem Repository ausführen.
3. `PHONE_RESOURCE_ID`, `PHONE_RUNNER_NAME` und `PHONE_RUNNER_LABEL` passend zu einem freien Slot setzen.
4. `prepare` und `register` ausführen. Das GitHub-Registrierungstoken wird ausschließlich interaktiv lokal eingegeben und danach aus der Shell entfernt.
5. `start` ausführen und das Telefon am Strom lassen; `termux-wake-lock` wird vom Template genutzt, sofern verfügbar.

Für eine erste technische Acceptance ist kein Modellname im Repository erforderlich. Der lokale bounded Stack kann den Standard-Qwen-Worker verwenden oder einen kompatiblen Worker setzen. Modellwahl und Gerätemodell sind keine wissenschaftlichen Ergebnisse.

## Automatisierung

` .github/workflows/android-phone-fleet-worker.yml` ist die generische Fleet-Spur. Sie läuft alle sechs Stunden sowie manuell und plant nur Geräte ein, deren eindeutiger Runner online ist. Das Routing nutzt die Standardlabels `self-hosted`, `linux`, `ARM64` plus das individuelle Geräte-Label.

Nach erfolgreicher Acceptance erzeugt die Receipt-Synchronisation einen gerätespezifischen Status unter `ops/android_phone_runtime_status/`. Dieser Status ist ein technischer Capability-Nachweis und keine Research-Evidence.

## Technische Akzeptanz

Akzeptiert wird nur ein vollständig typisierter 36-Fälle-Evidence-Critic-Lauf mit sechs Option-Order-Checks, Loopback-Grenze, festen Reproduzierbarkeitsparametern und den unveränderten Governance-Invarianten. Ein Offline-Telefon wird fail-closed behandelt.

GitHub dokumentiert für self-hosted Runner die Standardlabels `linux` und `ARM64` und erlaubt zusätzliche benutzerdefinierte Labels; ein Job bleibt in der Warteschlange, wenn kein passender Online-Runner vorhanden ist. Die Fleet-Planung filtert Offline-Geräte deshalb bereits vor der eigentlichen Job-Erstellung. citeturn612040search0turn612040search2

## Rolle im Trading-Agent-OS

Telefonressourcen sind bounded Compute/QA-Unterstützung. Sie dürfen weder Performance autorisieren noch Holdouts auswählen, Kandidaten ranken, Promotion auslösen oder Live-Orders ausführen.

Weitere Research-Aufgaben werden erst nach technischer Acceptance und nur innerhalb der bestehenden Orchestrierungs- und Provenienzverträge geroutet.
