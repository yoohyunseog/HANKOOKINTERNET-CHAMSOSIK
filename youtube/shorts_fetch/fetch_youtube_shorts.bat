@echo off
cd /d %~dp0

:: 가상환경 Python 탐색
set PYTHON_EXE=%~dp0..\..\.venv\Scripts\python.exe
if exist "%PYTHON_EXE%" goto :python_found
set PYTHON_EXE=%~dp0..\..\venv\Scripts\python.exe
if exist "%PYTHON_EXE%" goto :python_found
set PYTHON_EXE=%~dp0\.venv\Scripts\python.exe
if exist "%PYTHON_EXE%" goto :python_found
set PYTHON_EXE=%~dp0venv\Scripts\python.exe
if exist "%PYTHON_EXE%" goto :python_found
set PYTHON_EXE=python

:python_found
"%PYTHON_EXE%" fetch_youtube_shorts.py
