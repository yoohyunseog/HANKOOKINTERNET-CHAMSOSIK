@echo off
setlocal
cd /d "%~dp0"
node election_bot.js --loop --interval 600
pause