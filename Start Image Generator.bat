@echo off
cd /d "%~dp0"
title Image Generator Server

echo Starting Image Generator...
echo This window shows the server log. Close it to stop the server.
echo.

start "" cmd /c "timeout /t 12 /nobreak >nul & start "" http://localhost:5000"

venv\Scripts\python.exe app.py
