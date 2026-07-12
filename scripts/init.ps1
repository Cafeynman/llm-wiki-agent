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

    $templatePath = Join-Path $PackagePath "PROJECT.md"
    if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
        throw "PROJECT template not found in package: $templatePath"
    }

    Copy-Item -LiteralPath $templatePath -Destination $projectPath -Force
}

$DefaultGitIgnoreBlock = @"
# Local wiki runtime content.
/inbox/*
!/inbox/.gitkeep
/raw/
/intake/
/reviews/
/logs/
/questions/
/artifacts/
/wiki/
"@

$PrivateRuntimeGitIgnoreLines = @(
    "/inbox/*",
    "!/inbox/.gitkeep",
    "/raw/",
    "/intake/",
    "/reviews/",
    "/logs/",
    "/questions/",
    "/artifacts/",
    "/wiki/"
)

$VersionedRuntimeGitIgnoreLines = @(
    "/inbox/*",
    "!/inbox/.gitkeep",
    "/intake/tmp/"
)

$VersionedAllIntakeLocalGitIgnoreLines = @(
    "/inbox/*",
    "!/inbox/.gitkeep",
    "/intake/"
)

$RequiredLocalGitIgnoreLines = @(
    ".env",
    "**/.env",
    ".venv/",
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    ".ruff_cache/",
    ".mypy_cache/",
    "tmp/",
    ".claude/",
    ".claudian/",
    ".codex/"
)

function Test-GitIgnoreContainsLine {
    param(
        [string]$GitIgnorePath,
        [string]$Line
    )

    if (-not (Test-Path -LiteralPath $GitIgnorePath -PathType Leaf)) {
        return $false
    }

    foreach ($existingLine in Get-Content -LiteralPath $GitIgnorePath) {
        if ($existingLine -ceq $Line) {
            return $true
        }
    }
    return $false
}

function Test-GitIgnoreContainsAllLines {
    param(
        [string]$GitIgnorePath,
        [string[]]$Lines
    )

    foreach ($line in $Lines) {
        if (-not (Test-GitIgnoreContainsLine $GitIgnorePath $line)) {
            return $false
        }
    }
    return $true
}

function Add-GitIgnoreLine {
    param(
        [string]$GitIgnorePath,
        [string]$Line
    )

    if (-not (Test-GitIgnoreContainsLine $GitIgnorePath $Line)) {
        $content = Get-Content -LiteralPath $GitIgnorePath -Raw
        if ($content.Length -gt 0 -and -not $content.EndsWith("`n")) {
            Add-Content -LiteralPath $GitIgnorePath -Value "" -Encoding UTF8
        }
        Add-Content -LiteralPath $GitIgnorePath -Value $Line -Encoding UTF8
    }
}

function Test-WikiRuntimeGitIgnorePolicy {
    param([string]$GitIgnorePath)

    if (-not (Test-Path -LiteralPath $GitIgnorePath -PathType Leaf)) {
        return $false
    }

    return (
        (Test-GitIgnoreContainsAllLines $GitIgnorePath $PrivateRuntimeGitIgnoreLines) -or
        (Test-GitIgnoreContainsAllLines $GitIgnorePath $VersionedRuntimeGitIgnoreLines) -or
        (Test-GitIgnoreContainsAllLines $GitIgnorePath $VersionedAllIntakeLocalGitIgnoreLines)
    )
}

function Ensure-GitIgnoreFile {
    param([string]$TargetPath)

    $gitIgnorePath = Join-Path $TargetPath ".gitignore"
    $templatePath = Join-Path $PackagePath ".gitignore"

    if (-not (Test-Path -LiteralPath $gitIgnorePath)) {
        if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
            throw ".gitignore template not found in package: $templatePath"
        }

        Copy-Item -LiteralPath $templatePath -Destination $gitIgnorePath -Force
        return
    }

    foreach ($line in $RequiredLocalGitIgnoreLines) {
        Add-GitIgnoreLine $gitIgnorePath $line
    }

    if (-not (Test-WikiRuntimeGitIgnorePolicy $gitIgnorePath)) {
        $content = Get-Content -LiteralPath $gitIgnorePath -Raw
        if ($content.Length -gt 0 -and -not $content.EndsWith("`n")) {
            Add-Content -LiteralPath $gitIgnorePath -Value "" -Encoding UTF8
        }
        Add-Content -LiteralPath $gitIgnorePath -Value "`n$DefaultGitIgnoreBlock" -Encoding UTF8
    }
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
    Ensure-File (Join-Path $TargetPath "inbox/.gitkeep") ""
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
Ensure-GitIgnoreFile $VaultPath
Ensure-RuntimeStructure $VaultPath

Push-Location $VaultPath
try {
    uv sync --locked --default-index https://pypi.org/simple
}
finally {
    Pop-Location
}

Write-Host "Initialized package files, uv environment, and wiki structure at: $VaultPath"
Write-Host "Default .gitignore keeps wiki runtime directories local and private. Existing files are preserved; missing local baseline rules are appended, and the default runtime block is appended only when no wiki runtime policy is present. To version durable wiki content, refer to docs/gitignore-templates.md or docs/gitignore-templates.zh-CN.md."
Write-Host "Next project-context confirmation should ask open-ended questions for theme, goal, audience, structure, classification, naming, and project-specific rules."
Write-Host "Use short choices only for bounded operational preferences such as MinerU, OCR, transcription, or frame OCR. Store only non-secret choices in PROJECT.md; fill only variables required by the selected profile in .env."
