@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "REPO_DIR=%~dp0"
set "REMOTE_NAME=origin"
set "REMOTE_URL=https://github.com/yoohyunseog/HANKOOKINTERNET-CHAMSOSIK.git"

echo ========================================
echo GitHub upload helper
echo ========================================
echo.

cd /d "%REPO_DIR%"
if errorlevel 1 (
  echo [ERROR] Could not enter repo folder: %REPO_DIR%
  pause
  exit /b 1
)

if not exist ".git" (
  echo [ERROR] This folder is not a Git repository: %CD%
  pause
  exit /b 1
)

echo [1/6] Checking current branch...
for /f "usebackq delims=" %%B in (`git branch --show-current`) do set "BRANCH=%%B"
if not defined BRANCH (
  echo [ERROR] Could not detect current branch.
  pause
  exit /b 1
)
echo Branch: %BRANCH%
echo.

echo [2/6] Checking remote...
git remote get-url %REMOTE_NAME% >nul 2>nul
if errorlevel 1 (
  echo Adding remote %REMOTE_NAME%...
  git remote add %REMOTE_NAME% "%REMOTE_URL%"
  if errorlevel 1 (
    echo [ERROR] Failed to add remote.
    pause
    exit /b 1
  )
)
git remote -v
echo.

echo [3/6] Current status:
echo Skipping full status listing because this repository has many files.
echo.

echo [4/6] Staging all repository changes...
if exist ".git\index.lock" (
  tasklist /FI "IMAGENAME eq git.exe" 2>nul | find /I "git.exe" >nul
  if errorlevel 1 (
    echo Removing stale Git index lock...
    del /f ".git\index.lock" >nul 2>nul
    if exist ".git\index.lock" (
      echo [ERROR] Could not remove .git\index.lock.
      echo Close Git tools or run this script as administrator.
      pause
      exit /b 1
    )
  ) else (
    echo [ERROR] Git index is locked: .git\index.lock
    echo Close other Git tools first, then run this script again.
    pause
    exit /b 1
  )
)

echo Running: git add -A -- .
echo This includes all subfolders unless a file is ignored by .gitignore.
git add -A -- .
if errorlevel 1 (
  echo [ERROR] git add failed.
  pause
  exit /b 1
)
echo.

echo Staging complete.
echo.

choice /C YN /N /M "Commit and push these staged files? [Y/N] "
if errorlevel 2 (
  echo Cancelled. Staged changes are still staged; run "git restore --staged ." to unstage them if needed.
  pause
  exit /b 1
)

set "COMMIT_MSG=%~1"
if not defined COMMIT_MSG (
  for /f "usebackq delims=" %%T in (`powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm:ss'"`) do set "NOW=%%T"
  set "COMMIT_MSG=Update: !NOW!"
)

echo [5/6] Creating commit...
echo Commit message: %COMMIT_MSG%
git commit -m "%COMMIT_MSG%"
if errorlevel 1 (
  echo [ERROR] git commit failed.
  echo If Git says there is nothing to commit, there were no staged changes.
  pause
  exit /b 1
)
echo.

echo [6/6] Pushing to GitHub...
git push -u %REMOTE_NAME% %BRANCH%
if errorlevel 1 (
  echo.
  echo [ERROR] Upload failed.
  echo Check GitHub authentication, network, or remote branch permissions.
  pause
  exit /b 1
)

echo.
echo Done. Uploaded to GitHub.
echo Repository: %REMOTE_URL%
echo Branch: %BRANCH%
pause
exit /b 0
