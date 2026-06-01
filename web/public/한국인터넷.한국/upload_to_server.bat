@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo 한국인터넷.한국 폴더 업로드 스크립트
echo 참소식.com 폴더 제외
echo ========================================

set LOCAL_PATH=E:\Ai project\사이트\web\public\한국인터넷.한국
set REMOTE_SERVER=root@211.45.162.155
set REMOTE_PATH=/var/www/한국인터넷.한국

echo.
echo 업로드 시작: %date% %time%
echo.

REM .git 폴더와 참소식.com 폴더를 제외하고 업로드
echo 파일 및 폴더 업로드 중...
echo.

REM 현재 폴더의 파일들 업로드 (.gitignore 제외)
scp -r "%LOCAL_PATH%\ads.txt" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\calculator.html" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\data-crawler.html" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\domain-check.js" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\domain-report.html" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\icnn-history.html" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\index.html" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\quest-board.html" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\script.js" %REMOTE_SERVER%:%REMOTE_PATH%/
scp -r "%LOCAL_PATH%\style.css" %REMOTE_SERVER%:%REMOTE_PATH%/

echo.
echo 하위 폴더 업로드 중...
echo.

REM assets 폴더 업로드
echo [assets 폴더 업로드]
scp -r "%LOCAL_PATH%\assets" %REMOTE_SERVER%:%REMOTE_PATH%/

REM GAME 폴더 업로드
echo [GAME 폴더 업로드]
scp -r "%LOCAL_PATH%\GAME" %REMOTE_SERVER%:%REMOTE_PATH%/

REM 미분적분 폴더 업로드
echo [미분적분 폴더 업로드]
scp -r "%LOCAL_PATH%\미분적분" %REMOTE_SERVER%:%REMOTE_PATH%/

REM 보이니치 폴더 업로드
echo [보이니치 폴더 업로드]
scp -r "%LOCAL_PATH%\보이니치" %REMOTE_SERVER%:%REMOTE_PATH%/

echo.
echo 서버에서 .zip 파일 삭제 중...
ssh %REMOTE_SERVER% "find %REMOTE_PATH% -name '*.zip' -type f -delete"
echo .zip 파일 삭제 완료

echo.
echo ========================================
echo 업로드 완료: %date% %time%
echo ========================================
echo.
echo 제외된 항목:
echo   - .git 폴더
echo   - .gitignore
echo   - 참소식.com 폴더
echo   - 모든 .zip 파일 (*.zip)
echo   - upload_to_server.bat
echo   - download_bootstrap.bat
echo.
pause