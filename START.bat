@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo   Competence CRM - Startup Script
echo ========================================

echo [1/6] Checking Environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo   - Virtual Environment Activated
) else (
    echo   - Using System Python (Ensure dependencies are installed)
)

echo [2/6] Terminating Old Processes...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM uvicorn.exe /T >nul 2>&1
echo   - Cleaned up running instances
timeout /t 2 /nobreak >nul

echo [3/6] Clearing Cache...
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "api\__pycache__" rmdir /s /q "api\__pycache__"
del /s /q *.pyc >nul 2>&1
echo   - Cache cleared

echo [4/6] Starting Backend API (Port 8001)...
start "Competence CRM API" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload"

echo   - Waiting for API to wait warm up (5s)...
timeout /t 5 /nobreak >nul

echo [5/6] Starting Legacy Server (Port 3000)...
start "Competence CRM Legacy" cmd /k "python server.py"

echo [6/6] Starting Manager Portal (Port 5173)...
start "Competence CRM Manager" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================
echo   SYSTEM ONLINE
echo ========================================
echo   Manager/Login (New):  http://localhost:5173
echo   Legacy Backend:       http://localhost:3000
echo   API:                  http://localhost:8001
echo   Docs:                 http://localhost:8001/docs
echo ========================================
echo   [Credentials]
echo   Manager:  manager@crm.com  (Password: password123)
echo   Audit:    manager_audit_final@crm.com  (Password: password123)
echo ========================================
echo   To stop servers, close the popup windows.
echo ========================================
pause
