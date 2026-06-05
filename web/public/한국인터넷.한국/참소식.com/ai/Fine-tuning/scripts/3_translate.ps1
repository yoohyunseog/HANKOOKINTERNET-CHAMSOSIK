# 한국어 번역

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   한국어 번역' -ForegroundColor Cyan
Write-Host '============================================' -ForegroundColor Cyan
Write-Host ''

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

Write-Host 'JSONL 데이터에 한국어 번역을 추가합니다.' -ForegroundColor Yellow
Write-Host ''
Write-Host '[옵션] 번역 방법:' -ForegroundColor Cyan
Write-Host '  1. Kimi K2.5 Cloud (추천)'
Write-Host '  2. OpenAI API (GPT-4)'
Write-Host '  3. OpenAI API (GPT-3.5)'
Write-Host '  4. Ollama (로컬)'
Write-Host ''
Write-Host '[주의] Kimi API 키가 필요합니다.' -ForegroundColor Red
Write-Host '환경 변수 KIMI_API_KEY 또는 MOONSHOT_API_KEY를 설정하세요.'
Write-Host ''

& $python (Join-Path $scriptDir 'translate_korean.py')

Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host '   번역 완료!' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
Read-Host '계속하려면 Enter를 누르세요'
