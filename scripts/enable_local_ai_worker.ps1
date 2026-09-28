[CmdletBinding()]
param([switch]$Force)
$ErrorActionPreference = "Stop"

$root = Join-Path $HOME ".trading-agent"
$attestationPath = Join-Path $root "ai_free_attestation.json"
New-Item -ItemType Directory -Force -Path $root | Out-Null

$agy = Get-Command agy -ErrorAction SilentlyContinue
$gemini = Get-Command gemini -ErrorAction SilentlyContinue
$claude = Get-Command claude -ErrorAction SilentlyContinue

if (-not $agy -and -not $gemini) { throw "No Antigravity/Gemini CLI found in this Windows user's PATH." }
if (-not $claude) { Write-Warning "Claude CLI is not installed; Claude lane will remain skipped." }

# Local worker bootstrap: free-only, no paid or personal-credit fallback.
# Never allow Antigravity personal G1 credit fallback for project work.
$settingsPath = Join-Path $HOME ".gemini\antigravity-cli\settings.json"
New-Item -ItemType Directory -Force -Path (Split-Path $settingsPath) | Out-Null
$settingsText = if (Test-Path $settingsPath) {
    Get-Content $settingsPath -Raw
} else {
    "{}"
}

if ([string]::IsNullOrWhiteSpace($settingsText)) { $settingsText = "{}" }
if ($settingsText.TrimStart()[0] -ne "{") {
    if (-not $Force) { throw "Cannot parse $settingsPath as a JSON object. Use -Force only after verifying the file." }
    $settingsText = "{}"
}

# Constrained Language compatible JSON text mutation: no PSCustomObject/Add-Member operations.
if ($settingsText -match '(?i)"UseG1Credits"\s*:\s*(true|false)') {
    $settingsText = [regex]::Replace($settingsText, '(?i)"UseG1Credits"\s*:\s*(true|false)', '"UseG1Credits": false', 1)
} elseif ($settingsText -match '(?i)"useG1Credits"\s*:\s*(true|false)') {
    $settingsText = [regex]::Replace($settingsText, '(?i)"useG1Credits"\s*:\s*(true|false)', '"useG1Credits": false', 1)
} else {
    $trimmed = $settingsText.TrimEnd()
    if ($trimmed.EndsWith("}")) {
        $body = $trimmed.Substring(0, $trimmed.Length - 1).TrimEnd()
        if ($body -and -not $body.EndsWith(",")) { $body += "," }
        $settingsText = $body + '"UseG1Credits": false}'
    }
}

if ($settingsText -match '(?i)"tradingAgentFreeOnly"\s*:\s*(true|false)') {
    $settingsText = [regex]::Replace($settingsText, '(?i)"tradingAgentFreeOnly"\s*:\s*(true|false)', '"tradingAgentFreeOnly": true', 1)
} else {
    $trimmed = $settingsText.TrimEnd()
    if ($trimmed.EndsWith("}")) {
        $body = $trimmed.Substring(0, $trimmed.Length - 1).TrimEnd()
        if ($body -and -not $body.EndsWith(",")) { $body += "," }
        $settingsText = $body + '"tradingAgentFreeOnly": true}'
    }
}

Set-Content -Encoding UTF8 $settingsPath -Value $settingsText
$providers = @()
if ($agy -or $gemini) { $providers += "gemini_cli" }
if ($claude) { $providers += "claude_cli" }

@{
  schema_version = 1
  created_utc = [DateTime]::UtcNow.ToString("o")
  providers = $providers
  free_only = $true
  paid_fallback_allowed = $false
  personal_credit_fallback_allowed = $false
  notes = "Owner-authorized local CLI worker. Provider access remains subject to the account's included entitlement/quota."
} | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $attestationPath

Write-Output "LOCAL_AI_WORKER_ATTESTATION=$attestationPath"
Write-Output "ANTIGRAVITY_OR_GEMINI_PRESENT=$([bool]($agy -or $gemini))"
Write-Output "CLAUDE_PRESENT=$([bool]$claude)"
Write-Output "PERSONAL_G1_CREDITS_DISABLED=$true"
Write-Output "POWERSHELL_COMPATIBLE=WindowsPowerShell_5.1+"
