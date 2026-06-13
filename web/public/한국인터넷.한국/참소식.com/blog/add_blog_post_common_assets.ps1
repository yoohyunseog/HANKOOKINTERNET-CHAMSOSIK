param(
    [switch]$DryRun,
    [switch]$NoPause
)

$ErrorActionPreference = 'Stop'

function New-RelativeHref {
    param(
        [Parameter(Mandatory = $true)][string]$FromDirectory,
        [Parameter(Mandatory = $true)][string]$ToFile
    )

    $from = [System.IO.Path]::GetFullPath($FromDirectory).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
    $to = [System.IO.Path]::GetFullPath($ToFile)
    $fromUri = [Uri]$from
    $toUri = [Uri]$to
    return [Uri]::UnescapeDataString($fromUri.MakeRelativeUri($toUri).ToString()).Replace('\', '/')
}

function Add-BeforeHeadEnd {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Insert
    )

    if ($Content -match '(?i)</head>') {
        return [regex]::Replace($Content, '(?i)</head>', ($Insert + "`r`n</head>"), 1)
    }

    return $Content + "`r`n" + $Insert + "`r`n"
}

function Add-BeforeBodyEnd {
    param(
        [Parameter(Mandatory = $true)][string]$Content,
        [Parameter(Mandatory = $true)][string]$Insert
    )

    if ($Content -match '(?i)</body>') {
        return [regex]::Replace($Content, '(?i)</body>', ($Insert + "`r`n</body>"), 1)
    }

    return $Content + "`r`n" + $Insert + "`r`n"
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if ((Test-Path -LiteralPath (Join-Path $scriptRoot 'posts')) -and (Test-Path -LiteralPath (Join-Path $scriptRoot 'js\view-tracker.js'))) {
    $blogRoot = $scriptRoot
    $siteRoot = Split-Path -Parent $blogRoot
} else {
    $krInternet = -join ([char[]](0xD55C,0xAD6D,0xC778,0xD130,0xB137,0x002E,0xD55C,0xAD6D))
    $chamsosik = -join ([char[]](0xCC38,0xC18C,0xC2DD,0x002E,0x0063,0x006F,0x006D))
    $siteRoot = Join-Path $scriptRoot (Join-Path 'web\public' (Join-Path $krInternet $chamsosik))
    $blogRoot = Join-Path $siteRoot 'blog'
}

$postsRoot = Join-Path $blogRoot 'posts'
$faviconFile = Join-Path $siteRoot 'favicon.svg'
$viewTrackerFile = Join-Path $blogRoot 'js\view-tracker.js'

if (!(Test-Path -LiteralPath $postsRoot)) {
    throw "Posts folder not found: $postsRoot"
}
if (!(Test-Path -LiteralPath $faviconFile)) {
    throw "Favicon file not found: $faviconFile"
}
if (!(Test-Path -LiteralPath $viewTrackerFile)) {
    throw "View tracker file not found: $viewTrackerFile"
}

$adsClient = 'ca-pub-4501795912654667'
$adsScript = "  <script async src=""https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=$adsClient"" crossorigin=""anonymous""></script>"

$files = Get-ChildItem -LiteralPath $postsRoot -Filter '*.html' -File -Recurse
$changed = 0
$checked = 0
$changeLog = New-Object System.Collections.Generic.List[string]

Write-Host "[start] Blog root: $blogRoot"
Write-Host "[start] Posts root: $postsRoot"
Write-Host "[start] Site favicon: $faviconFile"
Write-Host "[start] View tracker: $viewTrackerFile"
Write-Host "[start] Mode: $(if ($DryRun) { 'dry-run, no files will be changed' } else { 'write changes' })"
Write-Host "[scan] Found $($files.Count) HTML files."
Write-Host ""

foreach ($file in $files) {
    $checked++
    $content = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8
    $updated = $content
    $actions = New-Object System.Collections.Generic.List[string]
    $fileDir = Split-Path -Parent $file.FullName

    $faviconHref = New-RelativeHref -FromDirectory $fileDir -ToFile $faviconFile
    if ($updated -notmatch '(?is)<link\b[^>]*rel=["''][^"'']*\bicon\b') {
        $faviconInsert = "  <link rel=""icon"" href=""$faviconHref"" type=""image/svg+xml"">"
        $updated = Add-BeforeHeadEnd -Content $updated -Insert $faviconInsert
        $actions.Add('favicon')
    }
    if ($updated -notmatch '(?is)<link\b[^>]*rel=["''][^"'']*\bapple-touch-icon\b') {
        $appleInsert = "  <link rel=""apple-touch-icon"" href=""$faviconHref"">"
        $updated = Add-BeforeHeadEnd -Content $updated -Insert $appleInsert
        $actions.Add('apple-touch-icon')
    }

    if ($updated -notmatch 'pagead2\.googlesyndication\.com/pagead/js/adsbygoogle\.js') {
        $updated = Add-BeforeHeadEnd -Content $updated -Insert $adsScript
        $actions.Add('google-ads')
    }

    if ($updated -notmatch 'view-tracker\.js') {
        $trackerHref = New-RelativeHref -FromDirectory $fileDir -ToFile $viewTrackerFile
        $trackerInsert = @"
  <script src="$trackerHref"></script>
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      if (window.BlogViewTracker) {
        window.BlogViewTracker.trackPostVisit();
      }
    });
  </script>
"@
        $updated = Add-BeforeBodyEnd -Content $updated -Insert $trackerInsert.TrimEnd()
        $actions.Add('view-tracker')
    } elseif ($updated -match 'view-tracker\.js' -and $updated -notmatch 'trackPostVisit\s*\(') {
        $trackCall = @"
  <script>
    document.addEventListener('DOMContentLoaded', function() {
      if (window.BlogViewTracker) {
        window.BlogViewTracker.trackPostVisit();
      }
    });
  </script>
"@
        $updated = Add-BeforeBodyEnd -Content $updated -Insert $trackCall.TrimEnd()
        $actions.Add('view-track-call')
    }

    if ($updated -ne $content) {
        $changed++
        $relative = $file.FullName.Substring($postsRoot.Length).TrimStart('\', '/')
        $changeLog.Add(("{0}: {1}" -f $relative, ($actions -join ', ')))

        if (!$DryRun) {
            Set-Content -LiteralPath $file.FullName -Value $updated -Encoding UTF8
            Write-Host ("[UPDATE] {0}" -f $relative) -ForegroundColor Yellow
        } else {
            Write-Host ("[WOULD UPDATE] {0}" -f $relative) -ForegroundColor Yellow
        }
        Write-Host ("         added/fixed: {0}" -f ($actions -join ', '))
    } else {
        $relative = $file.FullName.Substring($postsRoot.Length).TrimStart('\', '/')
        Write-Host ("[OK] {0}" -f $relative) -ForegroundColor Green
    }
}

Write-Host ""
if ($DryRun) {
    Write-Host "[summary] Checked $checked HTML files. Would update $changed files."
} else {
    Write-Host "[summary] Checked $checked HTML files. Updated $changed files."
}

if ($changeLog.Count -gt 0) {
    Write-Host ""
    Write-Host "[changed files]"
    $changeLog | ForEach-Object { Write-Host " - $_" }
} else {
    Write-Host "[changed files] None. Everything is already complete."
}
