$ErrorActionPreference = "Stop"
$runnerRoot = Join-Path $HOME "actions-runner"
Write-Output "RUNNER_ROOT=$runnerRoot"

$processes = Get-Process | Where-Object {
    $_.ProcessName -match "Runner|Runner.Listener|Runner.Worker"
}
if ($processes) {
    Write-Output "RUNNER_PROCESSES=RUNNING"
    $processes | Select-Object ProcessName, Id, StartTime | Format-Table -AutoSize
} else { Write-Output "RUNNER_PROCESSES=NONE" }

$services = Get-Service | Where-Object {
    $_.Name -match "^actions\.runner" -or
    $_.DisplayName -match "GitHub Actions Runner"
}
if ($services) {
    Write-Output "RUNNER_SERVICES=FOUND"
    $services | Select-Object Status, Name, DisplayName | Format-Table -AutoSize
} else { Write-Output "RUNNER_SERVICES=NONE" }

$diag = Join-Path $runnerRoot "_diag"
if (Test-Path $diag) {
    Write-Output "RUNNER_DIAG=FOUND"
    Get-ChildItem -Path $diag -Filter "*.log" -Force |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 5 Name, LastWriteTime, Length |
        Format-Table -AutoSize
} else { Write-Output "RUNNER_DIAG=NONE" }

$runCmd = Join-Path $runnerRoot "run.cmd"
if (Test-Path $runCmd) { Write-Output "RUNNER_COMMAND=AVAILABLE" }
else { Write-Output "RUNNER_COMMAND=MISSING" }

if ($processes) {
    Write-Output "RUNNER_STATUS=RUNNING"
} elseif ($services -and ($services | Where-Object Status -eq "Running")) {
    Write-Output "RUNNER_STATUS=RUNNING_AS_SERVICE"
} elseif (Test-Path $runCmd) {
    Write-Output "RUNNER_STATUS=INSTALLED_BUT_NOT_RUNNING"
} else {
    Write-Output "RUNNER_STATUS=NOT_CONFIGURED"
}
