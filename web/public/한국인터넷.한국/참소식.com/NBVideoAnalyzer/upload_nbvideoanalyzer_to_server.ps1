# NBVideoAnalyzer Upload Script
# PowerShell version for proper Unicode path handling

$SERVER = "root@211.45.162.155"
$LOCAL_DIR = $PSScriptRoot
$REMOTE_DIR = "/var/www/chamsosik/NBVideoAnalyzer"

Write-Host "========================================"
Write-Host "NBVideoAnalyzer web server upload"
Write-Host "========================================"
Write-Host ""

if (-not (Test-Path $LOCAL_DIR)) {
    Write-Host "Local folder not found: $LOCAL_DIR"
    Read-Host "Press Enter to exit"
    exit 1
}

# Check SSH and SCP
$ssh = Get-Command ssh -ErrorAction SilentlyContinue
$scp = Get-Command scp -ErrorAction SilentlyContinue

if (-not $ssh) {
    Write-Host "ssh command not found. Install OpenSSH Client first."
    Read-Host "Press Enter to exit"
    exit 1
}

if (-not $scp) {
    Write-Host "scp command not found. Install OpenSSH Client first."
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Local: $LOCAL_DIR"
Write-Host ""
Write-Host "Remote: ${SERVER}:$REMOTE_DIR"
Write-Host ""

Write-Host "[1/3] Ensure remote folder exists..."
ssh $SERVER "sudo mkdir -p $REMOTE_DIR"
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Failed to create remote folder"
    Read-Host "Press Enter to exit"
    exit 1 
}

Write-Host "[2/3] Upload files to temporary location..."
ssh $SERVER "rm -rf /tmp/nbvideo_upload && mkdir -p /tmp/nbvideo_upload"
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Failed to create temp folder"
    Read-Host "Press Enter to exit"
    exit 1 
}

scp -r "$LOCAL_DIR\*" "${SERVER}:/tmp/nbvideo_upload/"
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Failed to upload files"
    Read-Host "Press Enter to exit"
    exit 1 
}

Write-Host "[3/3] Move files to final location with sudo..."
ssh $SERVER "sudo rsync -a /tmp/nbvideo_upload/ $REMOTE_DIR/ && sudo rm -rf /tmp/nbvideo_upload"
if ($LASTEXITCODE -ne 0) { 
    Write-Host "Failed to move files"
    Read-Host "Press Enter to exit"
    exit 1 
}

Write-Host ""
Write-Host "Upload complete."
Write-Host "URL path: /NBVideoAnalyzer/"
Write-Host ""
Read-Host "Press Enter to exit"