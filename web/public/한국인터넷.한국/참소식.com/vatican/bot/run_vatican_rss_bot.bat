@echo off
chcp 65001 >nul
setlocal

pushd "%~dp0..\..\..\..\..\.." >nul
set "PROJECT_ROOT=%CD%"
popd >nul

set "BOT_DIR=%~dp0"
set "VENV_ACTIVATE=%PROJECT_ROOT%\.venv\Scripts\activate.bat"
set "OLLAMA_HOST=http://211.45.162.155:11434"
set "OLLAMA_MODEL=kimi-k2.5:cloud"
set "LAST_EXIT=0"

:loop
cls
echo.
echo ================================================================================
echo   Vatican News RSS Bot - RSS 피드 수집 및 AI 번역
echo ================================================================================
echo.
echo Start time: %date% %time%
echo Ollama Server: %OLLAMA_HOST%
echo Model: %OLLAMA_MODEL%
echo Stop: press Ctrl+C
echo.

echo [1/3] Activating virtual environment...
call "%VENV_ACTIVATE%"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    set "LAST_EXIT=1"
    goto repeat_now
)
echo Virtual environment activated.

echo.
echo [2/3] Checking Server Ollama...
curl -s %OLLAMA_HOST%/api/tags >nul 2>&1
if errorlevel 1 (
    echo Server Ollama not reachable. Translation will be skipped.
) else (
    echo Server Ollama connected: %OLLAMA_HOST%
)

echo.
echo [3/3] Running Vatican RSS Bot...
pushd "%BOT_DIR%"
set "OLLAMA_HOST=%OLLAMA_HOST%"
set "OLLAMA_MODEL=%OLLAMA_MODEL%"
python "vatican_rss_bot.py"
set "LAST_EXIT=%ERRORLEVEL%"
popd

if not "%LAST_EXIT%"=="0" (
    echo RSS bot failed with exit code %LAST_EXIT%.
    goto repeat_now
)

echo.
echo ================================================================================
echo   Run completed successfully.
echo ================================================================================

:repeat_now
if "%RUN_ONCE%"=="1" exit /b 0
echo.
echo Restarting in 30 minutes...
timeout /t 1800 /nobreak >nul
goto loop