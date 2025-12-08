#!/bin/bash
set -e

# Start backend API in background
# Use port 8001 as configured in server.py proxy target
# Log output to a file or stdout
echo "Starting Backend API on port 8001..."
uvicorn api.main:app --host 127.0.0.1 --port 8001 --workers 4 &

# Wait a bit for backend to initialize
sleep 5

# Start Frontend Proxy Server
# This will listen on the PORT env var provided by Render (or 3000 default)
echo "Starting Frontend Server..."
python server.py