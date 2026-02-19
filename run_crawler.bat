@echo off
echo =====================================
echo 웹 크롤러 설치 및 실행
echo =====================================
echo.

REM 가상환경 활성화
echo [1/4] 가상환경 활성화...
call .venv\Scripts\activate
if errorlevel 1 (
    echo 오류: 가상환경이 없습니다.
    echo python -m venv .venv 를 먼저 실행하세요.
    pause
    exit /b 1
)

REM 패키지 설치
echo.
echo [2/4] 크롤러 패키지 설치 중... (시간이 걸릴 수 있습니다)
pip install -r 8BIT\requirements_crawler.txt
if errorlevel 1 (
    echo 오류: 패키지 설치 실패
    pause
    exit /b 1
)

REM 테스트 실행
echo.
echo [3/4] 크롤러 테스트 실행...
python 8BIT\test_crawler.py
if errorlevel 1 (
    echo 오류: 크롤러 실행 실패
    pause
    exit /b 1
)

REM 완료
echo.
echo [4/4] 완료!
echo.
echo 수집된 데이터: data\test_crawled_data.json
echo.
pause
