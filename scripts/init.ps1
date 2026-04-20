param(
    [string]$VaultRoot = "."
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Ensure-File {
    param(
        [string]$Path,
        [string]$Content
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        $parent = Split-Path -Parent $Path
        Ensure-Directory $parent
        Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
    }
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv was not found. Installing uv with the official installer..."
    try {
        Invoke-Expression (Invoke-RestMethod https://astral.sh/uv/install.ps1)
    }
    catch {
        throw "uv installation failed. Install uv manually, then run this script again. Original error: $($_.Exception.Message)"
    }
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv installation did not make uv available in this shell. Install uv manually or restart the terminal, then run this script again."
}

Ensure-Directory $VaultRoot
$VaultPath = (Resolve-Path -LiteralPath $VaultRoot).Path

$directories = @(
    "inbox",
    "raw/digested",
    "raw/needs-review",
    "raw/ignored",
    "raw/unsupported",
    "intake/tmp",
    "intake/processed",
    "intake/logs",
    "reviews/source-review",
    "reviews/reflection",
    "logs",
    "questions",
    "artifacts",
    "wiki/sources",
    "wiki/entities",
    "wiki/concepts",
    "wiki/claims",
    "wiki/syntheses"
)

foreach ($dir in $directories) {
    Ensure-Directory (Join-Path $VaultPath $dir)
}

Ensure-File (Join-Path $VaultPath "logs/wiki.md") "# Wiki Log`n"
Ensure-File (Join-Path $VaultPath "wiki/home.md") "# Home`n"
Ensure-File (Join-Path $VaultPath "wiki/index.md") "# Index`n"
Ensure-File (Join-Path $VaultPath "wiki/overview.md") "# Overview`n"

Push-Location $ProjectRoot
try {
    uv sync
}
finally {
    Pop-Location
}

Write-Host "Initialized uv environment and wiki structure at: $VaultPath"
