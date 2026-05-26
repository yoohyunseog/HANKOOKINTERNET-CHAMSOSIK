param(
    [string]$Drive = "C:",
    [int]$MinAgeDays = 7,
    [string]$OllamaUrl = "http://localhost:11434",
    [string]$Model = $env:OLLAMA_MODEL,
    [switch]$Clean,
    [switch]$Deep,
    [switch]$NoAi,
    [switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "SilentlyContinue"

$driveRoot = ([System.IO.Path]::GetPathRoot($Drive)).TrimEnd("\")
if (-not $driveRoot) {
    $driveRoot = $Drive.TrimEnd("\")
}
if ($driveRoot -notmatch "^[A-Za-z]:$") {
    throw "Drive must look like C: or D:"
}
if ([string]::IsNullOrWhiteSpace($Model)) {
    $Model = "deepseek-v4-flash:cloud"
}
$driveRootWithSlash = "$driveRoot\"
$cutoff = (Get-Date).AddDays(-1 * [Math]::Abs($MinAgeDays))
$repoRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$reportDir = Join-Path $repoRoot "data\cleanup-reports"
$logDir = Join-Path $repoRoot "data\cleanup-logs"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$mdReport = Join-Path $reportDir "c-drive-cleaner-$stamp.md"
$jsonReport = Join-Path $reportDir "c-drive-cleaner-$stamp.json"
$logFile = Join-Path $logDir "c-drive-cleaner-$stamp.log"

function Format-Bytes {
    param([double]$Bytes)
    if ($Bytes -ge 1TB) { return "{0:N2} TB" -f ($Bytes / 1TB) }
    if ($Bytes -ge 1GB) { return "{0:N2} GB" -f ($Bytes / 1GB) }
    if ($Bytes -ge 1MB) { return "{0:N2} MB" -f ($Bytes / 1MB) }
    if ($Bytes -ge 1KB) { return "{0:N2} KB" -f ($Bytes / 1KB) }
    return "{0:N0} B" -f $Bytes
}

function Test-SafeTarget {
    param([string]$Path)
    if (-not $Path) { return $false }
    if (-not (Test-Path -LiteralPath $Path)) { return $false }
    $resolved = (Resolve-Path -LiteralPath $Path).Path.TrimEnd("\")
    if ($resolved.Length -lt 8) { return $false }
    if ($resolved -ieq $driveRoot -or $resolved -ieq $driveRootWithSlash.TrimEnd("\")) { return $false }
    $allowedFragments = @(
        "\Temp",
        "\AppData\Local\Temp",
        "\AppData\Local\Microsoft\Windows\INetCache",
        "\AppData\Local\Microsoft\Edge\User Data",
        "\AppData\Local\Google\Chrome\User Data",
        "\AppData\Local\Mozilla\Firefox\Profiles",
        "\AppData\Local\npm-cache",
        "\AppData\Local\pip\cache",
        "\AppData\Local\NuGet\Cache",
        "\AppData\Local\D3DSCache"
    )
    foreach ($fragment in $allowedFragments) {
        if ($resolved.IndexOf($fragment, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
            return $true
        }
    }
    return $false
}

function Get-FolderBytes {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return 0L }
    $sum = 0L
    Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue |
        ForEach-Object { $sum += $_.Length }
    return $sum
}

function Get-OldBytes {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return 0L }
    $sum = 0L
    Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff } |
        ForEach-Object { $sum += $_.Length }
    return $sum
}

function Remove-OldContent {
    param([string]$Path)
    $removedBytes = 0L
    $removedItems = 0
    $errors = 0

    if (-not (Test-SafeTarget -Path $Path)) {
        return [pscustomobject]@{
            path = $Path
            removedBytes = 0L
            removedItems = 0
            errors = 1
            note = "Skipped: path is not in the safe-clean allow list."
        }
    }

    $files = Get-ChildItem -LiteralPath $Path -Force -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -lt $cutoff }
    foreach ($file in $files) {
        $size = $file.Length
        Remove-Item -LiteralPath $file.FullName -Force -ErrorAction SilentlyContinue
        if (Test-Path -LiteralPath $file.FullName) {
            $errors++
        } else {
            $removedBytes += $size
            $removedItems++
        }
    }

    $dirs = Get-ChildItem -LiteralPath $Path -Force -Recurse -Directory -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending
    foreach ($dir in $dirs) {
        $hasChild = Get-ChildItem -LiteralPath $dir.FullName -Force -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $hasChild) {
            Remove-Item -LiteralPath $dir.FullName -Force -ErrorAction SilentlyContinue
        }
    }

    return [pscustomobject]@{
        path = $Path
        removedBytes = $removedBytes
        removedItems = $removedItems
        errors = $errors
        note = "Removed files older than $MinAgeDays day(s)."
    }
}

function Invoke-OllamaAdvice {
    param(
        [object]$Payload,
        [string]$Endpoint,
        [string]$ModelName
    )

    $promptData = $Payload | ConvertTo-Json -Depth 5
    $prompt = @"
You are a careful Windows disk-cleanup assistant.
Answer in Korean.
Use only the scan data below. Do not invent hidden folders.
Never recommend deleting personal files automatically.
Separate recommendations into:
1. Safe cleanup
2. Manual review
3. Things to avoid
Keep it short and practical.

Scan data:
$promptData
"@

    $body = @{
        model = $ModelName
        prompt = $prompt
        stream = $false
        options = @{
            temperature = 0.2
        }
    } | ConvertTo-Json -Depth 8

    try {
        $response = Invoke-RestMethod -Method Post -Uri "$Endpoint/api/generate" -Body $body -ContentType "application/json; charset=utf-8" -TimeoutSec 120
        if ($response.response) {
            return [pscustomobject]@{
                enabled = $true
                model = $ModelName
                ok = $true
                text = [string]$response.response
                error = $null
            }
        }
        return [pscustomobject]@{
            enabled = $true
            model = $ModelName
            ok = $false
            text = $null
            error = "Ollama returned no response text."
        }
    } catch {
        return [pscustomobject]@{
            enabled = $true
            model = $ModelName
            ok = $false
            text = $null
            error = $_.Exception.Message
        }
    }
}

function New-Candidate {
    param(
        [string]$Label,
        [string]$Path,
        [string]$Risk,
        [bool]$Cleanable,
        [string]$Action
    )
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    $totalBytes = Get-FolderBytes -Path $Path
    $oldBytes = if ($Cleanable) { Get-OldBytes -Path $Path } else { 0L }
    $score = 0
    if ($totalBytes -ge 1GB) { $score += 50 } elseif ($totalBytes -ge 250MB) { $score += 25 } elseif ($totalBytes -gt 0) { $score += 5 }
    if ($oldBytes -ge 1GB) { $score += 35 } elseif ($oldBytes -ge 250MB) { $score += 15 }
    if ($Risk -eq "Low") { $score += 15 } elseif ($Risk -eq "Medium") { $score += 5 }
    [pscustomobject]@{
        label = $Label
        path = $Path
        risk = $Risk
        cleanable = $Cleanable
        totalBytes = $totalBytes
        oldBytes = $oldBytes
        score = $score
        action = $Action
    }
}

$currentUser = [Environment]::GetFolderPath("UserProfile")
$localApp = [Environment]::GetFolderPath("LocalApplicationData")
$targets = @(
    @{ label = "Current user temp"; path = $env:TEMP; risk = "Low"; cleanable = $true; action = "Clean files older than the selected age." },
    @{ label = "Windows temp"; path = Join-Path $driveRootWithSlash "Windows\Temp"; risk = "Low"; cleanable = $true; action = "Clean old temp files. Run as administrator for best results." },
    @{ label = "Windows INetCache"; path = Join-Path $localApp "Microsoft\Windows\INetCache"; risk = "Low"; cleanable = $true; action = "Clean browser/system internet cache." },
    @{ label = "Edge cache"; path = Join-Path $localApp "Microsoft\Edge\User Data\Default\Cache"; risk = "Low"; cleanable = $true; action = "Clean old Edge cache files." },
    @{ label = "Edge code cache"; path = Join-Path $localApp "Microsoft\Edge\User Data\Default\Code Cache"; risk = "Low"; cleanable = $true; action = "Clean old Edge code cache files." },
    @{ label = "Chrome cache"; path = Join-Path $localApp "Google\Chrome\User Data\Default\Cache"; risk = "Low"; cleanable = $true; action = "Clean old Chrome cache files." },
    @{ label = "Chrome code cache"; path = Join-Path $localApp "Google\Chrome\User Data\Default\Code Cache"; risk = "Low"; cleanable = $true; action = "Clean old Chrome code cache files." },
    @{ label = "npm cache"; path = Join-Path $localApp "npm-cache"; risk = "Low"; cleanable = $true; action = "Clean old package cache files." },
    @{ label = "pip cache"; path = Join-Path $localApp "pip\cache"; risk = "Low"; cleanable = $true; action = "Clean old Python package cache files." },
    @{ label = "NuGet cache"; path = Join-Path $localApp "NuGet\Cache"; risk = "Low"; cleanable = $true; action = "Clean old NuGet cache files." },
    @{ label = "Downloads"; path = Join-Path $currentUser "Downloads"; risk = "Manual"; cleanable = $false; action = "Review manually; the bot never deletes Downloads." },
    @{ label = "Desktop"; path = Join-Path $currentUser "Desktop"; risk = "Manual"; cleanable = $false; action = "Review manually; the bot never deletes Desktop files." }
)

$candidates = foreach ($target in $targets) {
    New-Candidate -Label $target.label -Path $target.path -Risk $target.risk -Cleanable $target.cleanable -Action $target.action
}
$candidates = @($candidates | Where-Object { $_ -ne $null } | Sort-Object score, totalBytes -Descending)

$topDirs = @()
Get-ChildItem -LiteralPath $driveRootWithSlash -Force -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notin @("Windows", "Program Files", "Program Files (x86)", "ProgramData", "Users") } |
    ForEach-Object {
        $bytes = Get-FolderBytes -Path $_.FullName
        if ($bytes -gt 0) {
            $topDirs += [pscustomobject]@{
                path = $_.FullName
                totalBytes = $bytes
                note = "Manual review only."
            }
        }
    }
$topDirs = @($topDirs | Sort-Object totalBytes -Descending | Select-Object -First 10)

$cleanResults = @()
if ($Clean) {
    foreach ($candidate in ($candidates | Where-Object { $_.cleanable -and $_.oldBytes -gt 0 })) {
        $cleanResults += Remove-OldContent -Path $candidate.path
    }
}

$deepResults = @()
if ($Deep) {
    if ($Clean) {
        Clear-RecycleBin -DriveLetter $driveRoot.TrimEnd(":") -Force -ErrorAction SilentlyContinue
        $deepResults += [pscustomobject]@{ action = "Recycle Bin"; note = "Clear-RecycleBin was requested." }
        $dism = Start-Process -FilePath "dism.exe" -ArgumentList "/Online /Cleanup-Image /StartComponentCleanup" -Wait -PassThru -WindowStyle Hidden -ErrorAction SilentlyContinue
        $deepResults += [pscustomobject]@{ action = "DISM component cleanup"; exitCode = if ($dism) { $dism.ExitCode } else { $null } }
    } else {
        $deepResults += [pscustomobject]@{ action = "Deep cleanup"; note = "Skipped because -Clean was not provided." }
    }
}

$disk = Get-CimInstance Win32_LogicalDisk -Filter "DeviceID='$driveRoot'" -ErrorAction SilentlyContinue
$totalRemoved = 0L
foreach ($result in $cleanResults) { $totalRemoved += [int64]$result.removedBytes }

$aiInput = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("s")
    drive = $driveRoot
    mode = if ($Clean) { "clean" } else { "dry-run" }
    minAgeDays = $MinAgeDays
    freeBytes = if ($disk) { [int64]$disk.FreeSpace } else { $null }
    sizeBytes = if ($disk) { [int64]$disk.Size } else { $null }
    estimatedCleanableBytes = [int64](($candidates | Measure-Object oldBytes -Sum).Sum)
    removedBytes = $totalRemoved
    candidates = @($candidates | Select-Object -First 12 label, path, risk, cleanable, totalBytes, oldBytes, action)
    manualReview = @($topDirs | Select-Object -First 10 path, totalBytes, note)
    cleanResults = $cleanResults
}

$aiAdvice = if ($NoAi) {
    [pscustomobject]@{
        enabled = $false
        model = $Model
        ok = $false
        text = $null
        error = "Skipped because -NoAi was provided."
    }
} else {
    Invoke-OllamaAdvice -Payload $aiInput -Endpoint $OllamaUrl.TrimEnd("/") -ModelName $Model
}

$summary = [pscustomobject]@{
    generatedAt = (Get-Date).ToString("s")
    drive = $driveRoot
    mode = if ($Clean) { "clean" } else { "dry-run" }
    minAgeDays = $MinAgeDays
    freeBytes = if ($disk) { [int64]$disk.FreeSpace } else { $null }
    sizeBytes = if ($disk) { [int64]$disk.Size } else { $null }
    estimatedCleanableBytes = [int64](($candidates | Measure-Object oldBytes -Sum).Sum)
    removedBytes = $totalRemoved
    logFile = $logFile
    markdownReport = $mdReport
    jsonReport = $jsonReport
    candidates = $candidates
    manualReview = $topDirs
    cleanResults = $cleanResults
    deepResults = $deepResults
    aiAdvice = $aiAdvice
}

$lines = @()
$lines += "# C Drive AI Cleaner Report"
$lines += ""
$lines += "- Generated: $($summary.generatedAt)"
$lines += "- Drive: $driveRoot"
$lines += "- Mode: $($summary.mode)"
if ($disk) {
    $lines += "- Disk free: $(Format-Bytes $disk.FreeSpace) / $(Format-Bytes $disk.Size)"
}
$lines += "- Estimated safe cleanup: $(Format-Bytes $summary.estimatedCleanableBytes)"
$lines += "- Actually removed: $(Format-Bytes $summary.removedBytes)"
$lines += "- Ollama model: $Model"
$lines += "- Log file: ``$logFile``"
$lines += ""
$lines += "## Ollama AI advice"
$lines += ""
if ($aiAdvice.ok -and $aiAdvice.text) {
    $lines += $aiAdvice.text.Trim()
} elseif ($aiAdvice.enabled) {
    $lines += "Ollama advice was unavailable: $($aiAdvice.error)"
} else {
    $lines += "Ollama advice was skipped."
}
$lines += ""
$lines += "## AI-ranked cleanup candidates"
$lines += ""
$lines += "| Score | Risk | Total | Old cleanable | Path | Action |"
$lines += "| ---: | --- | ---: | ---: | --- | --- |"
foreach ($candidate in $candidates) {
    $lines += "| $($candidate.score) | $($candidate.risk) | $(Format-Bytes $candidate.totalBytes) | $(Format-Bytes $candidate.oldBytes) | ``$($candidate.path)`` | $($candidate.action) |"
}
$lines += ""
$lines += "## Manual review: large top-level folders"
$lines += ""
if ($topDirs.Count -eq 0) {
    $lines += "No large manual-review folders found outside standard Windows folders."
} else {
    $lines += "| Size | Path |"
    $lines += "| ---: | --- |"
    foreach ($dir in $topDirs) {
        $lines += "| $(Format-Bytes $dir.totalBytes) | ``$($dir.path)`` |"
    }
}
if ($cleanResults.Count -gt 0) {
    $lines += ""
    $lines += "## Clean results"
    $lines += ""
    $lines += "| Removed | Items | Errors | Path |"
    $lines += "| ---: | ---: | ---: | --- |"
    foreach ($result in $cleanResults) {
        $lines += "| $(Format-Bytes $result.removedBytes) | $($result.removedItems) | $($result.errors) | ``$($result.path)`` |"
    }
}
$lines += ""
$lines += "## Run commands"
$lines += ""
$lines += "- Scan only: ``powershell -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1``"
$lines += "- Scan with a specific Ollama model: ``powershell -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1 -Model deepseek-v4-flash:cloud``"
$lines += "- Clean safe old temp/cache files: ``powershell -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1 -Clean``"
$lines += "- Include recycle bin and Windows component cleanup: ``powershell -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1 -Clean -Deep``"
$lines += "- Disable Ollama advice: ``powershell -ExecutionPolicy Bypass -File tools\c_drive_ai_cleaner\c_drive_ai_cleaner.ps1 -NoAi``"

Set-Content -LiteralPath $mdReport -Value $lines -Encoding UTF8
$summary | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonReport -Encoding UTF8

$logLines = @()
$logLines += "[$($summary.generatedAt)] C Drive AI Cleaner started"
$logLines += "Drive: $driveRoot"
$logLines += "Mode: $($summary.mode)"
$logLines += "MinAgeDays: $MinAgeDays"
$logLines += "OllamaUrl: $OllamaUrl"
$logLines += "OllamaModel: $Model"
if ($disk) {
    $logLines += "DiskFree: $(Format-Bytes $disk.FreeSpace) / $(Format-Bytes $disk.Size)"
}
$logLines += "EstimatedSafeCleanup: $(Format-Bytes $summary.estimatedCleanableBytes)"
$logLines += "Removed: $(Format-Bytes $summary.removedBytes)"
$logLines += "MarkdownReport: $mdReport"
$logLines += "JsonReport: $jsonReport"
$logLines += "AiEnabled: $($aiAdvice.enabled)"
$logLines += "AiOk: $($aiAdvice.ok)"
if ($aiAdvice.error) {
    $logLines += "AiError: $($aiAdvice.error)"
}
$logLines += "TopCandidates:"
$candidates | Select-Object -First 8 | ForEach-Object {
    $logLines += ("- [{0}] {1}: total {2}, old {3}, path {4}" -f $_.risk, $_.label, (Format-Bytes $_.totalBytes), (Format-Bytes $_.oldBytes), $_.path)
}
if ($cleanResults.Count -gt 0) {
    $logLines += "CleanResults:"
    foreach ($result in $cleanResults) {
        $logLines += ("- removed {0}, items {1}, errors {2}, path {3}" -f (Format-Bytes $result.removedBytes), $result.removedItems, $result.errors, $result.path)
    }
}
$logLines += "[$((Get-Date).ToString("s"))] C Drive AI Cleaner finished"
Set-Content -LiteralPath $logFile -Value $logLines -Encoding UTF8

if ($Json) {
    $summary | ConvertTo-Json -Depth 6
} else {
    Write-Host "C Drive AI Cleaner"
    Write-Host "Mode: $($summary.mode)"
    if ($disk) {
        Write-Host "Free: $(Format-Bytes $disk.FreeSpace) / $(Format-Bytes $disk.Size)"
    }
    Write-Host "Estimated safe cleanup: $(Format-Bytes $summary.estimatedCleanableBytes)"
    Write-Host "Actually removed: $(Format-Bytes $summary.removedBytes)"
    if ($aiAdvice.ok -and $aiAdvice.text) {
        Write-Host ""
        Write-Host "Ollama advice ($Model):"
        Write-Host $aiAdvice.text.Trim()
    } elseif ($aiAdvice.enabled) {
        Write-Host "Ollama advice unavailable: $($aiAdvice.error)"
    }
    Write-Host "Report: $mdReport"
    Write-Host "Log: $logFile"
    Write-Host ""
    Write-Host "Top candidates:"
    $candidates | Select-Object -First 8 | ForEach-Object {
        Write-Host ("- [{0}] {1}: total {2}, old {3}" -f $_.risk, $_.label, (Format-Bytes $_.totalBytes), (Format-Bytes $_.oldBytes))
    }
}
