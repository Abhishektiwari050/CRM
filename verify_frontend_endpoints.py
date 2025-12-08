import requests
import json
import sys

BASE_URL = "http://localhost:8001"
MANAGER_EMAIL = "manager@crm.com"
MANAGER_PASSWORD = "admin123"

def login():
    print(f"Logging in as {MANAGER_EMAIL}...")
    try:
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD})
        if resp.status_code != 200:
            print(f"Login failed: {resp.text}")
            sys.exit(1)
        data = resp.json()
        print("Login successful")
        return data["access_token"]
    except Exception as e:
        print(f"Login error: {e}")
        sys.exit(1)

def verify_endpoints(token):
    headers = {"Authorization": f"Bearer {token}"}
    
    endpoints = [
        "/api/manager/stats",
        "/api/manager/employee-performance",
        "/api/manager/alerts",
        "/api/manager/workload-distribution",
        "/api/manager/report-flags",
        "/api/notifications"
    ]
    
    success = True
    for ep in endpoints:
        url = f"{BASE_URL}{ep}"
        print(f"Testing {ep}...", end=" ")
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                print("OK")
                # print(json.dumps(resp.json(), indent=2))
            else:
                print(f"FAILED ({resp.status_code})")
                print(resp.text)
                success = False
        except Exception as e:
            print(f"ERROR: {e}")
            success = False
            
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    token = login()
    verify_endpoints(token)
    print("\nAll Manager Dashboard endpoints verified successfully.")
