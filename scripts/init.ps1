param(
    [string]$VaultRoot = "."
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$UpgradeScript = Join-Path $ScriptDir "upgrade.ps1"

if (-not (Test-Path -LiteralPath $UpgradeScript -PathType Leaf)) {
    throw "Upgrade script not found: $UpgradeScript"
}

& $UpgradeScript -TargetRoot $VaultRoot
Write-Host "Initialized package files, uv environment, and wiki structure at: $VaultRoot"
