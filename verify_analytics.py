
import requests
import json
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
STATS_URL = f"{BASE_URL}/api/manager/stats"
WORKLOAD_URL = f"{BASE_URL}/api/manager/workload-distribution"

# Credentials (assuming these are valid/default for dev)
EMAIL = "manager@competence-consulting.com" 
PASSWORD = "password123" # Replace if you know the actual password or use a known one from seed data

def login():
    print(f"Logging in as {EMAIL}...")
    try:
        resp = requests.post(LOGIN_URL, json={"email": EMAIL, "password": PASSWORD})
        if resp.status_code == 200:
            token = resp.json().get("access_token")
            print("Login successful.")
            return token
        else:
            print(f"Login failed: {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        print(f"Login error: {e}")
        return None

def check_stats(token):
    print("\nChecking /api/manager/stats...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(STATS_URL, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("Stats Response:", json.dumps(data, indent=2))
            if data.get("employees") == 0 and data.get("clients") == 0:
                 print("WARNING: Stats are all zero. Use reproducing script to check database content.")
        else:
            print(f"Stats failed: {resp.status_code} - {resp.text}")
    except Exception as e:
         print(f"Stats error: {e}")

def check_workload(token):
    print("\nChecking /api/manager/workload-distribution...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get(WORKLOAD_URL, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            print("Workload Response:", json.dumps(data, indent=2))
        else:
            print(f"Workload failed: {resp.status_code} - {resp.text}")
    except Exception as e:
         print(f"Workload error: {e}")

if __name__ == "__main__":
    # Try to verify if we can connect
    token = login()
    if token:
        check_stats(token)
        check_workload(token)
    else:
        print("Skipping endpoint checks due to login failure.")
