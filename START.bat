@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo   Competence CRM - Unified Startup
echo ========================================

echo [1/6] Checking Environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo   - Virtual Environment Activated
) else (
    echo   - CAUTION: Using System Python
)

echo [2/6] Checking Dependencies...
cd frontend
if not exist "node_modules" (
    echo   - Installing Frontend Dependencies...
    call npm install
)
cd ..

echo [3/6] Cleaning up old processes...
taskkill /F /IM uvicorn.exe /T >nul 2>&1
taskkill /F /IM python.exe /T >nul 2>&1
timeout /t 1 /nobreak >nul

echo [4/6] Building Frontend (React)...
cd frontend
call npm run build
if %errorlevel% neq 0 (
    echo   - Build FAILED. Aborting.
    pause
    exit /b
)
cd ..
echo   - Build Complete.

echo [5/6] Starting Unified Server (Port 8001)...
start "Competence CRM Server" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8001"

echo [6/6] Launching Browser...
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
