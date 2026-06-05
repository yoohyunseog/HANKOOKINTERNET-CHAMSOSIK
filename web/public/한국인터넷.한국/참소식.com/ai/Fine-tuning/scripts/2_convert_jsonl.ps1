# 원문 변환 JSONL

$OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$baseDir = Split-Path -Parent $scriptDir

Write-Host '============================================' -ForegroundColor Cyan
Write-Host '   원문 변환 JSONL' -ForegroundColor Cyan
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

Write-Host '원문 텍스트를 JSONL 형식으로 변환합니다...' -ForegroundColor Yellow
Write-Host ''

& $python (Join-Path $scriptDir 'convert_to_jsonl.py')

Write-Host ''
Write-Host '============================================' -ForegroundColor Green
Write-Host '   변환 완료!' -ForegroundColor Green
Write-Host '============================================' -ForegroundColor Green
Read-Host '계속하려면 Enter를 누르세요'
