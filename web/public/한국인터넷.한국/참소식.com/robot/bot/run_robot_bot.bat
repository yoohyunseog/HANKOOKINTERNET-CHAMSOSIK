@echo off
chcp 65001 >nul
setlocal

pushd "%~dp0..\..\..\..\..\.." >nul
set "PROJECT_ROOT=%CD%"
popd >nul

set "BOT_DIR=%~dp0"
set "VENV_ACTIVATE=%PROJECT_ROOT%\.venv\Scripts\activate.bat"
set "LOCAL_NEWS_DATA=%BOT_DIR%..\news_data.json"
set "SERVER=root@211.45.162.155"
set "REMOTE_NEWS_DIR=/var/www/chamsosik/robot"
set "REMOTE_TMP_FILE=/tmp/chamsosik_robot_news_data.json"
set "WDM_LOCAL=1"
set "LAST_EXIT=0"

:loop
cls
echo.
echo ================================================================================
echo   Robotics news bot - auto repeat
echo ================================================================================
echo.
echo Start time: %date% %time%
echo Repeat interval: no wait
echo Stop: press Ctrl+C
echo.

echo [1/4] Activating virtual environment...
call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    set "LAST_EXIT=1"
    goto repeat_now
)
echo Virtual environment activated.

echo.
echo [2/4] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo Ollama is not running.
    echo Please start Ollama.
    set "LAST_EXIT=1"
    goto repeat_now
)
echo Ollama connected.

echo.
echo [3/4] Running news bot...
pushd "%BOT_DIR%"
python "news_bot.py"
set "LAST_EXIT=%ERRORLEVEL%"
popd
if not "%LAST_EXIT%"=="0" (
    echo News bot failed with exit code %LAST_EXIT%.
    goto repeat_now
)

echo.
echo [4/4] Uploading news_data.json to server...
if not exist "%LOCAL_NEWS_DATA%" (
    echo News data file not found: %LOCAL_NEWS_DATA%
    set "LAST_EXIT=1"
    goto repeat_now
)
ssh %SERVER% "sudo mkdir -p %REMOTE_NEWS_DIR%"
if errorlevel 1 (
    echo Failed to create remote news folder.
    set "LAST_EXIT=1"
    goto repeat_now
)
scp "%LOCAL_NEWS_DATA%" %SERVER%:%REMOTE_TMP_FILE%
if errorlevel 1 (
    echo Failed to upload news data file.
    set "LAST_EXIT=1"
    goto repeat_now
)
ssh %SERVER% "sudo mv %REMOTE_TMP_FILE% %REMOTE_NEWS_DIR%/news_data.json && sudo chmod 644 %REMOTE_NEWS_DIR%/news_data.json"
if errorlevel 1 (
    echo Failed to move news data file on server.
    set "LAST_EXIT=1"
    goto repeat_now
)
echo Server upload completed.

echo.
echo ================================================================================
echo   Run completed.
echo ================================================================================

:repeat_now
if "%RUN_ONCE%"=="1" exit /b 0
echo.
echo Restarting immediately...
goto loop
