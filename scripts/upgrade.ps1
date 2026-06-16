param(
    [string]$TargetRoot = "."
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Split-Path -Parent $ScriptDir
$PackagePath = (Resolve-Path -LiteralPath $PackageRoot).Path
$ManifestPath = Join-Path $ScriptDir "upgrade-manifest.txt"

$script:FileCount = 0
$script:DirectoryCount = 0
$script:CreatedRuntimeCount = 0
$script:SameRoot = $false

function Ensure-Directory {
    param(
        [string]$Path,
        [bool]$Count = $true
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
        if ($Count) {
            $script:CreatedRuntimeCount += 1
        }
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
        $script:CreatedRuntimeCount += 1
    }
}

function Copy-FileEntry {
    param(
        [string]$RelativePath,
        [string]$TargetPath
    )

    $source = Join-Path $PackagePath $RelativePath
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Manifest file entry not found in package: $RelativePath"
    }

    if ($script:SameRoot) {
        return
    }

    $target = Join-Path $TargetPath $RelativePath
    $sourceFull = (Resolve-Path -LiteralPath $source).Path
    Ensure-Directory (Split-Path -Parent $target) $false
    Copy-Item -LiteralPath $sourceFull -Destination $target -Force
    $script:FileCount += 1
}

function Copy-DirectoryEntry {
    param(
        [string]$RelativePath,
        [string]$TargetPath
    )

    $source = Join-Path $PackagePath $RelativePath
    if (-not (Test-Path -LiteralPath $source -PathType Container)) {
        throw "Manifest directory entry not found in package: $RelativePath"
    }

    if ($script:SameRoot) {
        return
    }

    $target = Join-Path $TargetPath $RelativePath
    $sourceFull = (Resolve-Path -LiteralPath $source).Path
    $targetFull = [System.IO.Path]::GetFullPath($target)

    Ensure-Directory $targetFull $false
    $script:DirectoryCount += 1

    Get-ChildItem -LiteralPath $sourceFull -File -Recurse -Force |
        Where-Object {
            $_.Name -notlike "*.pyc" -and
            $_.FullName -notmatch "(^|[\\/])__pycache__([\\/]|$)"
        } |
        ForEach-Object {
        $relativeFile = [System.IO.Path]::GetRelativePath($sourceFull, $_.FullName)
        $targetFile = Join-Path $targetFull $relativeFile
        Ensure-Directory (Split-Path -Parent $targetFile) $false
        Copy-Item -LiteralPath $_.FullName -Destination $targetFile -Force
        $script:FileCount += 1
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
    $script:CreatedRuntimeCount += 1
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

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Upgrade manifest not found: $ManifestPath"
}

Ensure-Directory $TargetRoot $false
$TargetPath = (Resolve-Path -LiteralPath $TargetRoot).Path
$script:SameRoot = [string]::Equals($PackagePath, $TargetPath, [System.StringComparison]::OrdinalIgnoreCase)

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
        "file" { Copy-FileEntry $relativePath $TargetPath }
        "dir" { Copy-DirectoryEntry $relativePath $TargetPath }
        default { throw "Invalid manifest entry kind: $kind" }
    }
}

Ensure-ProjectFile $TargetPath
Ensure-RuntimeStructure $TargetPath

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv was not found. Install uv manually, then run this script again."
}

Push-Location $TargetPath
try {
    uv sync
}
finally {
    Pop-Location
}

Write-Host "Upgraded package files at: $TargetPath"
Write-Host "Merged directories: $script:DirectoryCount"
Write-Host "Copied files: $script:FileCount"
Write-Host "Created missing runtime entries: $script:CreatedRuntimeCount"
Write-Host "Next project-context confirmation should ask open-ended questions for theme, goal, audience, structure, classification, naming, and project-specific rules."
Write-Host "Use short choices only for bounded operational preferences such as MinerU, OCR, transcription, or frame OCR. Store only non-secret choices in PROJECT.md; put MinerU tokens in .env as MINERU_TOKEN only when the selected profile actually uses token auth."
