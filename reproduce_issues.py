import requests
import json
import time

# Configuration
API_URL = "http://localhost:3000/api"
# API_URL = "http://localhost:8001"
MANAGER_EMAIL = "manager@crm.com"
MANAGER_PASSWORD = "password123"

def reproduce_issues():
    print(f"Attempting login for {MANAGER_EMAIL}...")
    try:
        # 1. Login
        resp = requests.post(f"{API_URL}/auth/login", json={"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD})
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} - {resp.text}")
            return
        
        token = resp.json()["access_token"]
        print("Login successful")
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Check Dashboard Data
        print("\n--- Checking Dashboard Data ---")
        resp = requests.get(f"{API_URL}/manager/stats", headers=headers)
        print(f"Manager Stats (Status: {resp.status_code}):")
        print(json.dumps(resp.json(), indent=2))
        
        resp = requests.get(f"{API_URL}/manager/employee-performance", headers=headers)
        print(f"Employee Performance (Status: {resp.status_code}):")
        data = resp.json().get("data", [])
        print(f"Found {len(data)} employees")
        if data:
            print(json.dumps(data[0], indent=2)) # Print first employee only

        # 3. Test Employee Deletion
        print("\n--- Testing Employee Deletion ---")
        # Create dummy employee
        dummy_emp = {
            "name": "Delete Me",
            "email": f"deleteme_{int(time.time())}@crm.com",
            "password": "password123"
        }
        resp = requests.post(f"{API_URL}/employees", json=dummy_emp, headers=headers)
        if resp.status_code == 200:
            emp_id = resp.json()["data"]["id"]
            print(f"Created dummy employee: {emp_id}")
            
            # Delete dummy employee
            resp = requests.delete(f"{API_URL}/admin/users/{emp_id}", headers=headers)
            print(f"Delete Employee Status: {resp.status_code}")
            print(f"Delete Response: {resp.text}")
        else:
            print(f"Failed to create dummy employee: {resp.status_code} - {resp.text}")

        # 4. Test Client Deletion
        print("\n--- Testing Client Deletion ---")
        # Create dummy client
        dummy_client = {
            "name": "Delete Client",
            "member_id": f"DEL-{int(time.time())}",
            "city": "Test City",
            "products_posted": 1,
            "expiry_date": "2025-12-31",
            "email": "client@test.com",
            "phone": "1234567890"
        }
        resp = requests.post(f"{API_URL}/clients", json=dummy_client, headers=headers)
        if resp.status_code == 200:
            client_id = resp.json()["data"]["id"]
            print(f"Created dummy client: {client_id}")
            
            # Delete dummy client
            resp = requests.delete(f"{API_URL}/clients/{client_id}", headers=headers)
            print(f"Delete Client Status: {resp.status_code}")
            print(f"Delete Response: {resp.text}")
        else:
            print(f"Failed to create dummy client: {resp.status_code} - {resp.text}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    reproduce_issues()
