@echo off
REM Chainlink 데이터 추출 자동 실행 스크립트 (가상환경 포함)

REM 1. 가상환경 경로 설정 (필요시 수정)

REM 2. 가상환경 활성화 (실제 경로로 수정)
call "E:\python_env\Scripts\activate.bat"


REM 4. 크롬 드라이버가 PATH에 없으면 경로 지정 필요
REM set PATH=%PATH%;C:\chromedriver

REM 5. 데이터 추출 파이썬 스크립트 실행
python "%~dp0extract_chamsosik_data.py"

REM 6. 추출 데이터 정제 스크립트 실행
python "%~dp0clean_chainlink_data.py"
pause
