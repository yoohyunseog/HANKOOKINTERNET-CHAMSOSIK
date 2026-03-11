@echo off
setlocal

:loop
echo [%date% %time%] ====== finance_crawler 루프 시작 ======
call "run_finance_crawler.bat"
if errorlevel 1 echo [%date% %time%] run_finance_crawler.bat 오류 발생 (무시하고 계속)
call "upload_finance_data.bat"
if errorlevel 1 echo [%date% %time%] upload_finance_data.bat 오류 발생 (무시하고 계속)
echo [%date% %time%] ====== 10분 대기 후 반복 ======
timeout /t 600 /nobreak >nul
goto loop

endlocal
