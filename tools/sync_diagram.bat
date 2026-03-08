@echo off
setlocal

REM Use UTF-8 so Korean folder names are handled correctly.
chcp 65001 >nul

set "SERVER=root@211.45.162.155"
set "REMOTE_ROOT=/var/www/chamsosik"
set "LOCAL_DIR=E:\Ai project\사이트\web\public\한국인터넷.한국\참소식.com"
set "DIAGRAM_FILE=website_diagram.mmd"

if not exist "%LOCAL_DIR%\%DIAGRAM_FILE%" (
  echo [ERROR] 다이어그램 파일을 찾을 수 없습니다: %LOCAL_DIR%\%DIAGRAM_FILE%
  echo.
  echo 먼저 다이어그램을 생성하세요: tools\run_website_diagram.bat
  exit /b 1
)

echo ========================================
echo 📤 다이어그램 파일 업로드
echo ========================================
echo.
echo 파일: %DIAGRAM_FILE%
echo 대상: %SERVER%:%REMOTE_ROOT%
echo.

echo [1/2] 서버에 파일 업로드 중...
scp "%LOCAL_DIR%\%DIAGRAM_FILE%" %SERVER%:/tmp/%DIAGRAM_FILE%

if %ERRORLEVEL% NEQ 0 (
    echo ❌ 파일 업로드 실패
    exit /b 1
)

echo [2/2] 최종 위치로 이동 중...
ssh %SERVER% "sudo mv /tmp/%DIAGRAM_FILE% %REMOTE_ROOT%/%DIAGRAM_FILE% && sudo chmod 644 %REMOTE_ROOT%/%DIAGRAM_FILE%"

if %ERRORLEVEL% NEQ 0 (
    echo ❌ 파일 이동 실패
    exit /b 1
)

echo.
echo ========================================
echo ✅ 업로드 완료!
echo ========================================
echo.

endlocal
