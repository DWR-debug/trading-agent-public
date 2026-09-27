# Continuous paper-forward operation

The project has a persistent operational paper portfolio that is separate
from research evidence. For unattended operation on the Windows PC, use the
owner-scoped Task Scheduler setup below. Its state is stored in the task user's
`%LOCALAPPDATA%`, outside the repository and Actions workspace. The existing
hosted workflow is a separate operational path; its schedule does not prove
that the local Windows process is installed or running.

Both paths use the frozen operational canary
paper-forward-operational-canary-btcusdt-1h-v1:
- BTCUSDT
- 1h closed candles
- EUR 500 hypothetical starting capital
- 1x leverage
- 10 bps fee
- 5 bps slippage
- existing strategy-engine parameters frozen in the candidate file

The process is not a broker connection. It never creates exchange orders and
does not write research/evidence or promotion state.

Each one-shot update:
1. checks all paper-only safety invariants;
2. restores the existing schema-v2 state if present, otherwise initializes it
   from a bounded historical Binance warm-up;
3. fetches only closed candles with a bounded fetch window;
4. applies the existing state/lock/fingerprint validation;
5. stores the updated state and feed receipt;
6. writes only the local operational state/receipt; the Windows wrapper also
   appends a bounded JSONL operations log with session, candidate/state
   fingerprints, last committed candle and error state.

A missed schedule does not create synthetic candles. The Windows wrapper
requests at most 100 recent closed candles per run. This is a bounded recovery
window, not permission to skip gaps: if the returned data cannot bridge every
missing candle, the existing updater fails closed and does not advance the
state. The next scheduled invocation retries from the same persisted state.
Do not delete the state, receipt, initialization marker or lock files to
recover a failure.

## Windows owner-user setup

Run these commands in PowerShell as the already-configured runner user. They
register a task only for that user, at limited privilege; do not use an
administrator prompt, install a Windows service, or configure a system-wide
task. This interactive task requires that runner user to remain logged in.
Use the same user for every run so `%LOCALAPPDATA%` resolves to the same
persistent state directory.

```powershell
$repository = (Resolve-Path "<path-to-trading-agent-public>").Path
$script = Join-Path $repository "scripts\paper_forward_self_hosted_once.ps1"
$identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$script`""
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(15) -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
$principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName "TradingAgent-PaperForward" -Action $action -Trigger $trigger -Principal $principal -Settings $settings
```

The task runs one update per invocation. `IgnoreNew` plus the application's
state/receipt locks prevents overlapping updates; a timed-out or failed update
is visible in Task Scheduler and the JSONL log, and a later schedule resumes
the existing state. Do not configure an automatic reset or a new state path
after failure. Correct the reported transient issue and allow the next run, or
stop and manually inspect/restore the matching state, receipt and initialization
marker as a set. If the gap exceeds the 100-candle fetch window, recovery
requires operator review; the runner intentionally will not skip it or bootstrap
a replacement session.

The state and feed receipt are each atomically written, but are not a joint
transaction. If a process is interrupted between those writes, the state may
be ahead of the receipt. Preserve both files and the operation log; do not
manually roll back or pair files from different sessions. A subsequent complete
update writes a fresh receipt, while any unresolved fingerprint mismatch
requires operator review.

Operational files for this task user:

- State and feed receipt: `%LOCALAPPDATA%\TradingAgent\PaperForward\state\`
- Bounded JSONL operations log, retaining the current and one rotated file:
  `%LOCALAPPDATA%\TradingAgent\PaperForward\logs\operations.jsonl`

Review a failed task using Task Scheduler's Last Run Result and the final
JSONL entry. A failed update preserves the last successful candle/fingerprint
when the state remains readable. Protect the user's profile using normal
Windows account controls; this task needs no broker secrets or elevated
permissions.

To remove the task, run `Unregister-ScheduledTask -TaskName
"TradingAgent-PaperForward" -Confirm:$false` as the same user. This does not
delete the paper state or logs.

The repository state is operational telemetry, not scientific evidence.
Forward P&L is descriptive only and cannot promote a candidate.

Safety invariants:
PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False
