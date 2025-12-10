@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo   Competence CRM - Unified Startup
echo ========================================

echo [1/5] Checking Environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo   - Virtual Environment Activated
) else (
    echo   - CAUTION: Using System Python
)

echo [2/5] Cleaning up old processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

echo [3/5] Building Frontend (React)...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo   - Build FAILED. Aborting.
    pause
    exit /b
)
cd ..
echo   - Build Complete.

echo [4/5] Starting Unified Server (Port 8001)...
start "Competence CRM Server" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8001"

echo [5/5] Launching Browser...
timeout /t 5 /nobreak >nul
start http://localhost:8001

echo.
echo ========================================
echo   SYSTEM ONLINE at http://localhost:8001
echo ========================================
echo   Manager:     manager@crm.com / password123
echo   Employee:    employee@crm.com / password123
echo ========================================
pause
