$ErrorActionPreference = "Stop"

$Server = "root@211.45.162.155"
$LocalDir = "E:\Ai project\사이트\web\public\한국인터넷.한국\보이니치\pen-export-emzyZae"
$RemoteDir = "/var/www/한국인터넷.한국/보이니치/pen-export-emzyZae"
$RemoteTmp = "/tmp/voynich_pen_export_upload"

if (-not (Test-Path -LiteralPath $LocalDir)) {
  throw "Local folder not found: $LocalDir"
}

Write-Host "[1/5] Remove remote temporary folder..."
& ssh $Server "rm -rf $RemoteTmp"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/5] Create remote temporary folder..."
& ssh $Server "mkdir -p $RemoteTmp"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[3/5] Upload folder contents..."
& scp -r "$LocalDir\*" "${Server}:$RemoteTmp/"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/5] Mirror to final remote folder..."
& ssh $Server "sudo mkdir -p '$RemoteDir'"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& ssh $Server "sudo rsync -a --delete $RemoteTmp/ '$RemoteDir/'"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[5/5] Clean temporary folder..."
& ssh $Server "rm -rf $RemoteTmp"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Upload completed."
Write-Host "Local : $LocalDir"
Write-Host "Remote: $RemoteDir"
