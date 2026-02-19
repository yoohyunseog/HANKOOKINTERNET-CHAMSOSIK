@echo off
chcp 65001 > nul
echo ======================================================
echo   네이버 크리에이터 트렌드 분석기 실행
echo ======================================================
echo.

cd /d "%~dp0"

REM Python 버전 확인
echo [1/3] Python 확인 중...
py --version
if errorlevel 1 (
    echo ❌ Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python을 설치해주세요.
    pause
    exit /b 1
)

REM 패키지 설치 (가상환경 없이 직접 설치)
echo [2/3] 필요한 패키지 설치 중...
py -m pip install --upgrade pip --quiet
py -m pip install -r 8BIT\requirements_naver_creator.txt --quiet

echo.
echo ✅ 준비 완료
echo.

REM 프로그램 실행
echo [3/3] 프로그램 실행...
py 8BIT\naver_creator_trend_analyzer.py

pause
