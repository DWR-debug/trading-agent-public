# Windows Runner C - Long-Run Capacity

Stand: 2026-10-04

Runner C is a dedicated third Windows/X64 capacity slot for long deterministic runs and independent reproductions. It is not a third scientific decision lane and does not create performance authorization.

Expected identity:

- Runner name: LHT-N133732-3
- OS: Windows
- Architecture: X64
- Common label: trading-agent-research
- Dedicated label: trading-agent-long
- Local shell: third PowerShell window on the work PC
- Repository: DWR-debug/trading-agent-public

One-time setup:

Run this from the third PowerShell window:

powershell -ExecutionPolicy Bypass -File .\scripts\setup_third_windows_runner.ps1

The script obtains the time-limited GitHub registration token through the authenticated GitHub CLI, registers the runner, assigns the labels, clears the token variable, and starts run.cmd. GitHub documents repository-level runner setup and the time-limited registration token.

Expected first-run state:

Connected to GitHub
Listening for Jobs

Q121-R6 capacity:

Q121-R6 Independent Windows Reproduction has been expanded from two to three shards. The aggregate gate now requires shard indices 0, 1, 2, shard_count=3, contiguous partition coverage, and the unchanged frozen population fingerprint. The run remains independent-reproduction-only and non-authorizing.

Safety:

PAPER_ONLY=True
LIVE_TRADING_ENABLED=False
ORDERS_ENABLED=False
AUTOMATIC_PROMOTION=False

No registration token or secret is written to repository files.
