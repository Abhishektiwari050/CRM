import requests
import json

BASE_URL = "http://localhost:8001"

def debug_get_reports():
    try:
        # Login
        login_res = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "manager@crm.com", "password": "admin123"}, timeout=5)
        token = login_res.json()["access_token"]
        
        headers = {"Authorization": f"Bearer {token}"}
        r = requests.get(f"{BASE_URL}/api/daily-reports", headers=headers, timeout=5)
        
        print(f"Status: {r.status_code}")
        print(r.text)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_get_reports()
