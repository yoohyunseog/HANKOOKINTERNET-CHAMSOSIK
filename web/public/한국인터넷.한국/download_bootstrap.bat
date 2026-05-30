@echo off
chcp 65001 >nul
echo Bootstrap 5.3.0 파일 다운로드 중...

set FOLDER=assets\bootstrap\5.3.0

if not exist "%FOLDER%\css" mkdir "%FOLDER%\css"
if not exist "%FOLDER%\js" mkdir "%FOLDER%\js"

echo CSS 파일 다운로드...
curl -L -o "%FOLDER%\css\bootstrap.min.css" https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/css/bootstrap.min.css

echo JS 파일 다운로드...
curl -L -o "%FOLDER%\js\bootstrap.bundle.min.js" https://cdnjs.cloudflare.com/ajax/libs/bootstrap/5.3.0/js/bootstrap.bundle.min.js

echo.
echo 다운로드 완료!
echo 파일 위치: %FOLDER%
pause