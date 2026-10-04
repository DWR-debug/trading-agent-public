$ErrorActionPreference = "Stop"

$Repo = "DWR-debug/trading-agent-public"
$RunnerName = "LHT-N133732-3"
$RunnerRoot = Join-Path $HOME "actions-runner-3"
$LabelSet = "self-hosted,Windows,X64,trading-agent-research,trading-agent-long"

Write-Host "Trading Agent - Windows Runner C setup"
Write-Host "Repository: $Repo"
Write-Host "Runner:     $RunnerName"
Write-Host "Directory:  $RunnerRoot"
Write-Host "Labels:     $LabelSet"

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI (gh) is required."
}
gh auth status | Out-Null

if (Test-Path (Join-Path $RunnerRoot "config.cmd")) {
    throw "Existing runner registration found in $RunnerRoot. Do not overwrite it."
}

New-Item -ItemType Directory -Force -Path $RunnerRoot | Out-Null
Set-Location $RunnerRoot

$release = gh api "repos/actions/runner/releases/latest" | ConvertFrom-Json
$asset = $release.assets |
    Where-Object { $_.name -match 'actions-runner-win-x64-.*\.zip$' } |
    Select-Object -First 1

if (-not $asset) {
    throw "Could not resolve the current Windows x64 Actions Runner release."
}

$zip = Join-Path $RunnerRoot "actions-runner-win-x64.zip"
Write-Host "Downloading current runner package..."
curl.exe -L --fail --silent --show-error --retry 5 --retry-all-errors --retry-delay 2 -o $zip $asset.browser_download_url
Expand-Archive -Path $zip -DestinationPath $RunnerRoot -Force
Remove-Item $zip -Force

Write-Host "Requesting one-hour registration token..."
$tokenResponse = gh api --method POST "repos/$Repo/actions/runners/registration-token" | ConvertFrom-Json
$token = $tokenResponse.token
if (-not $token) {
    throw "Registration token could not be obtained."
}

Write-Host "Registering runner..."
.\config.cmd --unattended --url "https://github.com/$Repo" --token $token --name $RunnerName --labels $LabelSet --work "_work"
$token = $null

Write-Host "Runner C registered. Starting Runner.Listener..."
.\run.cmd
