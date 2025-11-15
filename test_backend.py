#!/usr/bin/env python3
"""
Quick backend health check script
"""
import requests
import json
import sys

def test_backend():
    base_url = "http://localhost:8000"
    
    print("Testing Competence CRM Backend...")
    print(f"Base URL: {base_url}")
    print("-" * 50)
    
    # Test 1: Health check
    try:
        print("1. Testing health endpoint...")
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("PASS: Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"FAIL: Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: Cannot connect to backend: {e}")
        print("Make sure to run: python -m uvicorn index:app --host 0.0.0.0 --port 8001")
        return False
    
    # Test 2: Login endpoint
    try:
        print("\n2. Testing login endpoint...")
        login_data = {
            "email": "manager@crm.com",
            "password": "password123"
        }
        response = requests.post(
            f"{base_url}/api/auth/login", 
            json=login_data,
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            print("PASS: Login test passed")
            print(f"   User: {data.get('user', {}).get('name')} ({data.get('user', {}).get('role')})")
            return True
        else:
            print(f"FAIL: Login test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"FAIL: Login test error: {e}")
        return False

if __name__ == "__main__":
    success = test_backend()
    if success:
        print("\nSUCCESS: Backend is working correctly!")
        print("You can now start the frontend with: python server.py")
    else:
        print("\nFAILED: Backend has issues - fix these before starting frontend")
    sys.exit(0 if success else 1)