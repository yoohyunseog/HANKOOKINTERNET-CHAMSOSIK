@echo off
chcp 65001 >nul
title 로봇 뉴스 YouTube 모니터링

echo ========================================
echo   로봇 뉴스 YouTube 모니터링 시스템
echo ========================================
echo.

cd /d "%~dp0"

REM Python 가상환경 활성화
if exist "..\\.venv\\Scripts\\activate.bat" (
    call "..\\.venv\\Scripts\\activate.bat"
    echo [OK] Python 가상환경 활성화
) else (
    echo [WARN] 가상환경을 찾을 수 없습니다. 시스템 Python을 사용합니다.
)

echo.
echo [INFO] 로봇 뉴스 수집 시작...
echo [INFO] 키워드: 휴머노이드, 산업용 로봇, 서비스 로봇, 드론, 로봇 기술
echo.

python robot_news_monitor.py --max-videos 3 --keywords 5

echo.
echo ========================================
echo   로봇 뉴스 수집 완료
echo ========================================
echo.
echo 결과 파일: web\public\한국인터넷.한국\참소식.com\robot\news_data.json
echo.

pause