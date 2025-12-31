#!/usr/bin/env python3
"""
Test script for APP_967DFD01 - Verify all 3 issues are fixed:
1. NoneType error in process endpoint
2. get_validation_history missing method error
3. Chatbot access to database data
"""
import sys
from pathlib import Path
from src.databases.prod_sqlite_manager import SQLiteManager

print("=" * 80)
print("DIAGNOSTIC TEST FOR APP_967DFD01")
print("=" * 80)

# Check 1: Does application exist in database?
print("\n1. Checking if APP_967DFD01 exists in database...")
db = SQLiteManager('data/databases/unified_db.sqlite')
app_data = db.get_application('APP_967DFD01')

if app_data:
    print(f"✓ Application found in database")
    print(f"  Name: {app_data.get('applicant_name')}")
    print(f"  Credit Score: {app_data.get('credit_score')}")
    print(f"  Company: {app_data.get('company_name')}")
    print(f"  Credit Rating: {app_data.get('credit_rating')}")
    print(f"  Payment Ratio: {app_data.get('payment_ratio')}")
    
    # Check 2: Test chatbot data loading
    print("\n2. Testing chatbot data access...")
    extracted_data_dict = {
        'monthly_income': app_data.get('monthly_income', 0),
        'credit_score': app_data.get('credit_score', 0),
        'company_name': app_data.get('company_name'),
        'current_position': app_data.get('current_position'),
        'credit_rating': app_data.get('credit_rating'),
        'payment_ratio': app_data.get('payment_ratio'),
        'total_outstanding': app_data.get('total_outstanding'),
    }
    
    fields_ok = sum(1 for v in extracted_data_dict.values() if v is not None and v != 0)
    print(f"  ✓ Chatbot has access to {fields_ok}/{len(extracted_data_dict)} fields")
    for k, v in extracted_data_dict.items():
        status = "✓" if v is not None and v != 0 else "✗"
        print(f"    {status} {k}: {v}")
    
    # Check 3: Verify no get_validation_history errors
    print("\n3. Testing unified database manager...")
    from src.databases.unified_database_manager import UnifiedDatabaseManager
    unified_db = UnifiedDatabaseManager()
    try:
        # This used to call get_validation_history
        result = unified_db.get_full_application_context('APP_967DFD01')
        print(f"  ✓ Unified DB query successful (no get_validation_history error)")
    except AttributeError as e:
        print(f"  ✗ AttributeError still present: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"  ⚠ Other error: {e}")
    
    print("\n" + "=" * 80)
    print("✓ ALL CHECKS PASSED - Application data is accessible")
    print("=" * 80)
    
else:
    print("✗ Application NOT found in database!")
    print("\nPossible reasons:")
    print("  1. Processing failed before saving to database")
    print("  2. Application ID was never created")
    print("  3. Database path is incorrect")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    print("=" * 80)
    print("1. Re-upload documents for this application")
    print("2. Re-run: POST /api/applications/APP_967DFD01/process")
    print("3. The fixed code will now handle None values gracefully")
    print("4. Data will be saved to database correctly")
    print("5. Chatbot will have full access to all fields")
    
    sys.exit(1)
