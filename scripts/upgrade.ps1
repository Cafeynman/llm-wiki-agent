param(
    [string]$TargetRoot = "."
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Split-Path -Parent $ScriptDir
$PackagePath = (Resolve-Path -LiteralPath $PackageRoot).Path
$ManifestPath = Join-Path $ScriptDir "upgrade-manifest.txt"
$PathComparer = if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT) {
    [System.StringComparer]::OrdinalIgnoreCase
} else {
    [System.StringComparer]::Ordinal
}

$script:FileCount = 0
$script:ManifestDirectoryCount = 0
$script:CreatedRuntimeCount = 0
$RuntimeDirectories = @(
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
$RuntimeFiles = @(
    "logs/wiki.md",
    "inbox/.gitkeep",
    "wiki/home.md",
    "wiki/index.md",
    "wiki/overview.md"
)

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
        Ensure-Directory (Split-Path -Parent $Path)
        Set-Content -LiteralPath $Path -Value $Content -Encoding UTF8
        $script:CreatedRuntimeCount += 1
    }
}

function Test-SameFileContent {
    param(
        [string]$SourcePath,
        [string]$TargetPath
    )
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $SourcePath).Hash -ceq
        (Get-FileHash -Algorithm SHA256 -LiteralPath $TargetPath).Hash
}

function Test-ReparsePoint {
    param([System.IO.FileSystemInfo]$Item)

    return $null -ne $Item -and
        ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
}

