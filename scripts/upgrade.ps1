param(
    [string]$TargetRoot = "."
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Split-Path -Parent $ScriptDir
$PackagePath = (Resolve-Path -LiteralPath $PackageRoot).Path
$InventoryPath = Join-Path $ScriptDir "package-files.txt"
$PathComparer = [System.StringComparer]::OrdinalIgnoreCase
$Utf8NoBomStrict = New-Object System.Text.UTF8Encoding($false, $true)
$InventorySchemaMarker = "# inventory-schema: 1"
$RootPathComparison = if ([System.Environment]::OSVersion.Platform -eq [System.PlatformID]::Win32NT) {
    [System.StringComparison]::OrdinalIgnoreCase
} else {
    [System.StringComparison]::Ordinal
}

$script:FileCount = 0
$script:RemovedFileCount = 0
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
        [System.IO.File]::WriteAllText($Path, $Content, $Utf8NoBomStrict)
        $script:CreatedRuntimeCount += 1
    }
}

function Test-SameFileContent {
    param(
        [string]$SourcePath,
        [string]$TargetPath
    )
    $sourceAlgorithm = [System.Security.Cryptography.SHA256]::Create()
    $targetAlgorithm = [System.Security.Cryptography.SHA256]::Create()
    $sourceStream = $null
    $targetStream = $null
    try {
        $sourceStream = [System.IO.File]::OpenRead($SourcePath)
        $targetStream = [System.IO.File]::OpenRead($TargetPath)
        $sourceHash = [System.BitConverter]::ToString($sourceAlgorithm.ComputeHash($sourceStream))
        $targetHash = [System.BitConverter]::ToString($targetAlgorithm.ComputeHash($targetStream))
        return $sourceHash -ceq $targetHash
    }
    finally {
        if ($null -ne $sourceStream) {
            $sourceStream.Dispose()
        }
        if ($null -ne $targetStream) {
            $targetStream.Dispose()
        }
        $sourceAlgorithm.Dispose()
        $targetAlgorithm.Dispose()
    }
}

