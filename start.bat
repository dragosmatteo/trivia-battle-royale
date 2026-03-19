@echo off
echo ============================================
echo    Trivia Battle Royale - Startup
echo ============================================
echo.

REM Start backend
echo [1/2] Starting Backend (FastAPI)...
cd /d "%~dp0backend"
start "Trivia-Backend" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend
timeout /t 3 /nobreak > nul

REM Start frontend
echo [2/2] Starting Frontend (Vite)...
cd /d "%~dp0frontend"
start "Trivia-Frontend" cmd /k "npm run dev"

echo.
echo ============================================
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:5173
echo    API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Deschide http://localhost:5173 in browser
pause
