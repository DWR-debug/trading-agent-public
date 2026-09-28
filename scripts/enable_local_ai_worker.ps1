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
$settings = $null
if (Test-Path $settingsPath) {
    try { $settings = Get-Content $settingsPath -Raw | ConvertFrom-Json }
    catch {
        if (-not $Force) { throw "Cannot parse $settingsPath. Use -Force only after verifying the file." }
        $settings = [pscustomobject]@{}
    }
} else {
    $settings = [pscustomobject]@{}
}

$useG1 = $settings.PSObject.Properties["UseG1Credits"]
if ($null -eq $useG1) { $useG1 = $settings.PSObject.Properties["useG1Credits"] }
if ($null -ne $useG1) {
    $useG1.Value = $false
} else {
    $settings | Add-Member -NotePropertyName "UseG1Credits" -NotePropertyValue $false
}
$tradingOnly = $settings.PSObject.Properties["tradingAgentFreeOnly"]
if ($null -ne $tradingOnly) {
    $tradingOnly.Value = $true
} else {
    $settings | Add-Member -NotePropertyName "tradingAgentFreeOnly" -NotePropertyValue $true
}
$settings | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 $settingsPath

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
