@echo off
echo ========================================================
echo        ARIA - AI REWARDS CONCIERGE LAUNCHER
echo ========================================================
echo.

echo [1/2] Launching Backend FastAPI Server...
start "Aria Backend - FastAPI" cmd /k "cd backend && python -m venv venv && call venv\Scripts\activate && pip install -r requirements.txt && python main.py"

echo.
echo [2/2] Launching Frontend Dev Server...
start "Aria Frontend - Vite" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo Aria successfully launched!
echo - Backend will run on: http://localhost:8000
echo - Frontend will run on: http://localhost:5173
echo ========================================================
pause
