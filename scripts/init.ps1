param(
    [string]$VaultRoot = "."
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PackagePath = (Resolve-Path -LiteralPath $ProjectRoot).Path
$ManifestPath = Join-Path $ScriptDir "upgrade-manifest.txt"

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

function Copy-FileEntry {
    param(
        [string]$RelativePath,
        [string]$TargetPath,
        [bool]$SameRoot
    )

    $source = Join-Path $PackagePath $RelativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Manifest file entry not found in package: $RelativePath"
    }

    if ($SameRoot) {
        return
    }

    $target = Join-Path $TargetPath $RelativePath
    Ensure-Directory (Split-Path -Parent $target)
    Copy-Item -LiteralPath $source -Destination $target -Force
}

function Copy-DirectoryEntry {
    param(
        [string]$RelativePath,
        [string]$TargetPath,
        [bool]$SameRoot
    )

    $source = Join-Path $PackagePath $RelativePath
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "Manifest directory entry not found in package: $RelativePath"
    }

    if ($SameRoot) {
        return
    }

    $sourceFull = (Resolve-Path -LiteralPath $source).Path
    $targetFull = [System.IO.Path]::GetFullPath((Join-Path $TargetPath $RelativePath))

    Ensure-Directory $targetFull

    Get-ChildItem -LiteralPath $sourceFull -File -Recurse -Force |
        Where-Object {
            $_.Name -notlike "*.pyc" -and
            $_.FullName -notmatch "(^|[\\/])__pycache__([\\/]|$)"
        } |
        ForEach-Object {
        $relativeFile = [System.IO.Path]::GetRelativePath($sourceFull, $_.FullName)
        $targetFile = Join-Path $targetFull $relativeFile
        Ensure-Directory (Split-Path -Parent $targetFile)
        Copy-Item -LiteralPath $_.FullName -Destination $targetFile -Force
    }
}

function Install-PackageFiles {
    param([string]$TargetPath)

    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Upgrade manifest not found: $ManifestPath"
    }

    $sameRoot = [string]::Equals($PackagePath, $TargetPath, [System.StringComparison]::OrdinalIgnoreCase)

    Get-Content -LiteralPath $ManifestPath | ForEach-Object {
        $line = $_.Trim()
        if ($line.Length -eq 0 -or $line.StartsWith("#")) {
            return
        }

        $parts = $line -split "\s+", 2
        if ($parts.Count -ne 2) {
            throw "Invalid manifest line: $line"
        }

        $kind = $parts[0]
        $relativePath = $parts[1]

        switch ($kind) {
            "file" { Copy-FileEntry $relativePath $TargetPath $sameRoot }
            "dir" { Copy-DirectoryEntry $relativePath $TargetPath $sameRoot }
            default { throw "Invalid manifest entry kind: $kind" }
        }
    }
}

function Ensure-ProjectFile {
    param([string]$TargetPath)

    $projectPath = Join-Path $TargetPath "PROJECT.md"
    if (Test-Path -LiteralPath $projectPath) {
        return
    }

    $content = @"
# Project Context

This file records the current workspace's configurable project context, including project-specific wiki structure requirements, classification preferences, naming preferences, and project-specific rules. The agent should complete it during the first project-context initialization conversation and update it when the project subject changes.

Fields are optional unless required for the current task. Leave a field blank when the project has no specific preference; blank fields mean "not specified," not "to be invented."

## Workspace Paths

- Vault root: $TargetPath
- Package root: $TargetPath

## Context

- Theme:
- Goal:
- Audience:
- Scope:
- Preferred terms:
- Wiki structure requirements:
- Classification preferences:
- Naming preferences:
- Project-specific rules:
- Constraints:
- Open questions:

## Source Extraction Preferences

- Preferences status: unconfirmed
- Default provider for document: markitdown
- Alternative provider for document: mineru
- MinerU API key status: unconfirmed
- Prefer MinerU when available: unconfirmed
- PDF preflight policy: lightweight
- Default provider for webpage: defuddle
- Image extraction policy: ask-before-ocr
- Audio extraction policy: ask-before-transcription
- Video extraction policy: ask-before-transcription-or-frame-ocr
- Unsupported source kinds:
- Provider-specific preferences: non-secret provider choices only; private endpoints and secret values belong in the project-root .env
"@

    Set-Content -LiteralPath $projectPath -Value $content -Encoding UTF8
}

function Ensure-RuntimeStructure {
    param([string]$TargetPath)

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
        Ensure-Directory (Join-Path $TargetPath $dir)
    }

    Ensure-File (Join-Path $TargetPath "logs/wiki.md") "# Wiki Log`n"
    Ensure-File (Join-Path $TargetPath "wiki/home.md") "# Home`n"
    Ensure-File (Join-Path $TargetPath "wiki/index.md") "# Index`n"
    Ensure-File (Join-Path $TargetPath "wiki/overview.md") "# Overview`n"
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

Install-PackageFiles $VaultPath
Ensure-ProjectFile $VaultPath
Ensure-RuntimeStructure $VaultPath

Push-Location $VaultPath
try {
    uv sync
}
finally {
    Pop-Location
}

Write-Host "Initialized package files, uv environment, and wiki structure at: $VaultPath"
Write-Host "Next project-context confirmation should ask whether to configure MinerU and whether to prefer MinerU when available. Store only non-secret choices in PROJECT.md; put any MinerU token in .env as MINERU_TOKEN."
