@echo off
chcp 65001 >nul
setlocal

set "PYTHON_CMD="
if exist ".venv\Scripts\python.exe" set "PYTHON_CMD=.venv\Scripts\python.exe"
if not defined PYTHON_CMD where py >nul 2>nul && set "PYTHON_CMD=py"
if not defined PYTHON_CMD where python >nul 2>nul && set "PYTHON_CMD=python"

echo.
echo ================================================
echo  World Monitor AI JSON sync loop
echo ================================================
echo.

if not defined PYTHON_CMD (
  echo [ERROR] Python executable not found.
  echo Checked: .venv\Scripts\python.exe, py, python
  pause
  exit /b 1
)

echo [INFO] Using Python: %PYTHON_CMD%
echo.

:loop
echo [%date% %time%] Generating world-monitor-ai.json...
%PYTHON_CMD% web\generate_world_monitor_ai.py
if errorlevel 1 (
  echo [%date% %time%] Generation failed. Retrying in 60 seconds...
  powershell -NoProfile -Command "Start-Sleep -Seconds 60"
  goto :loop
)
echo [%date% %time%] Waiting 600 seconds...
powershell -NoProfile -Command "Start-Sleep -Seconds 600"
goto :loop
