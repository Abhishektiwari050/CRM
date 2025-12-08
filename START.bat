@echo off
echo Loading environment variables from .env file...
for /f "usebackq delims=" %%a in (".env") do (
    set "line=%%a"
    REM Skip empty lines and comments
    echo %%a | findstr /r "^[^#].*=" >nul
    if not errorlevel 1 (
        set %%a
    )
)

echo Killing all Python processes...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM python3.12.exe 2>nul
timeout /t 2 /nobreak >nul

echo Deleting all cache files...
del /s /q __pycache__\*.pyc 2>nul
rmdir /s /q __pycache__ 2>nul
rmdir /s /q api\__pycache__ 2>nul
rmdir /s /q .vercel\cache 2>nul
timeout /t 1 /nobreak >nul

echo Starting API server with Supabase connection...
echo Starting API server with Supabase connection...
start "CRM API" cmd /k "python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload"

echo Waiting for API to start...
timeout /t 5 /nobreak >nul

echo Starting frontend server...
start "CRM Frontend" cmd /k "python server.py"

echo.
echo ========================================
echo Competence CRM Started Successfully
echo ========================================
echo API: http://localhost:8001
echo Frontend: http://localhost:3000
echo ========================================
echo Manager Login: manager@crm.com / password123
echo Admin Login: admin@company.com / ChangeMe123!