function Test-ReparsePoint {
    param([System.IO.FileSystemInfo]$Item)

    return $null -ne $Item -and
        ($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
}

function Get-RelativePathCompat {
    param(
        [string]$BasePath,
        [string]$Path
    )

    $baseFullPath = [System.IO.Path]::GetFullPath($BasePath)
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if ([string]::Equals($baseFullPath, $fullPath, $RootPathComparison)) {
        return "."
    }

    $basePrefix = $baseFullPath.TrimEnd(
        [System.IO.Path]::DirectorySeparatorChar,
        [System.IO.Path]::AltDirectorySeparatorChar
    ) + [System.IO.Path]::DirectorySeparatorChar
    if ($fullPath.StartsWith($basePrefix, $RootPathComparison)) {
        return $fullPath.Substring($basePrefix.Length)
    }
    return $fullPath
}

function Get-PathItemNoFollow {
    param([string]$Path)

    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if ($null -ne $item) {
        return $item
    }

    $parent = Split-Path -Parent $Path
    $leaf = Split-Path -Leaf $Path
    if (-not $parent -or -not (Test-Path -LiteralPath $parent -PathType Container)) {
        return $null
    }
    return @(
        Get-ChildItem -LiteralPath $parent -Force -ErrorAction SilentlyContinue |
            Where-Object { [string]::Equals($_.Name, $leaf, $RootPathComparison) }
    ) | Select-Object -First 1
}

function Assert-PackageSourcePathSafe {
    param(
        [string]$RootPath,
        [string]$RelativePath,
        [ValidateSet("file", "directory")]
        [string]$ExpectedType,
        [string]$Context
    )

    $current = $RootPath
    $segments = $RelativePath.Split("/")
    for ($index = 0; $index -lt $segments.Count; $index += 1) {
        $current = Join-Path $current $segments[$index]
        $item = Get-PathItemNoFollow $current
        if ($null -eq $item) {
            throw "$Context not found: $RelativePath"
        }
        if (Test-ReparsePoint $item) {
            throw "$Context contains a link or reparse point: $RelativePath"
        }
        $isLast = $index -eq $segments.Count - 1
        if (-not $isLast -and -not $item.PSIsContainer) {
            throw "$Context contains a non-directory ancestor: $RelativePath"
        }
        if ($isLast -and $ExpectedType -eq "file" -and $item.PSIsContainer) {
            throw "$Context is not a regular file: $RelativePath"
        }
        if ($isLast -and $ExpectedType -eq "directory" -and -not $item.PSIsContainer) {
            throw "$Context is not a directory: $RelativePath"
        }
    }
}

function Assert-TargetRootPath {
    param([string]$TargetPath)

    $root = [System.IO.Path]::GetPathRoot($TargetPath)
    if (-not $root) {
        throw "Target root has no filesystem root: $TargetPath"
    }

    $relative = (Get-RelativePathCompat $root $TargetPath).Replace("\", "/")
    $segments = @($relative -split "/" | Where-Object { $_ -and $_ -ne "." })
    $current = $root
    foreach ($segment in $segments) {
        $current = Join-Path $current $segment
        $item = Get-PathItemNoFollow $current
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
        $relativeCheck = (Get-RelativePathCompat $TargetPath $fullPath).Replace("\", "/")
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
            $item = Get-PathItemNoFollow $current
            if ($null -eq $item) {
                break
            }

            $displayPath = (Get-RelativePathCompat $TargetPath $current).Replace("\", "/")
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

function ConvertTo-PackageRelativePath {
    param(
        [string]$RawPath,
        [string]$Context
    )

    $relative = $RawPath.TrimStart([char]0xFEFF).Trim().Replace("\", "/")
    if (
        -not $relative -or
        $relative.StartsWith("/") -or
        $relative.EndsWith("/") -or
        $relative.Contains("//") -or
        $relative.Contains(":") -or
        [System.IO.Path]::IsPathRooted($relative)
    ) {
        throw "$Context contains an invalid package path: $RawPath"
    }
    foreach ($segment in $relative.Split("/")) {
        if (-not $segment -or $segment -in @(".", "..")) {
            throw "$Context contains an invalid package path: $RawPath"
        }
    }
    return $relative
}

function Get-SafeTargetFileState {
    param(
        [string]$TargetPath,
        [string]$RelativePath
    )

    $current = $TargetPath
    $segments = $RelativePath.Split("/")
    for ($index = 0; $index -lt $segments.Count; $index += 1) {
        $current = Join-Path $current $segments[$index]
        $item = Get-PathItemNoFollow $current
        if ($null -eq $item) {
            return [pscustomobject]@{ State = "MISSING"; Reason = $null }
        }
        $displayPath = (Get-RelativePathCompat $TargetPath $current).Replace("\", "/")
        if (Test-ReparsePoint $item) {
            return [pscustomobject]@{
                State = "CONFLICT"
                Reason = "$displayPath is a link or reparse point"
            }
        }
        $isLast = $index -eq $segments.Count - 1
        if (-not $isLast -and -not $item.PSIsContainer) {
            return [pscustomobject]@{
                State = "CONFLICT"
                Reason = "$displayPath is not a directory"
            }
        }
        if ($isLast) {
            if ($item.PSIsContainer) {
                return [pscustomobject]@{ State = "CONFLICT"; Reason = "target path is a directory" }
            }
            return [pscustomobject]@{ State = "FILE"; Reason = $null }
        }
    }
    return [pscustomobject]@{ State = "MISSING"; Reason = $null }
}

function Assert-OwnershipMetadataPathSafe {
    param(
        [string]$TargetPath,
        [string]$RelativePath
    )

    $current = $TargetPath
    $segments = $RelativePath.Split("/")
    for ($index = 0; $index -lt $segments.Count; $index += 1) {
        $current = Join-Path $current $segments[$index]
        $item = Get-PathItemNoFollow $current
        if ($null -eq $item) {
            return
        }
        if (Test-ReparsePoint $item) {
            throw "Old package ownership metadata path is a link or reparse point: $RelativePath"
        }
        $isLast = $index -eq $segments.Count - 1
        if (-not $isLast -and -not $item.PSIsContainer) {
            throw "Old package ownership metadata parent is not a directory: $RelativePath"
        }
        if ($isLast -and $item.PSIsContainer) {
            throw "Old package ownership metadata path is not a regular file: $RelativePath"
        }
    }
}

function Read-PackageInventory {
    param(
        [string]$RootPath,
        [string]$InventoryFile,
        [bool]$RequireSourceFiles,
        [string]$Label
    )

    $active = [System.Collections.Generic.Dictionary[string, string]]::new($PathComparer)
    $removed = [System.Collections.Generic.HashSet[string]]::new($PathComparer)
    $seen = [System.Collections.Generic.HashSet[string]]::new($PathComparer)
    $schemaMarkerSeen = $false

    foreach ($inventoryLine in [System.IO.File]::ReadAllLines($InventoryFile, $Utf8NoBomStrict)) {
        $line = $inventoryLine.TrimStart([char]0xFEFF).Trim()
        if ($line -ceq $InventorySchemaMarker) {
            if ($schemaMarkerSeen) {
                throw "$Label inventory contains a duplicate schema marker."
            }
            $schemaMarkerSeen = $true
            continue
        }
        if ($line.StartsWith("# inventory-schema:")) {
            throw "$Label inventory uses an unsupported schema marker: $line"
        }
        if (-not $line -or $line.StartsWith("#")) {
            continue
        }

        $parts = $line -split "\s+", 2
        if ($parts.Count -ne 2 -or $parts[0] -cnotin @("active", "remove")) {
            throw "Invalid $Label inventory line: $line"
        }
        $kind = $parts[0]
        $relativePath = ConvertTo-PackageRelativePath $parts[1] "$Label inventory"
        if (-not $seen.Add($relativePath)) {
            throw "$Label inventory contains a duplicate package path: $relativePath"
        }

        if ($kind -ceq "active") {
            $sourcePath = Join-Path $RootPath $relativePath
            if ($RequireSourceFiles) {
                Assert-PackageSourcePathSafe $RootPath $relativePath "file" "$Label active inventory entry"
            }
            $active.Add($relativePath, $sourcePath)
        } else {
            if ($relativePath -ceq "scripts/package-files.txt") {
                throw "$Label inventory cannot retire itself: $relativePath"
            }
            $removed.Add($relativePath) | Out-Null
        }
    }

    if (-not $schemaMarkerSeen) {
        throw "$Label inventory must declare '$InventorySchemaMarker'."
    }
    if (-not $active.ContainsKey("scripts/package-files.txt")) {
        throw "$Label inventory must own scripts/package-files.txt as an active path."
    }

    return [pscustomobject]@{
        Available = $true
        ActivePaths = $active
        RemovedPaths = $removed
    }
}

function Get-OldPackageOwnership {
    param([string]$TargetPath)

    $oldInventory = Join-Path $TargetPath "scripts/package-files.txt"
    Assert-OwnershipMetadataPathSafe $TargetPath "scripts/package-files.txt"
    if (-not (Test-Path -LiteralPath $oldInventory -PathType Leaf)) {
        return [pscustomobject]@{
            Available = $false
            ActivePaths = [System.Collections.Generic.Dictionary[string, string]]::new($PathComparer)
            RemovedPaths = [System.Collections.Generic.HashSet[string]]::new($PathComparer)
        }
    }
    return Read-PackageInventory $TargetPath $oldInventory $false "Old package"
}

function Add-PlanRecord {
    param(
        [System.Collections.Generic.List[object]]$Records,
        [System.Collections.Generic.HashSet[string]]$Seen,
        [string]$RelativePath,
        [string]$SourcePath,
        [string]$TargetPath,
        [string]$Action,
        [string]$Reason
    )

    if (-not $Seen.Add($RelativePath)) {
        throw "Duplicate package path while building the ownership plan: $RelativePath"
    }
    $metadataOrder = if ($RelativePath -ceq "scripts/package-files.txt") { 1 } else { 0 }
    $Records.Add([pscustomobject]@{
        RelativePath = $RelativePath
        SourcePath = $SourcePath
        TargetPath = $TargetPath
        Action = $Action
        Reason = $Reason
        MetadataOrder = $metadataOrder
    }) | Out-Null
}

function Get-PackagePlan {
    param(
        [string]$TargetPath,
        [bool]$SameRoot,
        $NewMetadata,
        $OldMetadata
    )

    $records = [System.Collections.Generic.List[object]]::new()
    $seen = [System.Collections.Generic.HashSet[string]]::new($PathComparer)

    foreach ($relativePath in @($NewMetadata.ActivePaths.Keys | Sort-Object)) {
        $source = $NewMetadata.ActivePaths[$relativePath]
        $target = Join-Path $TargetPath $relativePath
        $oldOwns = $OldMetadata.Available -and $OldMetadata.ActivePaths.ContainsKey($relativePath)
        $action = "CREATE"
        $reason = $null
        $targetState = Get-SafeTargetFileState $TargetPath $relativePath
        if ($SameRoot) {
            $action = "UNCHANGED"
        } elseif ($targetState.State -eq "CONFLICT") {
            $action = "CONFLICT"
            $reason = $targetState.Reason
        } elseif ($targetState.State -eq "FILE") {
            if (Test-SameFileContent $source $target) {
                $action = "UNCHANGED"
            } elseif ($oldOwns) {
                $action = "REPLACE"
            } else {
                $action = "CONFLICT"
                $reason = "new package-owned path already exists with different content"
            }
        }
        Add-PlanRecord $records $seen $relativePath $source $target $action $reason
    }

    if ($OldMetadata.Available) {
        foreach ($relativePath in @($OldMetadata.ActivePaths.Keys | Sort-Object)) {
            if ($NewMetadata.ActivePaths.ContainsKey($relativePath)) {
                continue
            }
            $target = Join-Path $TargetPath $relativePath
            $targetState = Get-SafeTargetFileState $TargetPath $relativePath
            if (-not $NewMetadata.RemovedPaths.Contains($relativePath)) {
                Add-PlanRecord $records $seen $relativePath $null $target "CONFLICT" "old package-owned path is absent from the new inventory without an explicit remove entry"
                continue
            }
            $action = "UNCHANGED"
            $reason = $null
            if (-not $SameRoot) {
                if ($targetState.State -eq "CONFLICT") {
                    $action = "CONFLICT"
                    $reason = $targetState.Reason
                } elseif ($targetState.State -eq "FILE") {
                    $action = "REMOVE"
                }
            }
            Add-PlanRecord $records $seen $relativePath $null $target $action $reason
        }

        foreach ($relativePath in @($OldMetadata.RemovedPaths | Sort-Object)) {
            if (
                $NewMetadata.ActivePaths.ContainsKey($relativePath) -or
                $NewMetadata.RemovedPaths.Contains($relativePath)
            ) {
                continue
            }
            $target = Join-Path $TargetPath $relativePath
            Add-PlanRecord $records $seen $relativePath $null $target "CONFLICT" "old retired package path is absent from the new inventory; retain its remove entry or explicitly reactivate it"
        }
    }

    foreach ($relativePath in @($NewMetadata.RemovedPaths | Sort-Object)) {
        if ($seen.Contains($relativePath)) {
            continue
        }
        $target = Join-Path $TargetPath $relativePath
        $targetState = Get-SafeTargetFileState $TargetPath $relativePath
        $action = "UNCHANGED"
        $reason = $null
        if (-not $SameRoot) {
            if ($targetState.State -eq "CONFLICT") {
                $action = "CONFLICT"
                $reason = $targetState.Reason
            } elseif ($targetState.State -eq "FILE") {
                if ($OldMetadata.Available -and $OldMetadata.RemovedPaths.Contains($relativePath)) {
                    $action = "REMOVE"
                } else {
                    $action = "CONFLICT"
                    $reason = "retired package path exists without prior active or retired package ownership"
                }
            }
        }
        Add-PlanRecord $records $seen $relativePath $null $target $action $reason
    }

    return @($records | Sort-Object RelativePath)
}

function Get-PlanConflicts {
    param([object[]]$Plan)

    return @(
        $Plan |
            Where-Object Action -eq "CONFLICT" |
            ForEach-Object { "$($_.RelativePath): $($_.Reason)" }
    )
}

function Apply-PackagePlanContent {
    param([object[]]$Plan)

    foreach ($record in @($Plan | Where-Object MetadataOrder -eq 0)) {
        if ($record.Action -eq "REMOVE") {
            Remove-Item -LiteralPath $record.TargetPath -Force
            $script:RemovedFileCount += 1
            continue
        }
        if ($record.Action -notin @("CREATE", "REPLACE")) {
            continue
        }
        Ensure-Directory (Split-Path -Parent $record.TargetPath) $false
        Copy-Item -LiteralPath $record.SourcePath -Destination $record.TargetPath -Force
        $script:FileCount += 1
    }
}

function Write-PackageMetadataAtomically {
    param(
        [string]$SourcePath,
        [string]$TargetPath
    )

    $targetDirectory = Split-Path -Parent $TargetPath
    Ensure-Directory $targetDirectory $false
    $targetName = Split-Path -Leaf $TargetPath
    $temporaryPath = Join-Path $targetDirectory (".$targetName.upgrade-" + [Guid]::NewGuid().ToString("N") + ".tmp")
    $backupPath = Join-Path $targetDirectory (".$targetName.upgrade-backup-" + [Guid]::NewGuid().ToString("N") + ".tmp")
    try {
        Copy-Item -LiteralPath $SourcePath -Destination $temporaryPath
        if (Test-Path -LiteralPath $TargetPath -PathType Leaf) {
            [System.IO.File]::Replace($temporaryPath, $TargetPath, $backupPath)
        } else {
            [System.IO.File]::Move($temporaryPath, $TargetPath)
        }
        $script:FileCount += 1
    }
    finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
        if (Test-Path -LiteralPath $backupPath) {
            Remove-Item -LiteralPath $backupPath -Force
        }
    }
}

function Apply-PackagePlanMetadata {
    param([object[]]$Plan)

    foreach ($record in @($Plan | Where-Object MetadataOrder -eq 1)) {
        if ($record.Action -notin @("CREATE", "REPLACE")) {
            continue
        }
        Write-PackageMetadataAtomically $record.SourcePath $record.TargetPath
    }
}

function Test-PackageLock {
    Push-Location $PackagePath
    try {
        & uv lock --check --default-index https://pypi.org/simple
        if ($LASTEXITCODE -ne 0) {
            throw "Package dependency lock is stale. Run 'uv lock --default-index https://pypi.org/simple' in the package root before upgrading."
        }
    }
    finally {
        Pop-Location
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
    ".codex/",
    ".obsidian/"
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
    $existingBytes = [System.IO.File]::ReadAllBytes($GitIgnorePath)
    $separator = ""
    if (
        $existingBytes.Length -gt 0 -and
        $existingBytes[$existingBytes.Length - 1] -ne [byte]0x0A -and
        $existingBytes[$existingBytes.Length - 1] -ne [byte]0x0D
    ) {
        $separator = "`n"
    }
    [System.IO.File]::AppendAllText($GitIgnorePath, "$separator$Line`n", $Utf8NoBomStrict)
}

function Ensure-GitIgnoreFile {
    param([string]$TargetPath)

    $gitIgnorePath = Join-Path $TargetPath ".gitignore"
    $templatePath = Join-Path $PackagePath ".gitignore"
    if (-not (Test-Path -LiteralPath $gitIgnorePath)) {
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
Assert-PackageSourcePathSafe $PackagePath "scripts/package-files.txt" "file" "Package file inventory"
foreach ($templateName in @("PROJECT.md", ".gitignore")) {
    Assert-PackageSourcePathSafe $PackagePath $templateName "file" "Package template"
}
$sameRoot = [string]::Equals($PackagePath, $TargetPath, $RootPathComparison)
$newMetadata = Read-PackageInventory $PackagePath $InventoryPath $true "New package"
$oldMetadata = Get-OldPackageOwnership $TargetPath
$plan = Get-PackagePlan $TargetPath $sameRoot $newMetadata $oldMetadata
$conflicts = @(
    Get-PlanConflicts $plan
    Get-TargetStructureConflicts $TargetPath $plan
)

$createCount = @($plan | Where-Object Action -eq "CREATE").Count
$replaceCount = @($plan | Where-Object Action -eq "REPLACE").Count
$removeCount = @($plan | Where-Object Action -eq "REMOVE").Count
$unchangedCount = @($plan | Where-Object Action -eq "UNCHANGED").Count
Write-Host "Package file plan: create $createCount, replace $replaceCount, remove $removeCount, unchanged $unchangedCount."

if ($conflicts.Count -gt 0) {
    foreach ($conflict in $conflicts) {
        [Console]::Error.WriteLine("Conflict: $conflict")
    }
    throw "Package update stopped before writing because target paths require attention."
}

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    throw "uv was not found. Install uv manually, then run this script again."
}
Test-PackageLock

Ensure-Directory $TargetPath $false
Apply-PackagePlanContent $plan
Ensure-ProjectFile $TargetPath
Ensure-GitIgnoreFile $TargetPath
Ensure-RuntimeStructure $TargetPath

Push-Location $TargetPath
try {
    & uv sync --locked --default-index https://pypi.org/simple
    if ($LASTEXITCODE -ne 0) {
        throw "Package dependency sync failed; ownership metadata was not advanced."
    }
}
finally {
    Pop-Location
}
if (-not $sameRoot) {
    Apply-PackagePlanMetadata $plan
}

Write-Host "Upgraded package files at: $TargetPath"
Write-Host "Copied package files: $script:FileCount"
Write-Host "Removed retired package files: $script:RemovedFileCount"
Write-Host "Created missing runtime entries: $script:CreatedRuntimeCount"
Write-Host "Existing .gitignore domain rules are preserved; only secret and technical-cache baseline rules are added."
