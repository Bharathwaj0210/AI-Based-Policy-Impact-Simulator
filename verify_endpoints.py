import requests
import os
import sys

BASE_URL = "http://127.0.0.1:8001/api"

TEST_CASES = [
    {
        "domain": "insurance",
        "type": "health",
        "file": "backend/insurance/test_data/health/test_health_100.csv",
        "upload_params": {"insurance_type": "Health Insurance"}
    },
    {
        "domain": "insurance",
        "type": "vehicle",
        "file": "backend/insurance/test_data/vehicle/test_vehicle_100.csv",
        "upload_params": {"insurance_type": "Motor Insurance"}
    },
    {
        "domain": "government",
        "type": "scholarship",
        "file": "backend/government/test_data/test_scholarship_100.csv",
        "upload_params": {"policy": "scholarship"}
    },
    {
        "domain": "government",
        "type": "pension",
        "file": "backend/government/test_data/test_pension_100.csv",
        "upload_params": {"policy": "pension"}
    },
    {
        "domain": "hr",
        "type": "recruitment",
        "file": "backend/hr/test_data/test_recruitment_100.csv",
        "upload_params": {"analysis_type": "Recruitment Optimization"}
    },
    {
        "domain": "hr",
        "type": "attrition",
        "file": "backend/hr/test_data/test_attrition_100.csv",
        "upload_params": {"analysis_type": "Employee Attrition"}
    }
]

def run_tests():
    all_passed = True
    for case in TEST_CASES:
        print(f"\n--- Testing Domain: {case['domain']} ({case['type']}) ---")
        
        # 1. Upload
        url = f"{BASE_URL}/{case['domain']}/upload/"
        filepath = case['file']
        if not os.path.exists(filepath):
            print(f"ERROR: Test file not found at {filepath}")
            all_passed = False
            continue
            
        with open(filepath, 'rb') as f:
            files = {'file': f}
            try:
                r = requests.post(url, files=files, data=case['upload_params'], timeout=30)
            except Exception as e:
                print(f"ERROR connecting to server: {e}")
                sys.exit(1)
        
        if r.status_code != 200:
            print(f"FAILED Upload: {r.status_code} - {r.text[:200]}")
            all_passed = False
            continue
        
        res_data = r.json()
        print("SUCCESS: Uploaded")
        
        # 2. Filter & 3. Explain (parallel tests)
        # Use returned data for subsequent calls
        extracted_data = res_data.get('data', res_data.get('records', []))
        if not extracted_data:
             # Some might return it under a different key or it might be in metrics
             pass
        
        payload = {
            "data": extracted_data,
            "filters": {"age": 30} if case['domain'] == 'insurance' else {},
            **case['upload_params']
        }
        
        # Filter Test
        filter_url = f"{BASE_URL}/{case['domain']}/filter/"
        r_f = requests.post(filter_url, json=payload, timeout=30)
        if r_f.status_code != 200:
            print(f"FAILED Filter: {r_f.status_code} - {r_f.text[:200]}")
            all_passed = False
        else:
            print("SUCCESS: Filtered")

        # Explain (SHAP) Test
        explain_url = f"{BASE_URL}/{case['domain']}/explain/"
        r_e = requests.post(explain_url, json=payload, timeout=60)
        if r_e.status_code != 200:
            print(f"FAILED Explain: {r_e.status_code} - {r_e.text[:200]}")
            all_passed = False
        else:
            print("SUCCESS: Explained (SHAP)")

    if all_passed:
        print("\n🎉 ALL DOMAINS AND ENDPOINTS ARE WORKING PERFECTLY!")
    else:
        print("\n❌ SOME ENDPOINTS FAILED. CHECK LOGS ABOVE.")

if __name__ == "__main__":
    run_tests()
