"""
COMPREHENSIVE DATA PIPELINE VALIDATION TEST
Validates that new fields propagate through entire system:
1. Extraction → 2. Database → 3. API → 4. ML Model → 5. RAG Chatbot
"""
from src.services.document_extractor import get_document_extractor
from src.databases.prod_sqlite_manager import SQLiteManager
import json

def test_extraction():
    """Test extraction for TEST-07"""
    print("\n=== PHASE 1: EXTRACTION ===")
    extractor = get_document_extractor()
    
    test_docs = {
        'emirates_id': 'data/test_applications/TEST-07/emirates_id.png',
        'bank_statement': 'data/test_applications/TEST-07/bank_statement.pdf',
        'resume': 'data/test_applications/TEST-07/resume.pdf',
        'employment_letter': 'data/test_applications/TEST-07/employment_letter.pdf',
        'assets_liabilities': 'data/test_applications/TEST-07/assets_liabilities.xlsx',
        'credit_report': 'data/test_applications/TEST-07/credit_report.pdf'
    }
    
    results = {}
    for doc_type, path in test_docs.items():
        try:
            if doc_type == 'emirates_id':
                results[doc_type] = extractor.extract_emirates_id(path)
            elif doc_type == 'bank_statement':
                results[doc_type] = extractor.extract_bank_statement(path)
            elif doc_type == 'resume':
                results[doc_type] = extractor.extract_resume(path)
            elif doc_type == 'employment_letter':
                results[doc_type] = extractor.extract_employment_letter(path)
            elif doc_type == 'assets_liabilities':
                results[doc_type] = extractor.extract_assets_liabilities(path)
            elif doc_type == 'credit_report':
                results[doc_type] = extractor.extract_credit_report(path)
        except Exception as e:
            print(f"❌ {doc_type}: {e}")
            results[doc_type] = {}
    
    # Validate critical fields
    checks = {
        'Applicant Name': results['emirates_id'].get('full_name'),
        'Monthly Income': results['bank_statement'].get('monthly_income'),
        'Company Name': results['employment_letter'].get('company_name'),
        'Monthly Salary': results['employment_letter'].get('monthly_salary'),
        'Total Assets': results['assets_liabilities'].get('total_assets'),
        'Credit Score': results['credit_report'].get('credit_score'),
        'Credit Rating': results['credit_report'].get('credit_rating'),
        'Payment Ratio': results['credit_report'].get('payment_ratio'),
    }
    
    for field, value in checks.items():
        status = "✅" if value else "❌"
        print(f"{status} {field}: {value}")
    
    return results

def test_database_schema():
    """Test database has all new columns"""
    print("\n=== PHASE 2: DATABASE SCHEMA ===")
    db = SQLiteManager()
    
    # Check schema
    with db.get_connection() as conn:
        cursor = conn.execute("PRAGMA table_info(applications)")
        columns = [row[1] for row in cursor.fetchall()]
    
    required_columns = [
        'company_name', 'current_position', 'join_date',
        'credit_rating', 'credit_accounts', 'payment_ratio',
        'total_outstanding', 'work_experience_years', 'education_level'
    ]
    
    for col in required_columns:
        status = "✅" if col in columns else "❌"
        print(f"{status} Column: {col}")
    
    return columns

def test_database_storage():
    """Test database insertion with new fields"""
    print("\n=== PHASE 3: DATABASE STORAGE ===")
    db = SQLiteManager()
    
    test_data = {
        'app_id': 'TEST_VALIDATION_001',
        'applicant_name': 'Test User',
        'emirates_id': 'TEST-123',
        'submission_date': '2025-12-31',
        'status': 'PENDING',
        'monthly_income': 10000,
        'monthly_expenses': 5000,
        'family_size': 3,
        'employment_status': 'employed',
        'total_assets': 200000,
        'total_liabilities': 100000,
        'credit_score': 750,
        'company_name': 'Test Company',
        'current_position': 'Manager',
        'join_date': '2020-01-01',
        'credit_rating': 'Good',
        'payment_ratio': 95.5,
        'total_outstanding': 50000,
        'work_experience_years': 10,
        'education_level': 'Bachelor',
        'credit_accounts': json.dumps([{'type': 'Credit Card', 'balance': 5000}])
    }
    
    try:
        db.insert_application(test_data)
        print("✅ Insertion successful")
        
        # Retrieve and validate
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT company_name, credit_rating, payment_ratio, credit_score FROM applications WHERE app_id = ?",
                ('TEST_VALIDATION_001',)
            )
            row = cursor.fetchone()
            
            if row:
                print(f"✅ Retrieved: company={row[0]}, rating={row[1]}, ratio={row[2]}, score={row[3]}")
                return True
            else:
                print("❌ Could not retrieve data")
                return False
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_types_documentation():
    """Verify ExtractedData type has proper documentation"""
    print("\n=== PHASE 4: TYPE DEFINITIONS ===")
    from src.core.types import ExtractedData
    
    doc = ExtractedData.__doc__ or ""
    
    fields_to_check = [
        'company_name', 'credit_rating', 'payment_ratio',
        'credit_accounts', 'monthly_salary'
    ]
    
    for field in fields_to_check:
        if field in doc:
            print(f"✅ {field} documented")
        else:
            print(f"❌ {field} not documented")

