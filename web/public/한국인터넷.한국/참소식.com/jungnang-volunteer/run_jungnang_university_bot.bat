@echo off
setlocal
cd /d "%~dp0"
node jungnang_university_bot.js --loop --interval 600
pause