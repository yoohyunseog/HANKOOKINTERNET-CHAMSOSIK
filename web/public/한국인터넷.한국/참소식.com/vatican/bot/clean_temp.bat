@echo off
chcp 65001 >nul
echo ========================================
echo   Temp 폴더 안전 정리 도구
echo ========================================
echo.

set "TEMP_DIR=C:\Users\dbghw\AppData\Local\Temp"

echo [정리 대상] %TEMP_DIR%
echo.
echo [주의] 이 작업은 되돌릴 수 없습니다.
echo.

REM 현재 Temp 폴더 크기 확인
echo [1/4] Temp 폴더 크기 확인 중...
for /f "tokens=3" %%a in ('dir /s /-c "%TEMP_DIR%" 2^>nul ^| findstr /i "파일"') do set "temp_size=%%a"
echo     현재 크기: %temp_size% 바이트
echo.

REM 삭제 전 확인
echo [2/4] 삭제할 파일 목록 확인 중...
echo     다음 유형의 파일들이 삭제됩니다:
echo     - 임시 파일 (*.tmp, *.temp)
echo     - 로그 파일 (*.log)
echo     - 캐시 파일 (*.cache)
echo     - 브라우저 임시 파일
echo     - 기타 임시 데이터
echo.

set /p confirm="계속하시겠습니까? (Y/N): "
if /i not "%confirm%"=="Y" (
    echo.
    echo [취소] 작업이 취소되었습니다.
    pause
    exit /b 0
)

echo.
echo [3/4] Temp 폴더 정리 중...
echo.

REM 안전하게 삭제할 파일 패턴
echo     - TMP 파일 삭제 중...
del /f /s /q "%TEMP_DIR%\*.tmp" 2>nul
del /f /s /q "%TEMP_DIR%\*.temp" 2>nul

echo     - LOG 파일 삭제 중...
del /f /s /q "%TEMP_DIR%\*.log" 2>nul

echo     - CACHE 파일 삭제 중...
del /f /s /q "%TEMP_DIR%\*.cache" 2>nul

echo     - 임시 폴더 정리 중...
for /d %%d in ("%TEMP_DIR%\*") do (
    if /i not "%%~nxd"=="Microsoft" (
        if /i not "%%~nxd"=="Google" (
            if /i not "%%~nxd"=="Mozilla" (
                if /i not "%%~nxd"=="Adobe" (
                    rd /s /q "%%d" 2>nul
                )
            )
        )
    )
)

echo     - 빈 폴더 정리 중...
for /f "delims=" %%d in ('dir /ad /b /s "%TEMP_DIR%" 2^>nul ^| sort /r') do (
    rd "%%d" 2>nul
)

echo.
echo [4/4] 정리 완료!
echo.

REM 정리 후 크기 확인
for /f "tokens=3" %%a in ('dir /s /-c "%TEMP_DIR%" 2^>nul ^| findstr /i "파일"') do set "new_size=%%a"
echo     정리 전: %temp_size% 바이트
echo     정리 후: %new_size% 바이트

echo.
echo ========================================
echo   Temp 폴더 정리 완료
echo ========================================
echo.
echo [참고] 일부 파일은 사용 중이라 삭제되지 않을 수 있습니다.
echo [참고] Microsoft, Google, Mozilla, Adobe 폴더는 보호됩니다.
echo.

pause