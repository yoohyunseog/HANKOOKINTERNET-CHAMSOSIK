@echo off
chcp 65001 >nul
cls

echo.
echo ╔════════════════════════════════════════════════════╗
echo ║  🚀 AI 수익형 트렌드 콘텐츠 생성 시스템           ║
echo ╚════════════════════════════════════════════════════╝
echo.

echo 📋 옵션:
echo.
echo   1. 트렌드 분석 (기존 데이터 사용)
echo   2. 다운로드 필요한 패키지
echo   3. 종료
echo.

set /p choice="선택 (1-3): "

if "%choice%"=="1" (
    echo.
    echo [1/2] 트렌드 데이터 확인 중...
    if exist "data\naver_creator_trends\latest_trend_data.json" (
        echo ✅ 트렌드 데이터 발견
    ) else (
        echo ⚠️  트렌드 데이터 없음!
        echo 먼저 실행하세요: run_naver_creator_analyzer.bat
        pause
        exit /b
    )
    
    echo.
    echo [2/2] 수익형 콘텐츠 생성 중...
    py -m pip install beautifulsoup4 requests -q
    py 8BIT\trend_to_revenue_ai.py
    
    echo.
    echo 📂 결과 확인: data\revenue_content\
    pause
    
) else if "%choice%"=="2" (
    echo.
    echo 📦 필수 패키지 설치 중...
    py -m pip install beautifulsoup4 requests -q
    echo ✅ 설치 완료
    pause
    
) else if "%choice%"=="3" (
    exit /b
) else (
    echo ❌ 잘못된 선택
    pause
)
