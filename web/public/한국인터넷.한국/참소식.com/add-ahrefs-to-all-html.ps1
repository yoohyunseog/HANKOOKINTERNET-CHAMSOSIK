# Ahrefs Analytics 스크립트를 모든 HTML 파일에 추가하는 스크립트
# 실행 방법: .\add-ahrefs-to-all-html.ps1

$rootPath = "E:\Ai project\사이트\web\public\한국인터넷.한국"
$scriptTag = '<script src="./js/ahrefs-analytics.js"></script>'

# 이미 스크립트가 있는지 확인하는 함수
function HasAhrefsScript {
    param($content)
    return $content -match 'ahrefs-analytics\.js' -or $content -match 'analytics\.ahrefs\.com'
}

# HTML 파일 찾기
$htmlFiles = Get-ChildItem -Path $rootPath -Filter "*.html" -Recurse -File

$count = 0
$skipped = 0
$errors = 0

Write-Host "총 $($htmlFiles.Count)개의 HTML 파일을 검사합니다..." -ForegroundColor Cyan

foreach ($file in $htmlFiles) {
    try {
        $content = Get-Content -Path $file.FullName -Raw -Encoding UTF8
        
        # 이미 스크립트가 있으면 건너뜀
        if (HasAhrefsScript -content $content) {
            $skipped++
            Write-Host "건너뜀 (이미 있음): $($file.Name)" -ForegroundColor Yellow
            continue
        }
        
        # </head> 또는 </body> 앞에 추가
        if ($content -match '</head>') {
            $newContent = $content -replace '</head>', "`t$scriptTag`n</head>"
        } elseif ($content -match '</body>') {
            $newContent = $content -replace '</body>', "`t$scriptTag`n</body>"
        } else {
            # head나 body가 없으면 파일 끝에 추가
            $newContent = $content + "`n$scriptTag`n"
        }
        
        # 파일 저장
        Set-Content -Path $file.FullName -Value $newContent -Encoding UTF8 -NoNewline
        $count++
        Write-Host "추가됨: $($file.Name)" -ForegroundColor Green
        
    } catch {
        $errors++
        Write-Host "오류: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n완료!" -ForegroundColor Cyan
Write-Host "추가됨: $count" -ForegroundColor Green
Write-Host "건너뜀: $skipped" -ForegroundColor Yellow
Write-Host "오류: $errors" -ForegroundColor Red