[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$agy = Get-Command agy -ErrorAction SilentlyContinue
$gemini = Get-Command gemini -ErrorAction SilentlyContinue
if (-not $agy -and -not $gemini) {
    throw "No Antigravity/Gemini CLI found."
}

$settings = Join-Path $env:USERPROFILE ".geminiantigravity-clisettings.json"
if (-not (Test-Path -LiteralPath $settings)) {
    throw "Local AI settings missing: $settings"
}

$raw = Get-Content -LiteralPath $settings -Raw
if ($raw -notmatch '(?i)"(?:UseG1Credits|useG1Credits)"s*:s*false') {
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
