# 데이터 검증

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   데이터 검증' -ForegroundColor Cyan
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

Write-Host 'JSONL 데이터를 검증합니다...' -ForegroundColor Yellow
Write-Host ''

& $python (Join-Path $scriptDir 'validate_data.py')

Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host '   검증 완료!' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
Read-Host '계속하려면 Enter를 누르세요'
