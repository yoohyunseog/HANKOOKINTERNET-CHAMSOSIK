@echo off
chcp 65001 >nul
echo ========================================
echo   최신 기사 요약 AI 실행
echo ========================================
echo.

cd /d "%~dp0"

REM 가상환경 활성화
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] 가상환경 활성화
) else (
    echo [INFO] 가상환경 없이 실행
)

echo.
echo [실행 옵션]
echo 1. 기본 실행 (사이트당 3개 기사)
echo 2. 많은 기사 (사이트당 5개)
echo 3. AI 요약 없이 (빠른 실행)
echo 4. 커스텀 URL 지정
echo.

set /p choice="선택하세요 (1-4): "

if "%choice%"=="1" (
    echo.
    echo [실행] 기본 모드...
    python 8BIT\article_summarizer.py --max 3
)
if "%choice%"=="2" (
    echo.
    echo [실행] 많은 기사 모드...
    python 8BIT\article_summarizer.py --max 5
)
if "%choice%"=="3" (
    echo.
    echo [실행] AI 없이 빠른 모드...
    python 8BIT\article_summarizer.py --max 3 --no-ai
)
if "%choice%"=="4" (
    echo.
    set /p urls="URL들을 입력하세요 (공백으로 구분): "
    echo.
    echo [실행] 커스텀 URL 모드...
    python 8BIT\article_summarizer.py --urls %urls%
)

echo.
echo ========================================
echo   완료! 결과는 data\article_summaries\ 폴더에 저장됩니다.
echo ========================================
pause