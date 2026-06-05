# 웹 스크래핑 - 원문 수집 + 자동 한국어 번역 (Playwright/Chrome)
# UTF-8 BOM 인코딩으로 한글 메뉴 지원

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   웹 스크래핑 + 자동 한국어 번역" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Python 경로 찾기
function Get-PythonPath {
    $possiblePaths = @(
        "E:\Ai project\사이트\.venv\Scripts\python.exe"
        "E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com\ai\Fine-tuning\.venv\Scripts\python.exe"
        "python"
    )
    
    foreach ($path in $possiblePaths) {
        if ($path -eq "python") {
            return "python"
        }
        if (Test-Path $path) {
            Write-Host "[Python] $path" -ForegroundColor Gray
            return $path
        }
    }
    
    return "python"
}

$python = Get-PythonPath
Write-Host ""

# Playwright 설치 확인
Write-Host "Playwright 설치 확인 중..." -ForegroundColor Yellow
& $python -c "import playwright" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[설치] Playwright 설치 중..." -ForegroundColor Yellow
    & $python -m pip install playwright requests --quiet
    & $python -m playwright install chromium
    Write-Host "[완료] Playwright 설치 완료" -ForegroundColor Green
}

Write-Host ""
Write-Host "[1] Chinese Text Project 스크래핑 (ctext.org)"
Write-Host "[2] 위키문헌 스크래핑 (wikisource.org)"
Write-Host "[3] 전체 스크래핑"
Write-Host ""

$choice = Read-Host "선택 (번호)"

switch ($choice) {
    "1" { 
        Write-Host ""
        Write-Host "Chinese Text Project 스크래핑 시작..." -ForegroundColor Yellow
        Write-Host "크롬 브라우저가 실행됩니다." -ForegroundColor Gray
        & $python (Join-Path $scriptDir "scraper_ctext.py") 
    }
    "2" { 
        Write-Host ""
        Write-Host "위키문헌 스크래핑 시작..." -ForegroundColor Yellow
        Write-Host "크롬 브라우저가 실행됩니다." -ForegroundColor Gray
        & $python (Join-Path $scriptDir "scraper_wikisource.py") 
    }
    "3" { 
        Write-Host ""
        Write-Host "전체 스크래핑 시작..." -ForegroundColor Yellow
        Write-Host "크롬 브라우저가 실행됩니다." -ForegroundColor Gray
        & $python (Join-Path $scriptDir "scraper_ctext.py")
        & $python (Join-Path $scriptDir "scraper_wikisource.py")
    }
    default { Write-Host "잘못된 선택입니다." -ForegroundColor Red }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   스크래핑 완료!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "저장 위치:" -ForegroundColor Cyan
Write-Host "  - 원문: raw/" -ForegroundColor Gray
Write-Host "  - 번역: processed/" -ForegroundColor Gray
Write-Host ""
Read-Host "계속하려면 Enter를 누르세요"