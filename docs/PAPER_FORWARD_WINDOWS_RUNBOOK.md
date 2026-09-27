# Windows operation: GitHub runner and paper-forward shadow

## GitHub Actions runner

The self-hosted runner uses the label `trading-agent-research` and exists for
QA/engineering. It is not the paper portfolio process.

From PowerShell, the repository includes a deterministic status check:

```powershell
cd <repository>
.\scripts\check_github_runner.ps1
```

The script distinguishes:

- `RUNNING` / `RUNNING_AS_SERVICE`: an active runner process/service exists.
- `INSTALLED_BUT_NOT_RUNNING`: `actions-runner` is installed, but no runner is active.
- `NOT_CONFIGURED`: no usable runner installation was found.

The runner diagnostic logs are under `$HOME\actions-runner\_diag`.
Keep separate PowerShell commands separated by a newline; concatenating
`-Force` with the next `Get-ChildItem` command produces a parameter-binding error.

For an interactive runner session:

```powershell
cd $HOME\actions-runner
.\run.cmd
```

## Paper-forward process

The paper-forward loop is independent of the Windows self-hosted runner. Python-based validation/execution is hosted on GitHub-hosted Windows runners. It reads one frozen
candidate, fetches only completed public Binance candles, updates the persistent
schema-v2 shadow state and repeats.

One-shot initialization:

```powershell
python -m automation.paper_forward_loop `
  --candidate .\frozen_candidate.json `
  --state .\paper_forward\shadow.json `
  --receipt .\paper_forward\feed_receipt.json `
  --max-iterations 1
```

Continuous mode:

```powershell
python -m automation.paper_forward_loop `
  --candidate .\frozen_candidate.json `
  --state .\paper_forward\shadow.json `
  --receipt .\paper_forward\feed_receipt.json
```

The state file is the durable operational record. A process restart resumes
from the existing state. On resume, the saved, fully validated candidate
provides the polling interval; the original candidate file is not needed.
After initialization, a missing state fails closed instead of starting a new
session. Restore the matching state backup to recover, or deliberately use a
new state and receipt path to start an independent session.

The process takes exclusive state and receipt locks and exits clearly if
another process holds either lock. Adjacent `.lock` files are persistent lock
targets and must not be removed while a paper-forward process may be running.
An adjacent `.initialized.json` marker preserves the session identity so that
deleting or moving only the state cannot silently reset the session.

The loop contains no broker, account credential, order, promotion or
research-evidence path.

## Safety

The process fails closed unless:

`PAPER_ONLY=True`

`LIVE_TRADING_ENABLED=False`

`ORDERS_ENABLED=False`

`AUTOMATIC_PROMOTION=False`

The reference 500 EUR is simulation capital only.
