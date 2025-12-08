import requests
import json
import time
from datetime import datetime, timedelta

API_URL = "http://localhost:8001/api"
MANAGER_EMAIL = "manager@crm.com"
MANAGER_PASSWORD = "password123"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def test_verification():
    log("Starting verification...")
    
    # 1. Login as Manager
    log("Logging in as Manager...")
    resp = requests.post(f"{API_URL}/auth/login", json={"email": MANAGER_EMAIL, "password": MANAGER_PASSWORD})
    if resp.status_code != 200:
        log(f"Manager login failed: {resp.text}")
        return
    manager_token = resp.json()["access_token"]
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    
    # 2. Create Test Employees
    log("Creating test employees...")
    ts = int(time.time())
    emp_a = {"name": f"Test Emp A {ts}", "email": f"empa_{ts}@test.com", "password": "password123"}
    emp_b = {"name": f"Test Emp B {ts}", "email": f"empb_{ts}@test.com", "password": "password123"}
    
    resp_a = requests.post(f"{API_URL}/employees", json=emp_a, headers=manager_headers)
    resp_b = requests.post(f"{API_URL}/employees", json=emp_b, headers=manager_headers)
    
    if resp_a.status_code != 200 or resp_b.status_code != 200:
        log(f"Failed to create employees: {resp_a.text} / {resp_b.text}")
        return
        
    id_a = resp_a.json()["data"]["id"]
    id_b = resp_b.json()["data"]["id"]
    log(f"Created Emp A ({id_a}) and Emp B ({id_b})")
    
    # 3. Create Test Clients with specific Expiry Dates
    # Client A1: Overdue (Expired 10 days ago) -> Assigned to A
    # Client A2: Due Soon (Expires in 10 days) -> Assigned to A
    # Client B1: Good (Expires in 60 days) -> Assigned to B
    
    today = datetime.utcnow().date()
    clients_data = [
        {"name": f"Client A Overdue {ts}", "expiry_date": (today - timedelta(days=10)).isoformat(), "assigned": id_a, "expected_status": "overdue"},
        {"name": f"Client A DueSoon {ts}", "expiry_date": (today + timedelta(days=10)).isoformat(), "assigned": id_a, "expected_status": "due_soon"},
        {"name": f"Client B Good {ts}", "expiry_date": (today + timedelta(days=60)).isoformat(), "assigned": id_b, "expected_status": "good"}
    ]
    
    created_client_ids = []
    
    for c in clients_data:
        payload = {
            "name": c["name"],
            "expiry_date": c["expiry_date"],
            "email": f"client_{int(time.time())}_{c['expected_status']}@test.com"
        }
        resp = requests.post(f"{API_URL}/clients", json=payload, headers=manager_headers)
        if resp.status_code != 200:
            log(f"Failed to create client {c['name']}: {resp.text}")
            continue
        
        cid = resp.json()["data"]["id"]
        created_client_ids.append(cid)
        
        # Assign client
        requests.post(f"{API_URL}/clients/{cid}/assign", json={"employee_id": c["assigned"]}, headers=manager_headers)
        log(f"Created and assigned {c['name']} to {c['assigned']}")

    # 4. Verify Emp A View
    log("\n--- Verifying Emp A View ---")
    resp = requests.post(f"{API_URL}/auth/login", json={"email": emp_a["email"], "password": emp_a["password"]})
    token_a = resp.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    
    resp = requests.get(f"{API_URL}/clients", headers=headers_a)
    clients_a = resp.json()["data"]
    
    # Check Isolation
    log(f"Emp A sees {len(clients_a)} clients")
    if len(clients_a) != 2:
        log("FAIL: Emp A should see exactly 2 clients")
    else:
        log("PASS: Emp A sees correct number of clients")
        
    # Check Status Calculation
    for c in clients_a:
        name = c["name"]
        status = c.get("status")
        days = c.get("days_until_expiry")
        
        if "Overdue" in name:
            if status == "overdue" and days < 0:
                log(f"PASS: {name} is {status} ({days} days)")
            else:
                log(f"FAIL: {name} is {status} ({days} days) - Expected overdue < 0")
        elif "DueSoon" in name:
            if status == "due_soon" and 0 <= days <= 30:
                log(f"PASS: {name} is {status} ({days} days)")
            else:
                log(f"FAIL: {name} is {status} ({days} days) - Expected due_soon 0-30")
    
    # Check Emp A cannot see Emp B's client
    b_client_visible = any("Client B" in c["name"] for c in clients_a)
    if b_client_visible:
        log("FAIL: Emp A can see Emp B's client!")
    else:
        log("PASS: Emp A cannot see Emp B's client")

    # 5. Verify Emp B View
    log("\n--- Verifying Emp B View ---")
    resp = requests.post(f"{API_URL}/auth/login", json={"email": emp_b["email"], "password": emp_b["password"]})
    token_b = resp.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}
    
    resp = requests.get(f"{API_URL}/clients", headers=headers_b)
    clients_b = resp.json()["data"]
    
    log(f"Emp B sees {len(clients_b)} clients")
    if len(clients_b) != 1:
        log("FAIL: Emp B should see exactly 1 client")
    else:
        log("PASS: Emp B sees correct number of clients")
        
    if clients_b and clients_b[0]["status"] == "good":
        log(f"PASS: {clients_b[0]['name']} is good")
    else:
        log(f"FAIL: {clients_b[0]['name']} status is {clients_b[0].get('status')}")

    # 6. Cleanup
    log("\n--- Cleanup ---")
    for cid in created_client_ids:
        requests.delete(f"{API_URL}/clients/{cid}", headers=manager_headers)
    requests.delete(f"{API_URL}/admin/users/{id_a}", headers=manager_headers)
    requests.delete(f"{API_URL}/admin/users/{id_b}", headers=manager_headers)
    log("Cleanup complete")

if __name__ == "__main__":
    test_verification()
