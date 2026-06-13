@echo off
setlocal
cd /d "%~dp0..\..\..\..\..\..\"
py "%~dp0latest_robot_post_bot.py" "%~dp0latest_robot_post_writer.bot" %*
endlocal
