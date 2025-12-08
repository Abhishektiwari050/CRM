import requests
import os
import sys

URL = "http://localhost:8001"

def check_health():
    print(f"Checking {URL}/api/health ...")
    try:
        r = requests.get(f"{URL}/api/health", timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Failed to connect: {e}")

def check_login():
    print(f"\nChecking {URL}/api/auth/login ...")
    try:
        r = requests.post(f"{URL}/api/auth/login", json={"email": "manager@crm.com", "password": "admin123"}, timeout=5)
        print(f"Status: {r.status_code}")
        print(f"Response: {r.text}")
    except Exception as e:
        print(f"Failed to connect: {e}")

if __name__ == "__main__":
    check_health()
    check_login()
