@echo off
chcp 65001 >nul
setlocal

pushd "%~dp0.." >nul
set "ROBOT_DIR=%CD%"
popd >nul

set "SERVER_USER=root"
set "SERVER_HOST=211.45.162.155"
set "SERVER_PATH=/var/www/chamsosik/robot"

echo.
echo ================================================================================
echo   Upload robot folder to web server
echo ================================================================================
echo.
echo Local:  %ROBOT_DIR%
echo Remote: %SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%
echo.

echo [1/3] Checking required files...
if not exist "%ROBOT_DIR%\index.html" (
    echo ERROR: index.html was not found.
    pause
    exit /b 1
)

if not exist "%ROBOT_DIR%\news_data.json" (
    echo WARNING: news_data.json was not found. The site may load without news data.
)

if "%DRY_RUN%"=="1" (
    echo DRY_RUN=1, skipping remote connection and upload.
    echo.
    echo Would upload:
    echo   %ROBOT_DIR%\index.html
    if exist "%ROBOT_DIR%\news_data.json" echo   %ROBOT_DIR%\news_data.json
    if exist "%ROBOT_DIR%\bot\news_bot.py" echo   %ROBOT_DIR%\bot\news_bot.py
    if exist "%ROBOT_DIR%\bot\run_robot_bot.bat" echo   %ROBOT_DIR%\bot\run_robot_bot.bat
    exit /b 0
)

echo [2/3] Preparing remote directory...
ssh "%SERVER_USER%@%SERVER_HOST%" "sudo mkdir -p '%SERVER_PATH%' '%SERVER_PATH%/bot'"
if errorlevel 1 (
    echo ERROR: Could not prepare the remote directory.
    pause
    exit /b 1
)

echo [3/3] Uploading files...
echo.

where rsync >nul 2>&1
if %errorlevel% equ 0 (
    echo Using rsync...
    rsync -avz ^
        --exclude ".wdm/" ^
        --exclude "__pycache__/" ^
        --exclude "*.pyc" ^
        --exclude "*.exe" ^
        --exclude "*.zip" ^
        "%ROBOT_DIR%/" "%SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/"
) else (
    echo Using scp...

    echo Uploading root files...
    for %%f in ("%ROBOT_DIR%\*.html" "%ROBOT_DIR%\*.css" "%ROBOT_DIR%\*.js" "%ROBOT_DIR%\*.json" "%ROBOT_DIR%\*.md" "%ROBOT_DIR%\*.png" "%ROBOT_DIR%\*.jpg" "%ROBOT_DIR%\*.jpeg" "%ROBOT_DIR%\*.gif" "%ROBOT_DIR%\*.webp" "%ROBOT_DIR%\*.svg") do (
        if exist "%%f" (
            echo   %%~nxf
            scp "%%f" "%SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/"
            if errorlevel 1 goto upload_failed
        )
    )

    if exist "%ROBOT_DIR%\bot" (
        echo Uploading bot files...
        for %%f in ("%ROBOT_DIR%\bot\*.py" "%ROBOT_DIR%\bot\*.bat" "%ROBOT_DIR%\bot\*.json" "%ROBOT_DIR%\bot\*.md") do (
            if exist "%%f" (
                echo   bot/%%~nxf
                scp "%%f" "%SERVER_USER%@%SERVER_HOST%:%SERVER_PATH%/bot/"
                if errorlevel 1 goto upload_failed
            )
        )
    )
)

if errorlevel 1 goto upload_failed

echo.
echo ================================================================================
echo   Upload complete
echo ================================================================================
echo Remote path: %SERVER_PATH%
echo URL: http://211.45.162.155/robot/
echo.
pause
exit /b 0

:upload_failed
echo.
echo ERROR: Upload failed.
pause
exit /b 1
