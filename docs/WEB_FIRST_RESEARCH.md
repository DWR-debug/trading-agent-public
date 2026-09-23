# Web-basierte Research-Umgebung

## Codespaces

Das Repository enthält eine Dev-Container-Konfiguration für GitHub Codespaces.

Die Entwicklungsumgebung basiert auf Python 3.13, installiert pytest automatisch und aktiviert Python-/Pylance-Unterstützung.

## ARM64 Research Smoke Test

Der ARM64-Workflow läuft bei Pull Requests gegen master sowie manuell über workflow_dispatch.

Er prüft ARM64, die vollständige Pytest-Suite, die Paper-Trading-Sicherheitswerte und den vollständigen lokalen Research-Pfad inklusive finalem Holdout.

Der Test verwendet keine API-Schlüssel, keine Börsenorders und keine Live-Ausführung.

## Dauerhafter Research-Betrieb

Die permanente autonome Research-Schleife bleibt separat deaktiviert. Für lange Läufe unterstützt der Research-Runner atomare Checkpoints zwischen Datensätzen und kann mit resume=True fortgesetzt werden.

Ein eigener dauerhaft verfügbarer ARM64-Runner bleibt als spätere kostensensitive Ausführungsumgebung vorgesehen.

Die Smoke-Tests sind Infrastruktur- und Reproduzierbarkeitstests, kein Profitabilitätsnachweis.
