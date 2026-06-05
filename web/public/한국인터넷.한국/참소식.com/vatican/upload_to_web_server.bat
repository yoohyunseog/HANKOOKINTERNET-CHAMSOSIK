@echo off
setlocal

set "VATICAN_DIR=%~dp0"
set "VATICAN_DIR=%VATICAN_DIR:~0,-1%"

set "SERVER_USER=root"
set "SERVER_HOST=211.45.162.155"
set "SERVER_PATH=/var/www/chamsosik/vatican"

echo.
echo ================================================================================
echo   Upload Vatican folder to web server (skip exe, zip)
echo ================================================================================
echo.
echo Local:  %VATICAN_DIR%
echo Remote: %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%
echo.

echo [1/3] Checking required files...
if not exist "%VATICAN_DIR%\index.html" (
    echo ERROR: index.html was not found.
    pause
    exit /b 1
)

echo [2/3] Preparing remote directory...
ssh "%SERVER_USER%@%SERVER_HOST%" "mkdir -p '%SERVER_PATH%'"
if errorlevel 1 (
    echo ERROR: Could not prepare the remote directory.
    pause
    exit /b 1
)

echo [3/3] Uploading files (excluding exe, zip)...
echo.

REM Check if rsync is available
where rsync >nul 2>&1
if %errorlevel% equ 0 (
    echo Using rsync...
    rsync -avz --exclude "*.exe" --exclude "*.zip" "%VATICAN_DIR%/" "%SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/"
) else (
    echo Using scp...
    
    REM Create bot directory on server
    ssh "%SERVER_USER%@%SERVER_HOST%" "mkdir -p '%SERVER_PATH%/bot'"
    
    REM Upload root files
    echo Uploading root files...
    for %%f in ("%VATICAN_DIR%\*.html" "%VATICAN_DIR%\*.css" "%VATICAN_DIR%\*.js" "%VATICAN_DIR%\*.json" "%VATICAN_DIR%\*.md" "%VATICAN_DIR%\*.png" "%VATICAN_DIR%\*.jpg" "%VATICAN_DIR%\*.gif") do (
        if exist "%%f" (
            echo   %%~nxf
            scp "%%f" "%SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/" 2>nul
        )
    )
    
    REM Upload bot folder files (excluding exe, zip)
    echo Uploading bot files...
    for %%f in ("%VATICAN_DIR%\bot\*.py" "%VATICAN_DIR%\bot\*.bat" "%VATICAN_DIR%\bot\*.json" "%VATICAN_DIR%\bot\*.md") do (
        if exist "%%f" (
            echo   bot/%%~nxf
            scp "%%f" "%SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/bot/" 2>nul
        )
    )
)

if errorlevel 1 (
    echo ERROR: Upload failed.
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo   Upload complete
echo ================================================================================
echo Remote path: %SERVER_PATH%
echo URL: http://211.45.162.155/vatican/
echo.
pause