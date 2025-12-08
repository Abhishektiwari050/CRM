@echo off
echo Loading environment variables...
for /f "tokens=1,* delims==" %%a in (.env) do (
    set %%a=%%b
)

echo Starting API server...
start /b python -m uvicorn api.main:app --host 0.0.0.0 --port 8001 > api.log 2>&1

echo Starting Frontend server...
start /b python -u server.py > server.log 2>&1

echo Servers started. Check api.log and server.log for output.
