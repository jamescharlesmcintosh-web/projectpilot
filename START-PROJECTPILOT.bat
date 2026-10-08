@echo off
setlocal
cd /d "%~dp0"
title ProjectPilot
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 launch.py
) else (
  where python >nul 2>nul
  if %errorlevel%==0 (
    python launch.py
  ) else (
    echo.
    echo Python was not found. Install Python 3.11 or newer, then double-click this file again.
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
  )
)
if not %errorlevel%==0 pause
