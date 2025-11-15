@echo off
echo Cleaning up Python processes and cache...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM python3.12.exe 2>nul
taskkill /F /IM uvicorn.exe 2>nul
timeout /t 2 /nobreak >nul

echo Deleting cache...
del /s /q __pycache__\*.pyc 2>nul
rmdir /s /q __pycache__ 2>nul
rmdir /s /q api\__pycache__ 2>nul
timeout /t 1 /nobreak >nul

echo Starting backend...
cd api
start "CRM API" cmd /k "python -m uvicorn index:app --host 0.0.0.0 --port 8000 --reload"
cd ..

timeout /t 5 /nobreak >nul

echo Starting frontend...
start "CRM Frontend" cmd /k "python server.py"

echo Done!
