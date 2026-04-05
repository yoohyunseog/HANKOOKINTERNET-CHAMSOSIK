@echo off
setlocal

set "SERVER=root@211.45.162.155"
set "REMOTE_ROOT=/var/www/chamsosik"
set "REMOTE_TMP_DIR=/tmp/chamsosik_ai_upload"
set "LOCAL_FILE=%~dp0web\public\world-monitor-ai.json"
set "SSH_COMMON_OPTS=-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=10"

if not exist "%LOCAL_FILE%" (
  echo [ERROR] Local file not found: %LOCAL_FILE%
  exit /b 1
)

echo [1/3] Ensure remote folder exists...
ssh -n %SSH_COMMON_OPTS% %SERVER% "sudo mkdir -p %REMOTE_ROOT% && mkdir -p %REMOTE_TMP_DIR%"
if errorlevel 1 (
  echo [ERROR] Failed to prepare remote directories.
  exit /b 1
)

echo [2/3] Upload world-monitor-ai.json only...
scp -B %SSH_COMMON_OPTS% "%LOCAL_FILE%" %SERVER%:%REMOTE_TMP_DIR%/
if errorlevel 1 (
  echo [ERROR] Failed to upload world-monitor-ai.json.
  exit /b 1
)

echo [3/3] Move file to final location...
ssh -n %SSH_COMMON_OPTS% %SERVER% "sudo mv %REMOTE_TMP_DIR%/world-monitor-ai.json %REMOTE_ROOT%/world-monitor-ai.json && rmdir %REMOTE_TMP_DIR% 2>/dev/null || true"
if errorlevel 1 (
  echo [ERROR] Failed to move uploaded file into place.
  exit /b 1
)

echo [DONE] Uploaded %LOCAL_FILE%
endlocal