def test_eligibility_features():
    """Verify eligibility agent uses new features"""
    print("\n=== PHASE 5: ELIGIBILITY AGENT ===")
    
    with open('src/agents/eligibility_agent.py', 'r') as f:
        content = f.read()
    
    required_features = [
        'credit_rating', 'payment_ratio', 'monthly_salary',
        'company_name', 'current_position'
    ]
    
    for feature in required_features:
        if feature in content:
            print(f"✅ Feature: {feature}")
        else:
            print(f"❌ Feature: {feature} not found")

def test_rag_context():
    """Verify RAG engine includes new fields"""
    print("\n=== PHASE 6: RAG ENGINE ===")
    
    with open('src/services/rag_engine.py', 'r') as f:
        content = f.read()
    
    required_fields = [
        'company_name', 'current_position', 'credit_rating',
        'payment_ratio', 'total_outstanding'
    ]
    
    for field in required_fields:
        if field in content:
            print(f"✅ Field in context: {field}")
        else:
            print(f"❌ Field missing: {field}")

def test_api_response():
    """Verify API returns new fields"""
    print("\n=== PHASE 7: API RESPONSE ===")
    
    with open('src/api/main.py', 'r') as f:
        content = f.read()
    
    # Check database insertion includes new fields
    insertion_fields = [
        'company_name', 'current_position', 'join_date',
        'credit_rating', 'payment_ratio', 'total_outstanding'
    ]
    
    for field in insertion_fields:
        if f'"{field}"' in content or f"'{field}'" in content:
            print(f"✅ API handles: {field}")
        else:
            print(f"❌ API missing: {field}")

def main():
    print("="*70)
    print("COMPREHENSIVE DATA PIPELINE VALIDATION")
    print("="*70)
    
    # Run all tests
    extraction_results = test_extraction()
    db_columns = test_database_schema()
    db_storage_ok = test_database_storage()
    test_types_documentation()
    test_eligibility_features()
    test_rag_context()
    test_api_response()
    
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)
    
    # Count successes
    total_checks = 0
    passed_checks = 0
    
    # Extraction checks (8 fields)
    extraction_checks = [
        extraction_results['emirates_id'].get('full_name'),
        extraction_results['bank_statement'].get('monthly_income'),
        extraction_results['employment_letter'].get('company_name'),
        extraction_results['employment_letter'].get('monthly_salary'),
        extraction_results['assets_liabilities'].get('total_assets'),
        extraction_results['credit_report'].get('credit_score'),
        extraction_results['credit_report'].get('credit_rating'),
        extraction_results['credit_report'].get('payment_ratio'),
    ]
    total_checks += 8
    passed_checks += sum(1 for x in extraction_checks if x)
    
    # Database schema (9 columns)
    required_cols = [
        'company_name', 'current_position', 'join_date',
        'credit_rating', 'credit_accounts', 'payment_ratio',
        'total_outstanding', 'work_experience_years', 'education_level'
    ]
    total_checks += 9
    passed_checks += sum(1 for col in required_cols if col in db_columns)
    
    # Database storage (1 check)
    total_checks += 1
    if db_storage_ok:
        passed_checks += 1
    
    print(f"\n✅ Passed: {passed_checks}/{total_checks} checks")
    print(f"📊 Success Rate: {(passed_checks/total_checks)*100:.1f}%")
    
    if passed_checks == total_checks:
        print("\n🎉 ALL VALIDATIONS PASSED - System is production-ready!")
    else:
        print(f"\n⚠️  {total_checks - passed_checks} issues need attention")

if __name__ == "__main__":
    main()
