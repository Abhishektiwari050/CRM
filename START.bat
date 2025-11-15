@echo off
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

echo Starting API server...
cd api
start "CRM API" cmd /k "python -m uvicorn index:app --host 0.0.0.0 --port 8000 --reload"
cd ..

echo Waiting for API to start...
timeout /t 5 /nobreak >nul

echo Testing backend connection...
python test_backend.py
if errorlevel 1 (
    echo Backend test failed! Check the API server window for errors.
    pause
    exit /b 1
)

echo Starting frontend server...
start "CRM Frontend" cmd /k "python server.py"

echo.
echo ========================================
echo Competence CRM Started Successfully
echo ========================================
echo API: http://localhost:8000
echo Frontend: http://localhost:3000
echo ========================================
echo Demo Login: manager@crm.com / password123
echo Employee: john@crm.com / password123
echo ========================================
