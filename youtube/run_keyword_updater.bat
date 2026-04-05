@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_EXE="
if exist "%~dp0..\.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
if not defined PYTHON_EXE if exist "%~dp0.venv\Scripts\python.exe" set "PYTHON_EXE=%~dp0.venv\Scripts\python.exe"
if not defined PYTHON_EXE set "PYTHON_EXE=C:\Windows\py.exe"

echo ===============================================
echo YouTube Monitor Keyword Updater
echo ===============================================
echo.

"%PYTHON_EXE%" "%~dp0update_monitor_keywords.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [ERROR] Keyword update failed. Exit code: %EXIT_CODE%
    exit /b %EXIT_CODE%
)

echo.
echo [DONE] monitor_keywords.txt updated
