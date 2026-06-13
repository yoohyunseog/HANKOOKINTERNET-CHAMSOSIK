$ErrorActionPreference = 'Stop'

$root = [IO.Path]::GetFullPath($PSScriptRoot)
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$logDir = Join-Path $root 'logs'
$workspaceRoot = [IO.DirectoryInfo]$root
for ($i = 0; $i -lt 4; $i++) {
    if ($null -eq $workspaceRoot.Parent) { break }
    $workspaceRoot = $workspaceRoot.Parent
}
$backupRoot = Join-Path $workspaceRoot.FullName "restore_backups\clarity_repair_$timestamp"
$logFile = Join-Path $logDir "clarity_repair_$timestamp.log"

New-Item -ItemType Directory -Force -Path $logDir | Out-Null
New-Item -ItemType Directory -Force -Path $backupRoot | Out-Null

function Write-Log {
    param([string]$Message)
    Write-Host $Message
    Add-Content -LiteralPath $logFile -Value $Message -Encoding UTF8
}

function Write-LogWarning {
    param([string]$Message)
    Write-Warning $Message
    Add-Content -LiteralPath $logFile -Value "WARNING: $Message" -Encoding UTF8
}

$snippet = @'
<script type="text/javascript">
    (function(c,l,a,r,i,t,y){
        c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
        t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
        y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
    })(window, document, "clarity", "script", "x4jlyqheuh");
</script>
'@

$clarityScriptPattern = '(?is)<script\b[^>]*>.*?(?:clarity\.ms/tag|x4jlyqheuh).*?</script>'
$utf8NoBom = [Text.UTF8Encoding]::new($false)

$added = 0
$fixed = 0
$skipped = 0
$failed = 0

Write-Log "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Log "Root: $root"
Write-Log "Backup: $backupRoot"
Write-Log ''

Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.html' |
    Where-Object { $_.FullName -notmatch '\\backups\\' } |
    ForEach-Object {
        $path = $_.FullName
        $relative = $path.Substring($root.Length).TrimStart('\', '/')

        try {
            $html = [IO.File]::ReadAllText($path)
            $cleaned = [regex]::Replace($html, $clarityScriptPattern, '').TrimEnd()

            if ($cleaned -eq $html -and $html.Contains($snippet)) {
                Write-Log "SKIPPED $relative"
                $skipped++
                return
            }

            if ($cleaned -eq $html -and $html -notmatch 'clarity\.ms/tag' -and $html -notmatch 'x4jlyqheuh') {
                $action = 'ADDED  '
                $baseHtml = $html
            } else {
                $action = 'FIXED  '
                $baseHtml = $cleaned
            }

            if ($baseHtml -match '(?i)</head\s*>') {
                $updated = [regex]::Replace($baseHtml, '(?i)</head\s*>', ($snippet + [Environment]::NewLine + '$0'), 1)
            } elseif ($baseHtml -match '(?i)</body\s*>') {
                $updated = [regex]::Replace($baseHtml, '(?i)</body\s*>', ($snippet + [Environment]::NewLine + '$0'), 1)
            } else {
                $updated = $baseHtml.TrimEnd() + [Environment]::NewLine + $snippet + [Environment]::NewLine
            }

            $backupPath = Join-Path $backupRoot $relative
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupPath) | Out-Null
            Copy-Item -LiteralPath $path -Destination $backupPath -Force

            [IO.File]::WriteAllText($path, $updated, $utf8NoBom)

            Write-Log "$action $relative"
            if ($action.Trim() -eq 'ADDED') {
                $added++
            } else {
                $fixed++
            }
        } catch {
            Write-LogWarning "FAILED  $relative - $($_.Exception.Message)"
            $failed++
        }
    }

Write-Log ''
Write-Log ('Done. Added: {0}, Fixed: {1}, Skipped: {2}, Failed: {3}' -f $added, $fixed, $skipped, $failed)
Write-Log "Finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

if ($failed -gt 0) {
    exit 1
}

exit 0
