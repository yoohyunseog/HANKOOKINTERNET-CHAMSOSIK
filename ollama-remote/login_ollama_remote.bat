@echo off
chcp 65001 >nul
setlocal enableextensions

echo.
echo ================================================================
echo          Ollama 클라우드 모델 로그인 - 원격 서버
echo ================================================================
echo.

set "REMOTE_HOST=root@211.45.162.155"

echo 클라우드 모델(glm-5:cloud, gemma4:31b-cloud) 사용을 위한 로그인
echo.
echo 로그인 URL이 생성되면 브라우저에서 열어 Google/GitHub로 로그인하세요.
echo.

echo [로그인 URL 생성 중...]
echo.

ssh -t %REMOTE_HOST% "ollama login"

echo.
echo ================================================================
echo   로그인 완료!
echo   이제 클라우드 모델을 사용할 수 있습니다.
echo ================================================================
echo.

endlocal
pause