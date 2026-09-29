[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$agy = Get-Command agy -ErrorAction SilentlyContinue
$gemini = Get-Command gemini -ErrorAction SilentlyContinue
if (-not $agy -and -not $gemini) {
    throw "No Antigravity/Gemini CLI found."
}

$geminiDir = Join-Path $env:USERPROFILE ".gemini"
$agyConfigDir = Join-Path $geminiDir "antigravity-cli"
$settings = Join-Path $agyConfigDir "settings.json"
if (-not (Test-Path -LiteralPath $settings)) {
    throw "Local AI settings missing: $settings"
}

$raw = Get-Content -LiteralPath $settings -Raw
if ($raw -notmatch '(?i)"(?:UseG1Credits|useG1Credits)"\s*:\s*false\b') {
    throw "Personal G1 credit fallback is not explicitly disabled in $settings"
}

Write-Output "LOCAL_AI_READINESS=READY"
if ($agy) {
    Write-Output ("LOCAL_AI_PROVIDER_BINARY=" + $agy.Source)
} else {
    Write-Output ("LOCAL_AI_PROVIDER_BINARY=" + $gemini.Source)
}
Write-Output "LOCAL_AI_SETTINGS_PATH=$settings"
Write-Output "PERSONAL_G1_CREDITS_DISABLED=True"
