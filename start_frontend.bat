@echo off
echo ==========================================
echo   Transit-IQ Frontend Startup
echo   Running on http://localhost:5173
echo ==========================================
cd /d "%~dp0frontend"
npm run dev
pause
