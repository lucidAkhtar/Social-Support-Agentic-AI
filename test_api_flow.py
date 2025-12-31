#!/usr/bin/env python3
"""
Test complete API flow with TEST-07 documents
"""
import requests
import time
from pathlib import Path

BASE_URL = "http://localhost:8005"

def test_flow():
    print("=== TESTING COMPLETE API FLOW ===\n")
    
    # 1. Create application
    print("1. Creating application...")
    response = requests.post(
        f"{BASE_URL}/api/applications/create",
        data={"applicant_name": "TEST USER 07"}
    )
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return
    
    data = response.json()
    app_id = data["application_id"]
    print(f"✓ Created: {app_id}\n")
    
    # 2. Upload documents
    print("2. Uploading TEST-07 documents...")
    test_dir = Path("data/processed/TEST-07")
    
    files = []
    for doc in test_dir.glob("*"):
        if doc.is_file():
            files.append(("documents", (doc.name, open(doc, "rb"))))
            print(f"  - {doc.name}")
    
    response = requests.post(
        f"{BASE_URL}/api/applications/{app_id}/upload",
        files=files
    )
    
    # Close files
    for _, (_, f) in files:
        f.close()
    
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return
    
    upload_data = response.json()
    print(f"✓ Uploaded {upload_data['uploaded_count']} documents\n")
    
    # 3. Process application
    print("3. Processing application (this will take 30-60 seconds)...")
    response = requests.post(f"{BASE_URL}/api/applications/{app_id}/process")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return
    
    process_data = response.json()
    print(f"✓ Processing complete: {process_data['current_stage']}\n")
    
    # 4. Get results
    print("4. Fetching results...")
    response = requests.get(f"{BASE_URL}/api/applications/{app_id}/results")
    print(f"Status: {response.status_code}")
    if response.status_code != 200:
        print(f"ERROR: {response.text}")
        return
    
    results = response.json()
    
    # Print extracted data from database
    print("\n=== DATABASE STORED VALUES ===")
    db_fields = results.get("database_stored_fields", {})
    if db_fields:
        print(f"Company: {db_fields.get('company_name')}")
        print(f"Position: {db_fields.get('current_position')}")
        print(f"Credit Score: {db_fields.get('credit_score')}")
        print(f"Credit Rating: {db_fields.get('credit_rating')}")
        print(f"Payment Ratio: {db_fields.get('payment_ratio')}")
        print(f"Work Experience: {db_fields.get('work_experience_years')} years")
    else:
        print("NO DATABASE FIELDS FOUND!")
    
    # Print extracted data from state
    print("\n=== EXTRACTED DATA (FROM STATE) ===")
    extracted = results.get("extracted_data", {})
    if extracted:
        credit_data = extracted.get("credit_data", {})
        employment_data = extracted.get("employment_data", {})
        print(f"Credit Score (state): {credit_data.get('credit_score')}")
        print(f"Credit Rating (state): {credit_data.get('credit_rating')}")
        print(f"Company (state): {employment_data.get('company_name')}")
        print(f"Salary (state): {employment_data.get('monthly_salary')}")
    else:
        print("NO EXTRACTED DATA!")
    
    print("\n✓ Test complete")

if __name__ == "__main__":
    test_flow()
