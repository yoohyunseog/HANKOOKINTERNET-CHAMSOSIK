@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 한국인터넷.한국 폴더 업로드 (참소식.com 제외)
echo ========================================

set "SERVER=root@211.45.162.155"
set "REMOTE_DIR=/root/web/public/한국인터넷.한국"
set "LOCAL_DIR=E:\Ai project\사이트\web\public\한국인터넷.한국"

echo [1/5] 서버 디렉터리 생성...
ssh %SERVER% "mkdir -p '%REMOTE_DIR%'"

echo [2/5] 메인 파일 업로드...
scp "%LOCAL_DIR%\index.html" %SERVER%:%REMOTE_DIR%/
scp "%LOCAL_DIR%\calculator.html" %SERVER%:%REMOTE_DIR%/
scp "%LOCAL_DIR%\database.html" %SERVER%:%REMOTE_DIR%/ 2>nul
scp "%LOCAL_DIR%\data-crawler.html" %SERVER%:%REMOTE_DIR%/
scp "%LOCAL_DIR%\domain-report.html" %SERVER%:%REMOTE_DIR%/
scp "%LOCAL_DIR%\icnn-history.html" %SERVER%:%REMOTE_DIR%/ 2>nul
scp "%LOCAL_DIR%\quest-board.html" %SERVER%:%REMOTE_DIR%/ 2>nul
scp "%LOCAL_DIR%\domain-check.js" %SERVER%:%REMOTE_DIR%/
scp "%LOCAL_DIR%\script.js" %SERVER%:%REMOTE_DIR%/
scp "%LOCAL_DIR%\style.css" %SERVER%:%REMOTE_DIR%/
scp "%LOCAL_DIR%\ads.txt" %SERVER%:%REMOTE_DIR%/
scp "%LOCAL_DIR%\.gitignore" %SERVER%:%REMOTE_DIR%/ 2>nul

echo [3/5] assets 폴더 업로드...
ssh %SERVER% "mkdir -p '%REMOTE_DIR%/assets'"
scp -r "%LOCAL_DIR%\assets"/* %SERVER%:%REMOTE_DIR%/assets/

echo [4/5] GAME 폴더 업로드...
ssh %SERVER% "mkdir -p '%REMOTE_DIR%/GAME'"
scp -r "%LOCAL_DIR%\GAME"/* %SERVER%:%REMOTE_DIR%/GAME/

echo [5/5] 미분적분, 보이니치 폴더 업로드...
ssh %SERVER% "mkdir -p '%REMOTE_DIR%/미분적분'"
scp -r "%LOCAL_DIR%\미분적분"/* %SERVER%:%REMOTE_DIR%/미분적분/ 2>nul

ssh %SERVER% "mkdir -p '%REMOTE_DIR%/보이니치'"
scp -r "%LOCAL_DIR%\보이니치"/* %SERVER%:%REMOTE_DIR%/보이니치/ 2>nul

echo ========================================
echo 업로드 완료!
echo ========================================
echo.
echo 제외됨: 참소식.com 폴더, .git 폴더
echo.
pause
endlocal