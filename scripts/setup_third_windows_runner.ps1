$ErrorActionPreference = "Stop"

$Repo = "DWR-debug/trading-agent-public"
$RunnerName = "LHT-N133732-3"
$RunnerRoot = Join-Path $HOME "actions-runner-3"
$LabelSet = "trading-agent-research,trading-agent-long"

Write-Host "Trading Agent - Windows Runner C setup"
Write-Host "Repository: $Repo"
Write-Host "Runner:     $RunnerName"
Write-Host "Directory:  $RunnerRoot"
Write-Host "Labels:     $LabelSet"

if (Test-Path (Join-Path $RunnerRoot "config.cmd")) {
    throw "Existing runner registration found in $RunnerRoot. Do not overwrite it."
}

New-Item -ItemType Directory -Force -Path $RunnerRoot | Out-Null
Set-Location $RunnerRoot

Write-Host "Resolving current Windows x64 Actions Runner package..."
$release = Invoke-RestMethod -Method Get -Uri "https://api.github.com/repos/actions/runner/releases/latest" -Headers @{
    Accept = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2026-03-10"
}
$asset = $release.assets |
    Where-Object { $_.name -match '^actions-runner-win-x64-.*\.zip$' } |
    Select-Object -First 1

if (-not $asset) {
    throw "Could not resolve the current Windows x64 Actions Runner release."
}

$zip = Join-Path $RunnerRoot $asset.name
Write-Host "Downloading $($asset.name)..."
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zip -UseBasicParsing
Expand-Archive -Path $zip -DestinationPath $RunnerRoot -Force
Remove-Item $zip -Force

Write-Host ""
Write-Host "GitHub requires a short-lived repository runner registration token."
Write-Host "Generate one at:"
Write-Host "Repository -> Settings -> Actions -> Runners -> New self-hosted runner"
Write-Host "The token expires after one hour."
$token = Read-Host "Paste the one-time runner registration token"
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "No runner registration token supplied."
}

Write-Host "Registering runner..."
.\config.cmd --unattended --url "https://github.com/$Repo" --token $token.Trim() --name $RunnerName --labels $LabelSet --work "_work"
$token = $null

Write-Host ""
Write-Host "Runner C registered. Starting Runner.Listener..."
.\run.cmd
