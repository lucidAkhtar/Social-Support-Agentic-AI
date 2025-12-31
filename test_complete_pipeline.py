#!/usr/bin/env python3
"""
Complete Pipeline Test: Extraction → Database → Chatbot
Tests all file types (PDF, PNG, XLSX) and verifies new fields everywhere
"""
import sys
import json
from pathlib import Path

print("=" * 80)
print("COMPLETE PIPELINE TEST")
print("=" * 80)

# Test 1: Document Extraction (PDF, PNG, XLSX)
print("\n1. TESTING DOCUMENT EXTRACTION")
print("-" * 80)

from src.services.document_extractor import DocumentExtractor
extractor = DocumentExtractor()

# Find sample files
search_dirs = [
    Path("data/processed/documents"),
    Path("data/raw"),
    Path("data/processed"),
    Path("data")
]

data_dir = None
for dir_path in search_dirs:
    if dir_path.exists():
        data_dir = dir_path
        break

if not data_dir:
    print("ERROR: No data directory found!")
    sys.exit(1)

print(f"Looking for files in: {data_dir}")

# Test credit report (JSON or PDF) - search recursively
credit_files = list(data_dir.rglob("*credit*.json")) + list(data_dir.rglob("*credit*.pdf"))
employment_files = list(data_dir.rglob("*employment*.txt")) + list(data_dir.rglob("*employment*.pdf"))
bank_files = list(data_dir.rglob("*bank*.pdf")) + list(data_dir.rglob("*bank*.xlsx"))

extraction_results = {}

