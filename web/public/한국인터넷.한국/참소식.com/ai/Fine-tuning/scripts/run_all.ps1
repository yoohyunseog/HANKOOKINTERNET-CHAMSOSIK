# 전체 파이프라인 실행

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   전체 파이프라인 실행' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

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
Write-Host ''

Write-Host '이 스크립트는 전체 데이터 처리 파이프라인을 실행합니다.' -ForegroundColor Yellow
Write-Host ''
Write-Host '[1단계] 웹 스크래핑 (Chrome)'
Write-Host '[2단계] JSONL 변환'
Write-Host '[3단계] 한국어 번역 (선택사항)'
Write-Host '[4단계] 데이터 검증'
Write-Host ''

$confirm = Read-Host '계속하시겠습니까? (Y/N)'
if ($confirm -ne 'Y' -and $confirm -ne 'y') {
    Write-Host '취소되었습니다.' -ForegroundColor Red
    exit 0
}

Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   [1/4] 웹 스크래핑' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

Write-Host '[1] Chinese Text Project 스크래핑'
Write-Host '[2] 위키문헌 스크래핑'
Write-Host '[3] 전체 스크래핑'
Write-Host '[4] 건너뛰기'
Write-Host ''

$scrapeChoice = Read-Host '선택 (번호)'

# Playwright 설치 확인
Write-Host ''
Write-Host 'Playwright 설치 확인 중...' -ForegroundColor Yellow
& $python -c "import playwright" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host '[설치] Playwright 설치 중...' -ForegroundColor Yellow
    & $python -m pip install playwright requests
    & $python -m playwright install chromium
}

switch ($scrapeChoice) {
    '1' { & $python (Join-Path $scriptDir 'scraper_ctext.py') }
    '2' { & $python (Join-Path $scriptDir 'scraper_wikisource.py') }
    '3' {
        & $python (Join-Path $scriptDir 'scraper_ctext.py')
        & $python (Join-Path $scriptDir 'scraper_wikisource.py')
    }
    '4' { Write-Host '건너뜁니다.' -ForegroundColor Gray }
    default { Write-Host '잘못된 선택입니다.' -ForegroundColor Red }
}

Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   [2/4] JSONL 변환' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

& $python (Join-Path $scriptDir 'convert_to_jsonl.py')

Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   [3/4] 한국어 번역' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

$translate = Read-Host '한국어 번역을 실행하시겠습니까? (Y/N)'
if ($translate -eq 'Y' -or $translate -eq 'y') {
    Write-Host ""
    Write-Host "[옵션] 번역 방법:" -ForegroundColor Cyan
    Write-Host "  1. Kimi K2.5 Cloud (추천)"
    Write-Host "  2. OpenAI API (GPT-4)"
    Write-Host "  3. OpenAI API (GPT-3.5)"
    Write-Host "  4. Ollama (로컬)"
    Write-Host ""
    Write-Host "[주의] Kimi API 키가 필요합니다." -ForegroundColor Red
    Write-Host "환경 변수 KIMI_API_KEY 또는 MOONSHOT_API_KEY를 설정하세요."
    Write-Host ""
    & $python (Join-Path $scriptDir 'translate_korean.py')
} else {
    Write-Host '건너뜁니다.' -ForegroundColor Gray
}

Write-Host ''
Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   [4/4] 데이터 검증' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

& $python (Join-Path $scriptDir 'validate_data.py')

Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host '   전체 파이프라인 완료!' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
Write-Host ''
Write-Host '결과 파일 위치:' -ForegroundColor Yellow
Write-Host '  - raw/          : 원문 텍스트'
Write-Host '  - processed/    : JSONL 데이터'
Write-Host '  - metadata/     : 메타데이터'
Write-Host ''

Read-Host '계속하려면 Enter를 누르세요'
