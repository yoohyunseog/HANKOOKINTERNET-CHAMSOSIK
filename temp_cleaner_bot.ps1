param(
    [string]$TargetPath = "C:\Users\dbghw\AppData\Local\Temp",
    [int]$OlderThanDays = 7,
    [switch]$DryRun,
    [switch]$Quiet,
    [switch]$VerboseLog,
    [switch]$Deep
)

$ErrorActionPreference = "Stop"

function Write-Status {
    param([string]$Message)
    if (-not $Quiet) {
        Write-Host $Message
    }
}

function Get-FullPath {
    param([string]$Path)
    return [System.IO.Path]::GetFullPath($Path).TrimEnd('\')
}

$expectedPath = Get-FullPath "C:\Users\dbghw\AppData\Local\Temp"
$fullTargetPath = Get-FullPath $TargetPath

if ($fullTargetPath -ne $expectedPath) {
    throw "Safety stop: this bot only cleans $expectedPath. Requested path was $fullTargetPath."
}

if (-not (Test-Path -LiteralPath $fullTargetPath -PathType Container)) {
    throw "Target folder does not exist: $fullTargetPath"
}

if ($OlderThanDays -lt 1) {
    throw "OlderThanDays must be 1 or higher."
}

$cutoff = (Get-Date).AddDays(-$OlderThanDays)
$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptRoot) {
    $scriptRoot = (Get-Location).Path
}

$logDir = Join-Path $scriptRoot "logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$logFile = Join-Path $logDir ("temp-cleaner-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))

$summary = [ordered]@{
    StartedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    TargetPath = $fullTargetPath
    OlderThanDays = $OlderThanDays
    DryRun = [bool]$DryRun
    RemovedFiles = 0
    RemovedFolders = 0
    SkippedItems = 0
    FreedBytes = 0
    Errors = 0
}

function Add-Log {
    param([string]$Message)
    Add-Content -LiteralPath $logFile -Value ("[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message) -Encoding UTF8
}

function Test-ItemSafeToRemove {
    param([System.IO.FileSystemInfo]$Item)

    if (($Item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        return $false
    }

    if (($Item.Attributes -band [System.IO.FileAttributes]::System) -ne 0) {
        return $false
    }

    if ($Item.LastWriteTime -gt $cutoff) {
        return $false
    }

    return $true
}

Write-Status "Temp Cleaner BOT"
Write-Status "Target: $fullTargetPath"
Write-Status "Mode: $(if ($DryRun) { 'preview only' } else { 'cleanup' })"
Write-Status "Deleting items older than $OlderThanDays day(s)."
Write-Status "Scan: $(if ($Deep) { 'deep recursive scan' } else { 'fast top-level scan' })"
Add-Log "Started. Target=$fullTargetPath OlderThanDays=$OlderThanDays DryRun=$DryRun"

$scanCount = 0
$scanParams = @{
    LiteralPath = $fullTargetPath
    Force = $true
    ErrorAction = "SilentlyContinue"
}

if ($Deep) {
    $scanParams.Recurse = $true
}

$items = Get-ChildItem @scanParams | Where-Object { Test-ItemSafeToRemove $_ }

foreach ($item in $items) {
    try {
        $isDirectory = $item.PSIsContainer
        $size = if ($isDirectory) { 0 } else { $item.Length }

        if ($DryRun) {
            if ($VerboseLog) {
                Add-Log "Would remove item: $($item.FullName)"
            }
        } else {
            Remove-Item -LiteralPath $item.FullName -Force -Recurse:$isDirectory -ErrorAction Stop
            if ($VerboseLog) {
                Add-Log "Removed item: $($item.FullName)"
            }
        }

        if ($isDirectory) {
            $summary.RemovedFolders++
        } else {
            $summary.RemovedFiles++
        }

        $summary.FreedBytes += $size
    } catch {
        $summary.SkippedItems++
        $summary.Errors++
        Add-Log "Skipped item: $($item.FullName) | $($_.Exception.Message)"
    }

    $scanCount++
    if ((-not $Quiet) -and ($scanCount % 100 -eq 0)) {
        $freedMbNow = [math]::Round($summary.FreedBytes / 1MB, 2)
        Write-Host ("Progress: {0} candidate(s), {1} MB" -f $scanCount, $freedMbNow)
    }
}

$summary.FinishedAt = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$freedMb = [math]::Round($summary.FreedBytes / 1MB, 2)
Add-Log "Finished. RemovedFiles=$($summary.RemovedFiles) RemovedFolders=$($summary.RemovedFolders) Skipped=$($summary.SkippedItems) FreedMB=$freedMb Errors=$($summary.Errors)"

Write-Status ""
Write-Status "Done."
Write-Status "Files: $($summary.RemovedFiles), folders: $($summary.RemovedFolders), skipped: $($summary.SkippedItems)"
Write-Status "Estimated space: $freedMb MB"
Write-Status "Log: $logFile"

if ($summary.Errors -gt 0) {
    exit 1
}

exit 0
