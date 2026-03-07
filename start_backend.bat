@echo off
echo ==========================================
echo   Transit-IQ Backend Startup
echo   Intelligent Fleet Orchestration System
echo ==========================================
cd /d "%~dp0backend"

echo Checking for existing process on port 8000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000 "') do (
    echo Killing old backend process PID %%a ...
    taskkill /F /PID %%a >nul 2>&1
)
timeout /t 1 /nobreak >nul

echo Starting FastAPI backend on http://localhost:8000 ...
python main.py
pause
