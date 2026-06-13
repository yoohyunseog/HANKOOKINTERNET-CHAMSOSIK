# Smart sync script for chamsosik
# Excludes: .exe, .json, .zip
# Smart image handling: skip if same name exists on server with non-zero size

param(
    [string]$Server = "root@211.45.162.155",
    [string]$RemoteRoot = "/var/www/chamsosik",
    [string]$RemoteTmp = "/tmp/chamsosik_upload_smart",
    [string]$SshOpts = "-o BatchMode=yes -o ConnectTimeout=15"
)

$ErrorActionPreference = 'Stop'

# Build Korean paths
$root = (Get-Location).Path
$krInternet = -join ([char[]](0xD55C,0xAD6D,0xC778,0xD130,0xB137,0x002E,0xD55C,0xAD6D))
$chamsosik = -join ([char[]](0xCC38,0xC18C,0xC2DD,0x002E,0x0063,0x006F,0x006D))
$local = Join-Path $root (Join-Path 'web\public' (Join-Path $krInternet $chamsosik))
$stage = Join-Path $env:TEMP "chamsosik_upload_smart"

Write-Host "[1/6] Checking local folder..." -ForegroundColor Cyan

if (!(Test-Path -LiteralPath $local)) {
    Write-Host "Local folder not found: $local" -ForegroundColor Red
    exit 1
}

# Clean and create staging folder
if (Test-Path -LiteralPath $stage) {
    Remove-Item -LiteralPath $stage -Recurse -Force
}
New-Item -ItemType Directory -Path $stage -Force | Out-Null

# Image extensions to check
$imageExtensions = @('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp')

# Get list of image files on server (with non-zero size)
Write-Host "[2/6] Getting image file list from server..." -ForegroundColor Cyan

$serverImageList = @{}
try {
    # Get all image files with size > 0 from server
    $findCmd = "find $RemoteRoot -type f \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.gif' -o -iname '*.webp' -o -iname '*.svg' -o -iname '*.ico' -o -iname '*.bmp' \) -size +0 2>/dev/null | while read f; do echo `"`$f|`$(stat -c%s `"`$f`" 2>/dev/null || echo 0)`"; done"
    
    $result = ssh $SshOpts.Split(' ') $Server $findCmd 2>$null
    
    foreach ($line in $result) {
        if ($line -match '^(.+)\|(\d+)$') {
            $filePath = $matches[1]
            $fileSize = [int64]$matches[2]
            $fileName = Split-Path $filePath -Leaf
            if ($fileSize -gt 0) {
                $serverImageList[$fileName] = $filePath
            }
        }
    }
    
    Write-Host "  Found $($serverImageList.Count) non-zero images on server" -ForegroundColor Green
} catch {
    Write-Host "  Warning: Could not get server image list, will upload all" -ForegroundColor Yellow
}

# Copy files to staging, excluding .exe, .json, .zip and smart image handling
Write-Host "[3/6] Copying files to staging folder..." -ForegroundColor Cyan

$skippedImages = @()
$copiedFiles = 0
$skippedZeroSize = 0

# Get all files recursively
$files = Get-ChildItem -LiteralPath $local -File -Recurse

foreach ($file in $files) {
    $relativePath = $file.FullName.Substring($local.Length).TrimStart('\', '/')
    $destPath = Join-Path $stage $relativePath
    $destDir = Split-Path $destPath -Parent
    
    # Check exclusion patterns
    $ext = $file.Extension.ToLower()
    $fileName = $file.Name
    
    # Skip .exe, .json, .zip, .lnk, .chromedriver, .bat
    if ($ext -in @('.exe', '.json', '.zip', '.lnk', '.chromedriver', '.bat')) {
        continue
    }
    
    # Skip node_modules and .git directories
    if ($relativePath -match 'node_modules|\.git') {
        continue
    }
    
    # Skip R: and W: drive references
    if ($relativePath -match '^R:\\|^W:\\') {
        continue
    }
    
    # Smart image handling
    if ($ext -in $imageExtensions) {
        # Check if local file has zero size
        if ($file.Length -eq 0) {
            $skippedZeroSize++
            continue
        }
        
        # Check if same filename exists on server with non-zero size
        if ($serverImageList.ContainsKey($fileName)) {
            $skippedImages += $fileName
            continue
        }
    }
    
    # Create destination directory and copy file
    if (!(Test-Path -LiteralPath $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    
    Copy-Item -LiteralPath $file.FullName -Destination $destPath -Force
    $copiedFiles++
}

Write-Host "  Copied: $copiedFiles files" -ForegroundColor Green
if ($skippedImages.Count -gt 0) {
    Write-Host "  Skipped $($skippedImages.Count) duplicate images:" -ForegroundColor Yellow
    $skippedImages | Select-Object -First 5 | ForEach-Object { Write-Host "    - $_" }
    if ($skippedImages.Count -gt 5) {
        Write-Host "    ... and $($skippedImages.Count - 5) more"
    }
}
if ($skippedZeroSize -gt 0) {
    Write-Host "  Skipped $skippedZeroSize zero-size images" -ForegroundColor Yellow
}

if ($copiedFiles -eq 0) {
    Write-Host "No files to upload." -ForegroundColor Yellow
    Remove-Item -LiteralPath $stage -Recurse -Force -ErrorAction SilentlyContinue
    exit 0
}

# Upload to server
Write-Host "[4/6] Uploading to server..." -ForegroundColor Cyan

ssh $SshOpts.Split(' ') $Server "rm -rf $RemoteTmp && mkdir -p $RemoteTmp"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create remote temp folder" -ForegroundColor Red
    exit 1
}

scp $SshOpts.Split(' ') -r "$stage\*" "${Server}:$RemoteTmp/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Upload failed" -ForegroundColor Red
    exit 1
}

# Move to final location
Write-Host "[5/6] Moving files to final location..." -ForegroundColor Cyan

ssh $SshOpts.Split(' ') $Server "sudo mkdir -p $RemoteRoot && sudo rsync -a $RemoteTmp/ $RemoteRoot/ && rm -rf $RemoteTmp"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Remote sync failed" -ForegroundColor Red
    exit 1
}

# Cleanup
Write-Host "[6/6] Cleaning up..." -ForegroundColor Cyan
Remove-Item -LiteralPath $stage -Recurse -Force

Write-Host "Done. Uploaded $copiedFiles files (excluded: .exe, .json, .zip, duplicate images)" -ForegroundColor Green
exit 0