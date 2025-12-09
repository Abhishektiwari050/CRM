#!/bin/bash
# Exit on error
set -o errexit

echo "Installing Python Dependencies..."
pip install -r requirements.txt

echo "Building React Frontend..."
cd frontend
npm install
npm run build
cd ..

echo "Build Complete!"
