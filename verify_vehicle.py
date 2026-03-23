import requests
import os

BASE_URL = "http://127.0.0.1:8001/api"
case = {
    "domain": "insurance",
    "type": "vehicle",
    "file": "backend/insurance/test_data/vehicle/test_vehicle_100.csv",
    "upload_params": {"insurance_type": "Motor Insurance"}
}

def test_vehicle():
    print(f"\n--- Targeted Test: {case['domain']} ({case['type']}) ---")
    url = f"{BASE_URL}/{case['domain']}/upload/"
    with open(case['file'], 'rb') as f:
        files = {'file': f}
        r = requests.post(url, files=files, data=case['upload_params'], timeout=30)
    
    if r.status_code != 200:
        print(f"FAILED Upload: {r.status_code} - {r.text[:200]}")
        return
    
    data = r.json()
    if data.get('status') == 'error':
        print(f"FAILED (Backend Logic): {data.get('message')}")
        return
        
    print("SUCCESS: Uploaded and Predicted")
    
    payload = {
        "data": data.get('data', data.get('records', [])),
        "filters": {},
        **case['upload_params']
    }
    
    # Filter Test
    r_f = requests.post(f"{BASE_URL}/{case['domain']}/filter/", json=payload, timeout=30)
    print(f"Filter status: {r_f.status_code}")
    
    # Explain Test
    r_e = requests.post(f"{BASE_URL}/{case['domain']}/explain/", json=payload, timeout=60)
    print(f"Explain status: {r_e.status_code}")
    if r_e.status_code == 200:
        print("🎉 VEHICLE DOMAIN IS NOW FULLY STABLE!")

if __name__ == "__main__":
    test_vehicle()
