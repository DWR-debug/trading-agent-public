param(
    [string]$PythonExecutable = "python"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
    throw "LOCALAPPDATA is unavailable for the current task user."
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$candidatePath = Join-Path $repositoryRoot "ops\paper_forward\operational_candidate.json"
$stateRoot = Join-Path $env:LOCALAPPDATA "TradingAgent\PaperForward"
$statePath = Join-Path $stateRoot "state\shadow.json"
$receiptPath = Join-Path $stateRoot "state\feed_receipt.json"
$logPath = Join-Path $stateRoot "logs\operations.jsonl"
$sessionId = [Guid]::NewGuid().ToString("N")
$startedAtUtc = [DateTime]::UtcNow.ToString("o")
$candidateFingerprint = $null
$stateRunId = $null
$stateFingerprint = $null
$lastSuccessfulCandleUtc = $null
$operationStatus = "FAILED"
$errorState = "INITIALIZATION_FAILED"
$errorMessage = $null
$processExitCode = 1
$stateObservationError = $null

try {
    New-Item -ItemType Directory -Force -Path (Split-Path $statePath) | Out-Null
    New-Item -ItemType Directory -Force -Path (Split-Path $logPath) | Out-Null
    if (-not (Test-Path -LiteralPath $candidatePath -PathType Leaf)) {
        throw "Frozen operational candidate is missing: $candidatePath"
    }

    $candidateFingerprint = (Get-FileHash -LiteralPath $candidatePath -Algorithm SHA256).Hash.ToLowerInvariant()
    Push-Location $repositoryRoot
    try {
        $output = @(
            & $PythonExecutable -m automation.paper_forward_loop `
                --candidate $candidatePath `
                --state $statePath `
                --receipt $receiptPath `
                --fetch-limit 100 `
                --max-iterations 1 2>&1
        )
        $processExitCode = $LASTEXITCODE
        foreach ($line in $output) {
            Write-Output $line
        }
    }
    finally {
        Pop-Location
    }

    if ($processExitCode -ne 0) {
        $errorState = "UPDATE_FAILED"
        $errorMessage = ($output | ForEach-Object { "$_" }) -join "`n"
        if ([string]::IsNullOrWhiteSpace($errorMessage)) {
            $errorMessage = "Paper-forward process exited with code $processExitCode."
        }
    }
    else {
        $operationStatus = "SUCCESS"
        $errorState = "NONE"
    }
}
catch {
    $errorMessage = $_.Exception.Message
}

if (Test-Path -LiteralPath $statePath -PathType Leaf) {
    try {
        $persistedState = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
        $stateRunId = $persistedState.run_id
        $stateFingerprint = $persistedState.input_fingerprint
        $lastSuccessfulCandleUtc = $persistedState.last_market_timestamp_utc
        if (
            $operationStatus -eq "SUCCESS" -and
            (
                [string]::IsNullOrWhiteSpace($stateRunId) -or
                [string]::IsNullOrWhiteSpace($stateFingerprint) -or
                [string]::IsNullOrWhiteSpace($lastSuccessfulCandleUtc)
            )
        ) {
            $operationStatus = "FAILED"
            $errorState = "STATE_FIELDS_MISSING"
            $errorMessage = "Successful process exit did not produce a readable schema-v2 state identity."
            $processExitCode = 1
        }
    }
    catch {
        $stateObservationError = $_.Exception.Message
        if ($operationStatus -eq "SUCCESS") {
            $operationStatus = "FAILED"
            $errorState = "STATE_OBSERVATION_FAILED"
            $errorMessage = $stateObservationError
            $processExitCode = 1
        }
    }
}
elseif ($operationStatus -eq "SUCCESS") {
    $operationStatus = "FAILED"
    $errorState = "STATE_MISSING_AFTER_SUCCESS"
    $errorMessage = "Successful process exit did not leave a persistent state file."
    $processExitCode = 1
}

if (-not [string]::IsNullOrWhiteSpace($errorMessage) -and $errorMessage.Length -gt 4096) {
    $errorMessage = $errorMessage.Substring(0, 4096) + " [truncated]"
}

$record = [ordered]@{
    schema_version = 1
    session_id = $sessionId
    started_at_utc = $startedAtUtc
    completed_at_utc = [DateTime]::UtcNow.ToString("o")
    operation_status = $operationStatus
    error_state = $errorState
    error_message = $errorMessage
    python_exit_code = $processExitCode
    candidate_path = $candidatePath
    candidate_fingerprint = $candidateFingerprint
    state_path = $statePath
    state_run_id = $stateRunId
    state_fingerprint = $stateFingerprint
    last_successful_candle_utc = $lastSuccessfulCandleUtc
    state_observation_error = $stateObservationError
}
$jsonLine = $record | ConvertTo-Json -Compress -Depth 4

if (Test-Path -LiteralPath $logPath -PathType Leaf) {
    $existingLog = Get-Item -LiteralPath $logPath
    if ($existingLog.Length -ge 5MB) {
        $rotatedLogPath = "$logPath.1"
        if (Test-Path -LiteralPath $rotatedLogPath) {
            Remove-Item -LiteralPath $rotatedLogPath -Force
        }
        Move-Item -LiteralPath $logPath -Destination $rotatedLogPath
    }
}
Add-Content -LiteralPath $logPath -Value $jsonLine -Encoding UTF8

if ($operationStatus -ne "SUCCESS") {
    [Console]::Error.WriteLine("Paper-forward update failed ($errorState): $errorMessage")
    exit $processExitCode
}

Write-Output "Paper-forward update succeeded; session=$sessionId state=$stateFingerprint candle=$lastSuccessfulCandleUtc"
