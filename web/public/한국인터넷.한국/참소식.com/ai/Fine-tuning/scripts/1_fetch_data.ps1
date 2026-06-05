# 고전 문헌 원문 수집

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   고전 문헌 원문 수집' -ForegroundColor Cyan
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

Write-Host '[1] Chinese Text Project 수집'
Write-Host '[2] 위키문헌 수집'
Write-Host '[3] Project Gutenberg 수집'
Write-Host '[4] 전체 수집'
Write-Host ''

$choice = Read-Host '선택 (번호)'

switch ($choice) {
    '1' { & $python (Join-Path $scriptDir 'fetch_ctext.py') }
    '2' { & $python (Join-Path $scriptDir 'fetch_wikisource.py') }
    '3' { & $python (Join-Path $scriptDir 'fetch_gutenberg.py') }
    '4' {
        & $python (Join-Path $scriptDir 'fetch_ctext.py')
        & $python (Join-Path $scriptDir 'fetch_wikisource.py')
        & $python (Join-Path $scriptDir 'fetch_gutenberg.py')
    }
    default { Write-Host '잘못된 선택입니다.' -ForegroundColor Red }
}

Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host '   수집 완료!' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
Read-Host '계속하려면 Enter를 누르세요'