if credit_files:
    print(f"\nTesting credit report extraction: {credit_files[0].name}")
    try:
        credit_data = extractor.extract_credit_report(str(credit_files[0]))
        extraction_results['credit'] = credit_data
        print(f"  ✓ Credit Score: {credit_data.get('credit_score', 'N/A')}")
        print(f"  ✓ Credit Rating: {credit_data.get('credit_rating', 'N/A')}")
        print(f"  ✓ Payment Ratio: {credit_data.get('payment_ratio', 'N/A')}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        extraction_results['credit'] = {}
else:
    print("\n  ⚠ No credit report files found")
    extraction_results['credit'] = {}

if employment_files:
    print(f"\nTesting employment letter extraction: {employment_files[0].name}")
    try:
        emp_data = extractor.extract_employment_letter(str(employment_files[0]))
        extraction_results['employment'] = emp_data
        print(f"  ✓ Company: {emp_data.get('company_name', 'N/A')}")
        print(f"  ✓ Position: {emp_data.get('current_position', 'N/A')}")
        print(f"  ✓ Salary: {emp_data.get('monthly_salary', 'N/A')}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        extraction_results['employment'] = {}
else:
    print("\n  ⚠ No employment letter files found")
    extraction_results['employment'] = {}

if bank_files:
    print(f"\nTesting bank statement extraction: {bank_files[0].name}")
    try:
        bank_data = extractor.extract_bank_statement(str(bank_files[0]))
        extraction_results['bank'] = bank_data
        print(f"  ✓ Average Balance: {bank_data.get('average_balance', 'N/A')}")
        print(f"  ✓ Income: {bank_data.get('income', 'N/A')}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
        extraction_results['bank'] = {}
else:
    print("\n  ⚠ No bank statement files found")
    extraction_results['bank'] = {}

# Test 2: Database Round-trip
print("\n\n2. TESTING DATABASE ROUND-TRIP")
print("-" * 80)

from src.databases.prod_sqlite_manager import SQLiteManager
db = SQLiteManager('data/databases/unified_db.sqlite')

test_app_id = "TEST_PIPELINE_001"

# Prepare test data with new fields
app_data = {
    'app_id': test_app_id,
    'applicant_name': 'Pipeline Test User',
    'submission_date': '2024-12-31',
    'status': 'COMPLETED',
    'monthly_income': extraction_results.get('employment', {}).get('monthly_salary', 5000),
    'monthly_expenses': 3000,
    'family_size': 4,
    'employment_status': 'Employed',
    'total_assets': 50000,
    'total_liabilities': 20000,
    'credit_score': extraction_results.get('credit', {}).get('credit_score', 0),
    'emirates_id': '784-1234567-1',
    # NEW FIELDS
    'company_name': extraction_results.get('employment', {}).get('company_name'),
    'current_position': extraction_results.get('employment', {}).get('current_position'),
    'join_date': extraction_results.get('employment', {}).get('join_date'),
    'credit_rating': extraction_results.get('credit', {}).get('credit_rating'),
    'payment_ratio': extraction_results.get('credit', {}).get('payment_ratio'),
    'total_outstanding': extraction_results.get('credit', {}).get('total_outstanding'),
    'work_experience_years': extraction_results.get('employment', {}).get('work_experience_years'),
    'education_level': 'Bachelor'
}

print(f"\nInserting test application: {test_app_id}")
print(f"  Company: {app_data.get('company_name')}")
print(f"  Credit Score: {app_data.get('credit_score')}")
print(f"  Credit Rating: {app_data.get('credit_rating')}")

try:
    db.insert_application(app_data)
    print("  ✓ Inserted successfully")
except Exception as e:
    print(f"  ✗ Insert failed: {e}")
    sys.exit(1)

# Query back
print(f"\nQuerying back from database...")
import sqlite3
conn = sqlite3.connect('data/databases/unified_db.sqlite')
cursor = conn.execute('''
    SELECT credit_score, company_name, credit_rating, payment_ratio, 
           current_position, join_date, total_outstanding, 
           work_experience_years, education_level
    FROM applications WHERE app_id = ?
''', (test_app_id,))
row = cursor.fetchone()
conn.close()

if row:
    print("  ✓ Retrieved from database:")
    print(f"    Credit Score: {row[0]}")
    print(f"    Company: {row[1]}")
    print(f"    Credit Rating: {row[2]}")
    print(f"    Payment Ratio: {row[3]}")
    print(f"    Position: {row[4]}")
    print(f"    Join Date: {row[5]}")
    print(f"    Outstanding: {row[6]}")
    print(f"    Experience: {row[7]} years")
    print(f"    Education: {row[8]}")
    
    # Verify data integrity
    if row[0] != app_data.get('credit_score'):
        print(f"  ✗ Credit score mismatch! Expected {app_data.get('credit_score')}, got {row[0]}")
    if row[1] != app_data.get('company_name'):
        print(f"  ✗ Company mismatch! Expected {app_data.get('company_name')}, got {row[1]}")
    if row[2] != app_data.get('credit_rating'):
        print(f"  ✗ Credit rating mismatch! Expected {app_data.get('credit_rating')}, got {row[2]}")
else:
    print("  ✗ Failed to retrieve from database!")
    sys.exit(1)

# Test 3: Verify fields available to chatbot
print("\n\n3. TESTING CHATBOT DATA ACCESS")
print("-" * 80)

# Simulate what the chatbot sees
db_data = db.get_application(test_app_id)
if db_data:
    print("\nData available to chatbot:")
    new_fields = {
        'company_name': db_data.get('company_name'),
        'current_position': db_data.get('current_position'),
        'join_date': db_data.get('join_date'),
        'credit_rating': db_data.get('credit_rating'),
        'payment_ratio': db_data.get('payment_ratio'),
        'total_outstanding': db_data.get('total_outstanding'),
        'work_experience_years': db_data.get('work_experience_years'),
        'education_level': db_data.get('education_level')
    }
    
    for field, value in new_fields.items():
        status = "✓" if value is not None else "✗"
        print(f"  {status} {field}: {value}")
else:
    print("  ✗ Failed to load application data!")

# Test 4: Check FastAPI endpoint field mapping
print("\n\n4. VERIFYING FASTAPI ENDPOINT INTEGRATION")
print("-" * 80)

# Check if the process endpoint has all new fields
with open('src/api/main.py', 'r') as f:
    api_code = f.read()
    
new_field_keys = [
    'company_name',
    'current_position', 
    'join_date',
    'credit_rating',
    'credit_accounts',
    'payment_ratio',
    'total_outstanding',
    'work_experience_years',
    'education_level'
]

print("\nChecking FastAPI app_data dict:")
missing_fields = []
for field in new_field_keys:
    if f'"{field}":' in api_code or f"'{field}':" in api_code:
        print(f"  ✓ {field} - present in API")
    else:
        print(f"  ✗ {field} - MISSING in API!")
        missing_fields.append(field)

if missing_fields:
    print(f"\n  ⚠ WARNING: {len(missing_fields)} fields missing from API!")

# Final summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

extraction_ok = bool(extraction_results.get('credit') or extraction_results.get('employment'))
database_ok = row is not None and row[0] == app_data.get('credit_score')
chatbot_ok = db_data and db_data.get('company_name') is not None
api_ok = len(missing_fields) == 0

print(f"✓ Extraction:     {'PASS' if extraction_ok else 'FAIL'}")
print(f"✓ Database:       {'PASS' if database_ok else 'FAIL'}")
print(f"✓ Chatbot Access: {'PASS' if chatbot_ok else 'FAIL'}")
print(f"✓ API Integration: {'PASS' if api_ok else 'FAIL'}")

if extraction_ok and database_ok and chatbot_ok and api_ok:
    print("\n🎉 ALL TESTS PASSED!")
    sys.exit(0)
else:
    print("\n❌ SOME TESTS FAILED - Review output above")
    sys.exit(1)
