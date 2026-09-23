# Research Runbook

## Ziel

Ein Research-Lauf ist erst vollständig, wenn Daten, Code, Protokoll, Parameterraum, Safety-Zustand, Gates und Ergebnis eindeutig zusammengehören.

Der Ablauf bleibt vollständig Paper-Only.

## Erster Lauf auf dem Research-Gerät

Nach dem Checkout des freigegebenen `master`:

```bash
cd ~/trading-agent && git pull --ff-only origin master && git status --short
```

Sicherheit und Tests:

```bash
cd ~/trading-agent && python - <<'PY'
from config import settings
assert settings.PAPER_ONLY is True
assert settings.LIVE_TRADING_ENABLED is False
print("PAPER-ONLY OK")
PY
python -m pytest -q
```

Historische Research-Daten vorbereiten:

```bash
cd ~/trading-agent && python -m automation.prepare_research_data --target-count 10000
```

Research-Lauf mit unveränderlicher Run-Identität starten:

```bash
cd ~/trading-agent && export GIT_COMMIT_SHA="$(git rev-parse HEAD)" && python -m automation.research_workflow
```

Das Ergebnis wird unter `reports/` gespeichert. Zusätzlich entstehen:
- `research/data_manifest.json`
- `research/run_manifest.json`
- `research/checkpoints/latest.json`

## Resume nach Unterbrechung

Wichtig: Vor einem Resume **keine neuen Research-Daten erzeugen**.

Zuerst:

```bash
cd ~/trading-agent && export GIT_COMMIT_SHA="$(git rev-parse HEAD)" && python -m automation.research_workflow --resume
```

Der Resume wird automatisch verweigert, wenn sich Dataset, Datenmanifest, Code-Version, Research-Protokoll, Parameterraum oder sicherheitsrelevante Konfiguration verändert haben.

## Neuer Research-Lauf

Für einen bewusst neuen Lauf einen neuen Manifest-/Checkpoint-Pfad verwenden, statt einen bestehenden Lauf zu überschreiben.

Beispiel:

```bash
cd ~/trading-agent && export GIT_COMMIT_SHA="$(git rev-parse HEAD)" && python -m automation.research_workflow --manifest research/run_manifest_$(date +%Y%m%d_%H%M%S).json --checkpoint research/checkpoints/run_$(date +%Y%m%d_%H%M%S).json
```

Vor einem neuen Lauf müssen die Daten bewusst als neuer Research-Input vorbereitet und validiert werden.

## Interpretation

`PASSED` bedeutet ausschließlich, dass die definierten Research-Gates bestanden wurden.

`BLOCKED` bedeutet, dass mindestens ein Gate nicht bestanden wurde. Ein blockiertes Ergebnis wird nicht als belastbarer Research-Checkpoint behandelt.

Kein einzelner Backtest oder einzelner Research-Lauf ist eine Grundlage für Live-Handel.

## GitHub Actions

Nach Freigabe des Research-Workflow-PR kann ein vollständiger ARM64-Research-Lauf auch manuell über GitHub Actions gestartet werden:

```bash
cd ~/trading-agent && gh workflow run research-run.yml --ref master -f target_count=10000
```

Die Actions-Ausführung sichert Datenmanifest, Run-Manifest, Checkpoint, Reports und Research-Daten als Artifact.

Auch dort gilt: Paper-Only bleibt zwingend aktiv.
