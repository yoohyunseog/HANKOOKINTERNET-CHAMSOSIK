# 전체 파이프라인 실행
# encoding: utf-8

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   전체 파이프라인 실행" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Python 경로 찾기
function Get-PythonPath {
    $venvPaths = @(
        Join-Path $baseDir ".venv\Scripts\python.exe"
        Join-Path (Split-Path -Parent $baseDir) ".venv\Scripts\python.exe"
        Join-Path (Split-Path -Parent (Split-Path -Parent $baseDir)) ".venv\Scripts\python.exe"
    )
    
    foreach ($path in $venvPaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    
    return "python"
}

$python = Get-PythonPath
Write-Host "[Python] $python" -ForegroundColor Gray
Write-Host ""

Write-Host "이 스크립트는 전체 데이터 처리 파이프라인을 실행합니다." -ForegroundColor Yellow
Write-Host ""
Write-Host "[1단계] 원문 수집"
Write-Host "[2단계] JSONL 변환"
Write-Host "[3단계] 한국어 번역 (선택사항)"
Write-Host "[4단계] 데이터 검증"
Write-Host ""

$confirm = Read-Host "계속하시겠습니까? (Y/N)"
if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "취소되었습니다." -ForegroundColor Red
    Read-Host "계속하려면 Enter를 누르세요"
    exit 0
}

# 1단계: 원문 수집
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   [1/4] 원문 수집" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1] Chinese Text Project 수집"
Write-Host "[2] 위키문헌 수집"
Write-Host "[3] Project Gutenberg 수집"
Write-Host "[4] 모두 수집"
Write-Host "[5] 건너뛰기"
Write-Host ""

$fetchChoice = Read-Host "선택 (번호)"

switch ($fetchChoice) {
    "1" {
        Write-Host "Chinese Text Project 수집 중..." -ForegroundColor Yellow
        & $python (Join-Path $scriptDir "fetch_ctext.py")
    }
    "2" {
        Write-Host "위키문헌 수집 중..." -ForegroundColor Yellow
        & $python (Join-Path $scriptDir "fetch_wikisource.py")
    }
    "3" {
        Write-Host "Project Gutenberg 수집 중..." -ForegroundColor Yellow
        & $python (Join-Path $scriptDir "fetch_gutenberg.py")
    }
    "4" {
        Write-Host "Chinese Text Project..." -ForegroundColor Yellow
        & $python (Join-Path $scriptDir "fetch_ctext.py")
        Write-Host ""
        Write-Host "위키문헌..." -ForegroundColor Yellow
        & $python (Join-Path $scriptDir "fetch_wikisource.py")
        Write-Host ""
        Write-Host "Project Gutenberg..." -ForegroundColor Yellow
        & $python (Join-Path $scriptDir "fetch_gutenberg.py")
    }
    "5" {
        Write-Host "건너뜁니다." -ForegroundColor Gray
    }
    default {
        Write-Host "잘못된 선택입니다. 건너뜁니다." -ForegroundColor Red
    }
}

# 2단계: JSONL 변환
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   [2/4] JSONL 변환" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "원문을 JSONL로 변환 중..." -ForegroundColor Yellow
& $python (Join-Path $scriptDir "convert_to_jsonl.py")

# 3단계: 한국어 번역
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   [3/4] 한국어 번역" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$translate = Read-Host "한국어 번역을 실행하시겠습니까? (Y/N)"
if ($translate -eq "Y" -or $translate -eq "y") {
    Write-Host "[주의] OpenAI API 키가 필요합니다." -ForegroundColor Red
    & $python (Join-Path $scriptDir "translate_korean.py")
} else {
    Write-Host "건너뜁니다." -ForegroundColor Gray
}

# 4단계: 데이터 검증
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   [4/4] 데이터 검증" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "데이터 검증 중..." -ForegroundColor Yellow
& $python (Join-Path $scriptDir "validate_data.py")

# 완료
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "   전체 파이프라인 완료!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "결과 파일 위치:" -ForegroundColor Yellow
Write-Host "  - raw/          : 원문 텍스트"
Write-Host "  - processed/    : JSONL 데이터"
Write-Host "  - metadata/     : 메타데이터"
Write-Host ""

Read-Host "계속하려면 Enter를 누르세요"
