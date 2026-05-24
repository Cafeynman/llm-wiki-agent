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
$script:SameRoot = $false

function Ensure-Directory {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
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
    Ensure-Directory (Split-Path -Parent $target)
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

    Ensure-Directory $targetFull
    $script:DirectoryCount += 1

    Get-ChildItem -LiteralPath $sourceFull -File -Recurse -Force | ForEach-Object {
        $relativeFile = [System.IO.Path]::GetRelativePath($sourceFull, $_.FullName)
        $targetFile = Join-Path $targetFull $relativeFile
        Ensure-Directory (Split-Path -Parent $targetFile)
        Copy-Item -LiteralPath $_.FullName -Destination $targetFile -Force
        $script:FileCount += 1
    }
}

if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
    throw "Upgrade manifest not found: $ManifestPath"
}

Ensure-Directory $TargetRoot
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
