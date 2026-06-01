# 한국인터넷.한국 폴더 업로드 스크립트
# .zip 파일 제외

$LOCAL_PATH = "E:\Ai project\사이트\web\public\한국인터넷.한국"
$REMOTE_SERVER = "root@211.45.162.155"
$REMOTE_PATH = "/var/www/한국인터넷.한국"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "한국인터넷.한국 폴더 업로드 스크립트" -ForegroundColor Cyan
Write-Host ".zip 파일 제외" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date
Write-Host "업로드 시작: $($startTime)" -ForegroundColor Green
Write-Host ""

# 현재 폴더의 파일들 업로드 (.zip 제외)
Write-Host "파일 업로드 중..." -ForegroundColor Yellow
$files = @(
    "ads.txt",
    "calculator.html",
    "data-crawler.html",
    "domain-check.js",
    "domain-report.html",
    "icnn-history.html",
    "index.html",
    "quest-board.html",
    "script.js",
    "style.css"
)

foreach ($file in $files) {
    $localFile = Join-Path $LOCAL_PATH $file
    if (Test-Path $localFile) {
        Write-Host "  업로드: $file" -ForegroundColor Gray
        & scp $localFile "${REMOTE_SERVER}:${REMOTE_PATH}/"
    }
}

Write-Host ""
Write-Host "하위 폴더 업로드 중..." -ForegroundColor Yellow

# 폴더 업로드 함수 (.zip 제외)
function Upload-Folder {
    param(
        [string]$FolderName
    )
    
    Write-Host "[$FolderName 폴더 업로드 - .zip 제외]" -ForegroundColor Cyan
    
    $sourcePath = Join-Path $LOCAL_PATH $FolderName
    
    # 임시 폴더 생성
    $tempPath = Join-Path $env:TEMP "upload_temp_$FolderName"
    if (Test-Path $tempPath) {
        Remove-Item -Recurse -Force $tempPath
    }
    New-Item -ItemType Directory -Path $tempPath -Force | Out-Null
    
    # .zip 파일 제외하고 복사
    Get-ChildItem -Path $sourcePath -Recurse -File | Where-Object { $_.Extension -ne '.zip' } | ForEach-Object {
        $relativePath = $_.FullName.Substring($sourcePath.Length)
        $destPath = Join-Path $tempPath $relativePath
        $destDir = Split-Path $destPath -Parent
        
        if (-not (Test-Path $destDir)) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
        
        Copy-Item $_.FullName $destPath -Force
    }
    
    # 업로드
    & scp -r $tempPath "${REMOTE_SERVER}:${REMOTE_PATH}/"
    
    # 원격에서 폴더 이름 변경
    & ssh $REMOTE_SERVER "mv '${REMOTE_PATH}/upload_temp_${FolderName}' '${REMOTE_PATH}/${FolderName}'" 2>$null
    
    # 임시 폴더 삭제
    Remove-Item -Recurse -Force $tempPath
}

# 각 폴더 업로드
$folders = @("assets", "GAME", "미분적분", "보이니치")

foreach ($folder in $folders) {
    Upload-Folder -FolderName $folder
    Write-Host ""
}

$endTime = Get-Date
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "업로드 완료: $($endTime)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "제외된 항목:" -ForegroundColor Yellow
Write-Host "  - .git 폴더" -ForegroundColor Gray
Write-Host "  - .gitignore" -ForegroundColor Gray
Write-Host "  - 참소식.com 폴더" -ForegroundColor Gray
Write-Host "  - 모든 .zip 파일 (*.zip)" -ForegroundColor Gray
Write-Host "  - upload_to_server.bat" -ForegroundColor Gray
Write-Host "  - upload_to_server.ps1" -ForegroundColor Gray
Write-Host "  - download_bootstrap.bat" -ForegroundColor Gray
Write-Host ""