function Assert-TargetRootPath {
    param([string]$TargetPath)

    $root = [System.IO.Path]::GetPathRoot($TargetPath)
    if (-not $root) {
        throw "Target root has no filesystem root: $TargetPath"
    }

    $relative = [System.IO.Path]::GetRelativePath($root, $TargetPath).Replace("\", "/")
    $segments = @($relative -split "/" | Where-Object { $_ -and $_ -ne "." })
    $current = $root
    foreach ($segment in $segments) {
        $current = Join-Path $current $segment
        $item = Get-Item -LiteralPath $current -Force -ErrorAction SilentlyContinue
        if ($null -eq $item) {
            break
        }
        if (Test-ReparsePoint $item) {
            throw "Target root path contains a link or reparse point: $current"
        }
        if (-not $item.PSIsContainer) {
            throw "Target root path contains a non-directory component: $current"
        }
    }
}

function Get-TargetStructureConflicts {
    param(
        [string]$TargetPath,
        [object[]]$Plan
    )

    $checks = [System.Collections.Generic.List[object]]::new()
    foreach ($record in $Plan) {
        $checks.Add([pscustomobject]@{
            RelativePath = $record.RelativePath
            ExpectedType = "file"
        }) | Out-Null
    }
    foreach ($relativePath in @("PROJECT.md", ".gitignore") + $RuntimeFiles) {
        $checks.Add([pscustomobject]@{
            RelativePath = $relativePath
            ExpectedType = "file"
        }) | Out-Null
    }
    foreach ($relativePath in $RuntimeDirectories + @(".venv")) {
        $checks.Add([pscustomobject]@{
            RelativePath = $relativePath
            ExpectedType = "directory"
        }) | Out-Null
    }

    $conflicts = [System.Collections.Generic.List[string]]::new()
    $seen = [System.Collections.Generic.HashSet[string]]::new($PathComparer)
    $reported = [System.Collections.Generic.HashSet[string]]::new($PathComparer)
    foreach ($check in $checks) {
        $relativePath = $check.RelativePath.Replace("\", "/")
        if (-not $seen.Add($relativePath)) {
            continue
        }

        try {
            $fullPath = [System.IO.Path]::GetFullPath((Join-Path $TargetPath $relativePath))
        }
        catch {
            if ($reported.Add("invalid:$relativePath")) {
                $conflicts.Add("$($relativePath): invalid target path") | Out-Null
            }
            continue
        }
        $relativeCheck = [System.IO.Path]::GetRelativePath($TargetPath, $fullPath).Replace("\", "/")
        if (
            [System.IO.Path]::IsPathRooted($relativeCheck) -or
            $relativeCheck -eq ".." -or
            $relativeCheck.StartsWith("../")
        ) {
            if ($reported.Add("escape:$relativePath")) {
                $conflicts.Add("$($relativePath): target path escapes the workspace root") | Out-Null
            }
            continue
        }

        $segments = @($relativeCheck -split "/" | Where-Object { $_ -and $_ -ne "." })
        $current = $TargetPath
        for ($index = 0; $index -lt $segments.Count; $index += 1) {
            $current = Join-Path $current $segments[$index]
            $item = Get-Item -LiteralPath $current -Force -ErrorAction SilentlyContinue
            if ($null -eq $item) {
                break
            }

            $displayPath = [System.IO.Path]::GetRelativePath($TargetPath, $current).Replace("\", "/")
            if (Test-ReparsePoint $item) {
                if ($reported.Add("reparse:$displayPath")) {
                    $conflicts.Add("$($displayPath): target path is a link or reparse point") | Out-Null
                }
                break
            }

            $isLast = $index -eq $segments.Count - 1
            if (-not $isLast -and -not $item.PSIsContainer) {
                if ($reported.Add("parent-file:$displayPath")) {
                    $conflicts.Add("$($displayPath): parent path is not a directory") | Out-Null
                }
                break
            }
            if ($isLast -and $check.ExpectedType -eq "file" -and $item.PSIsContainer) {
                if ($reported.Add("expected-file:$displayPath")) {
                    $conflicts.Add("$($displayPath): expected a file but found a directory") | Out-Null
                }
                break
            }
            if ($isLast -and $check.ExpectedType -eq "directory" -and -not $item.PSIsContainer) {
                if ($reported.Add("expected-directory:$displayPath")) {
                    $conflicts.Add("$($displayPath): expected a directory but found a file") | Out-Null
                }
                break
            }
        }
    }
    return @($conflicts)
}

function Add-PackagePlanRecord {
    param(
        [System.Collections.Generic.List[object]]$Records,
        [System.Collections.Generic.HashSet[string]]$Seen,
        [string]$RelativePath,
        [string]$SourcePath,
        [string]$TargetPath,
        [bool]$SameRoot
    )

    $relative = $RelativePath.Replace("\", "/")
    if (-not $Seen.Add($relative)) {
        throw "Duplicate package-managed path in manifest expansion: $relative"
    }

    $action = "CREATE"
    $reason = $null
    if ($SameRoot) {
        $action = "UNCHANGED"
    } elseif (Test-Path -LiteralPath $TargetPath -PathType Container) {
        $action = "CONFLICT"
        $reason = "target path is a directory"
    } elseif (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
        if (Test-SameFileContent $SourcePath $TargetPath) {
            $action = "UNCHANGED"
        } else {
            $action = "REPLACE"
        }
    }

    $Records.Add([pscustomobject]@{
        RelativePath = $relative
        SourcePath = $SourcePath
        TargetPath = $TargetPath
        Action = $action
        Reason = $reason
    }) | Out-Null
}

function Get-PackagePlan {
    param(
        [string]$TargetPath,
        [bool]$SameRoot
    )

    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) {
        throw "Upgrade manifest not found: $ManifestPath"
    }

    $records = [System.Collections.Generic.List[object]]::new()
    $seen = [System.Collections.Generic.HashSet[string]]::new($PathComparer)

    foreach ($manifestLine in Get-Content -LiteralPath $ManifestPath) {
        $line = $manifestLine.Trim()
        if ($line.Length -eq 0 -or $line.StartsWith("#")) {
            continue
        }

        $parts = $line -split "\s+", 2
        if ($parts.Count -ne 2) {
            throw "Invalid manifest line: $line"
        }

        $kind = $parts[0]
        $relativePath = $parts[1].Replace("\", "/")
        $source = Join-Path $PackagePath $relativePath

        if ($kind -eq "file") {
            if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
                throw "Manifest file entry not found in package: $relativePath"
            }
            Add-PackagePlanRecord $records $seen $relativePath $source (Join-Path $TargetPath $relativePath) $SameRoot
            continue
        }

        if ($kind -eq "dir") {
            if (-not (Test-Path -LiteralPath $source -PathType Container)) {
                throw "Manifest directory entry not found in package: $relativePath"
            }
            $script:ManifestDirectoryCount += 1
            $sourceFull = (Resolve-Path -LiteralPath $source).Path
            foreach ($sourceFile in Get-ChildItem -LiteralPath $sourceFull -File -Recurse -Force |
                Where-Object {
                    $_.Name -notlike "*.pyc" -and
                    $_.FullName -notmatch "(^|[\\/])__pycache__([\\/]|$)"
                }) {
                $child = [System.IO.Path]::GetRelativePath($sourceFull, $sourceFile.FullName).Replace("\", "/")
                $expanded = "$relativePath/$child"
                Add-PackagePlanRecord $records $seen $expanded $sourceFile.FullName (Join-Path $TargetPath $expanded) $SameRoot
            }
            continue
        }

        throw "Invalid manifest entry kind: $kind"
    }

    return @($records | Sort-Object RelativePath)
}

function Get-GitBaseline {
    param([string]$TargetPath)

    if (-not (Test-Path -LiteralPath $TargetPath -PathType Container)) {
        return $null
    }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return $null
    }

    $inside = & git -C $TargetPath rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -ne 0 -or $inside -notcontains "true") {
        return $null
    }
    & git -C $TargetPath rev-parse --verify HEAD 1>$null 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }

    $gitRootOutput = @(& git -C $TargetPath rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -ne 0 -or $gitRootOutput.Count -eq 0) {
        return $null
    }
    $gitRoot = (Resolve-Path -LiteralPath $gitRootOutput[0]).Path
    $tracked = [System.Collections.Generic.HashSet[string]]::new($PathComparer)
    $dirty = [System.Collections.Generic.HashSet[string]]::new($PathComparer)

    foreach ($path in @(& git -c core.quotepath=false -C $gitRoot ls-files 2>$null)) {
        if ($path) {
            $tracked.Add($path.Replace("\", "/")) | Out-Null
        }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read tracked paths from Git baseline: $gitRoot"
    }

    foreach ($path in @(& git -c core.quotepath=false -C $gitRoot diff --name-only HEAD -- 2>$null)) {
        if ($path) {
            $dirty.Add($path.Replace("\", "/")) | Out-Null
        }
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to compare Git baseline: $gitRoot"
    }

    return [pscustomobject]@{
        Root = $gitRoot
        Tracked = $tracked
        Dirty = $dirty
    }
}

function Get-PlanConflicts {
    param(
        [object[]]$Plan,
        $GitBaseline
    )

    $conflicts = [System.Collections.Generic.List[string]]::new()
    foreach ($record in $Plan) {
        if ($record.Action -eq "UNCHANGED") {
            continue
        }
        if ($record.Action -eq "CONFLICT") {
            $conflicts.Add("$($record.RelativePath): $($record.Reason)") | Out-Null
            continue
        }

        if ($null -eq $GitBaseline) {
            if ($record.Action -eq "REPLACE") {
                $conflicts.Add("$($record.RelativePath): existing file differs and no Git baseline is available") | Out-Null
            }
            continue
        }

        $gitRelative = [System.IO.Path]::GetRelativePath($GitBaseline.Root, $record.TargetPath).Replace("\", "/")
        if ($gitRelative -eq ".." -or $gitRelative.StartsWith("../")) {
            $conflicts.Add("$($record.RelativePath): target path is outside the Git baseline") | Out-Null
            continue
        }

        if ($record.Action -eq "CREATE") {
            if ($GitBaseline.Tracked.Contains($gitRelative) -and $GitBaseline.Dirty.Contains($gitRelative)) {
                $conflicts.Add("$($record.RelativePath): tracked package file is deleted in the working tree") | Out-Null
            }
            continue
        }

        if (-not $GitBaseline.Tracked.Contains($gitRelative)) {
            $conflicts.Add("$($record.RelativePath): existing file differs and is not tracked by the Git baseline") | Out-Null
        } elseif ($GitBaseline.Dirty.Contains($gitRelative)) {
            $conflicts.Add("$($record.RelativePath): tracked package file has uncommitted changes") | Out-Null
        }
    }
    return @($conflicts)
}

function Copy-PackageFiles {
    param([object[]]$Plan)

    foreach ($record in $Plan) {
        if ($record.Action -notin @("CREATE", "REPLACE")) {
            continue
        }
        Ensure-Directory (Split-Path -Parent $record.TargetPath) $false
        Copy-Item -LiteralPath $record.SourcePath -Destination $record.TargetPath -Force
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
    Copy-Item -LiteralPath $templatePath -Destination $projectPath
    $script:CreatedRuntimeCount += 1
}

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

function Add-GitIgnoreLine {
    param(
        [string]$GitIgnorePath,
        [string]$Line
    )
    if (Test-GitIgnoreContainsLine $GitIgnorePath $Line) {
        return
    }
    $content = Get-Content -LiteralPath $GitIgnorePath -Raw
    if ($content.Length -gt 0 -and -not $content.EndsWith("`n")) {
        Add-Content -LiteralPath $GitIgnorePath -Value "" -Encoding UTF8
    }
    Add-Content -LiteralPath $GitIgnorePath -Value $Line -Encoding UTF8
}

function Test-TrackedWikiRuntime {
    param([string]$TargetPath)

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        return $false
    }
    $insideWorkTree = & git -C $TargetPath rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -ne 0 -or $insideWorkTree -notcontains "true") {
        return $false
    }
    $trackedPaths = @(& git -C $TargetPath ls-files -- wiki reviews logs questions artifacts intake/processed intake/logs raw inbox 2>$null)
    if ($LASTEXITCODE -ne 0) {
        return $false
    }
    foreach ($trackedPath in $trackedPaths) {
        if ($trackedPath.Replace("\", "/") -notmatch "(^|/)inbox/\.gitkeep$") {
            return $true
        }
    }
    return $false
}

function Ensure-GitIgnoreFile {
    param([string]$TargetPath)

    $gitIgnorePath = Join-Path $TargetPath ".gitignore"
    $templatePath = Join-Path $PackagePath ".gitignore"
    if (-not (Test-Path -LiteralPath $gitIgnorePath)) {
        if (Test-TrackedWikiRuntime $TargetPath) {
            New-Item -ItemType File -Path $gitIgnorePath -Force | Out-Null
            foreach ($line in $RequiredLocalGitIgnoreLines) {
                Add-GitIgnoreLine $gitIgnorePath $line
            }
            $script:CreatedRuntimeCount += 1
            Write-Host "Created baseline-only .gitignore because durable wiki runtime files are already tracked."
            return
        }
        if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
            throw ".gitignore template not found in package: $templatePath"
        }
        Copy-Item -LiteralPath $templatePath -Destination $gitIgnorePath
        $script:CreatedRuntimeCount += 1
        Write-Host "Created the default private wiki runtime .gitignore policy."
        return
    }
    foreach ($line in $RequiredLocalGitIgnoreLines) {
        Add-GitIgnoreLine $gitIgnorePath $line
    }
    Write-Host "Preserved the target-owned .gitignore domain policy; added only secret and technical-cache rules."
}

function Ensure-RuntimeStructure {
    param([string]$TargetPath)

    foreach ($dir in $RuntimeDirectories) {
        Ensure-Directory (Join-Path $TargetPath $dir)
    }
    Ensure-File (Join-Path $TargetPath "logs/wiki.md") "# Wiki Log`n"
    Ensure-File (Join-Path $TargetPath "inbox/.gitkeep") ""
    Ensure-File (Join-Path $TargetPath "wiki/home.md") "# Home`n"
    Ensure-File (Join-Path $TargetPath "wiki/index.md") "# Index`n"
    Ensure-File (Join-Path $TargetPath "wiki/overview.md") "# Overview`n"
}

$TargetPath = [System.IO.Path]::GetFullPath($TargetRoot)
Assert-TargetRootPath $TargetPath
foreach ($templateName in @("PROJECT.md", ".gitignore")) {
    $templatePath = Join-Path $PackagePath $templateName
    if (-not (Test-Path -LiteralPath $templatePath -PathType Leaf)) {
        throw "Package template not found: $templatePath"
    }
}
$sameRoot = [string]::Equals($PackagePath, $TargetPath, [System.StringComparison]::OrdinalIgnoreCase)
$plan = Get-PackagePlan $TargetPath $sameRoot
$gitBaseline = if ($sameRoot) { $null } else { Get-GitBaseline $TargetPath }
$conflicts = @(
    Get-PlanConflicts $plan $gitBaseline
    Get-TargetStructureConflicts $TargetPath $plan
)

$createCount = @($plan | Where-Object Action -eq "CREATE").Count
$replaceCount = @($plan | Where-Object Action -eq "REPLACE").Count
$unchangedCount = @($plan | Where-Object Action -eq "UNCHANGED").Count
Write-Host "Package file plan: create $createCount, replace $replaceCount, unchanged $unchangedCount."

if ($conflicts.Count -gt 0) {
    foreach ($conflict in $conflicts) {
        [Console]::Error.WriteLine("Conflict: $conflict")
    }
    throw "Package update stopped before writing because target paths require attention."
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv was not found. Install uv manually, then run this script again."
}

Ensure-Directory $TargetPath $false
Copy-PackageFiles $plan
Ensure-ProjectFile $TargetPath
Ensure-GitIgnoreFile $TargetPath
Ensure-RuntimeStructure $TargetPath

Push-Location $TargetPath
try {
    uv sync --locked --default-index https://pypi.org/simple
}
finally {
    Pop-Location
}

Write-Host "Upgraded package files at: $TargetPath"
Write-Host "Merged manifest directories: $script:ManifestDirectoryCount"
Write-Host "Copied package files: $script:FileCount"
Write-Host "Created missing runtime entries: $script:CreatedRuntimeCount"
Write-Host "Existing .gitignore domain rules are preserved; only secret and technical-cache baseline rules are added."
