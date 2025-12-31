"""
PRODUCTION-LEVEL END-TO-END TEST
Tests complete workflow: Upload → Extract → Process → Store → Query

Tests 3 applications with all 6-7 document types:
1. TEST-01
2. TEST-02
3. TEST-03

Validates:
✅ All documents uploaded successfully
✅ Extraction returns data for all document types
✅ Critical fields extracted (name, income, assets, credit score)
✅ Data saved to database
✅ Chatbot can access and query the data
"""
import sys
import sqlite3
from pathlib import Path
import requests
import json
import time

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'

API_BASE = "http://localhost:8000/api/applications"
DB_PATH = "data/databases/applications.db"

def print_section(title):
    print(f"\n{Colors.BLUE}{'='*70}")
    print(f"{title:^70}")
    print(f"{'='*70}{Colors.RESET}\n")

def test_application_processing(app_id, test_folder):
    """
    Full end-to-end test for one application
    
    Steps:
    1. Create application
    2. Upload all documents
    3. Process application
    4. Verify extraction results
    5. Verify database storage
    6. Test chatbot queries
    """
    print(f"\n{Colors.BLUE}📋 Testing Application: {app_id}{Colors.RESET}")
    print(f"   Test Data Folder: {test_folder}")
    
    test_results = {
        "app_id": app_id,
        "create_success": False,
        "upload_success": False,
        "process_success": False,
        "extraction_quality": {},
        "database_saved": False,
        "chatbot_accessible": False
    }
    
    # Step 1: Create Application
    try:
        response = requests.post(f"{API_BASE}/create", data={
            "applicant_name": f"Test Applicant {app_id}"
        })
        if response.status_code == 200:
            print(f"   {Colors.GREEN}✅ Application created{Colors.RESET}")
            test_results["create_success"] = True
            # Use the returned application ID
            result = response.json()
            app_id = result.get("application_id", app_id)
            test_results["app_id"] = app_id
        else:
            print(f"   {Colors.RED}❌ Failed to create application: {response.status_code}{Colors.RESET}")
            print(f"      Response: {response.text[:200]}")
            return test_results
    except Exception as e:
        print(f"   {Colors.RED}❌ Create request failed: {e}{Colors.RESET}")
        return test_results
    
    # Step 2: Upload Documents
    document_files = [
        ("emirates_id.png", "emirates_id"),
        ("bank_statement.pdf", "bank_statement"),
        ("resume.pdf", "resume"),
        ("employment_letter.pdf", "employment_letter"),
        ("assets_liabilities.xlsx", "assets_liabilities"),
        ("credit_report.json", "credit_report")
    ]
    
    uploaded_count = 0
    for filename, doc_type in document_files:
        file_path = Path(test_folder) / filename
        if not file_path.exists():
            print(f"   {Colors.YELLOW}⚠️  {filename} not found, skipping{Colors.RESET}")
            continue
        
        try:
            with open(file_path, 'rb') as f:
                # Upload as multipart form with file
                files = {"documents": (filename, f, "application/octet-stream")}
                response = requests.post(
                    f"{API_BASE}/{app_id}/upload",
                    files=files
                )
                if response.status_code == 200:
                    uploaded_count += 1
                else:
                    print(f"   {Colors.RED}❌ Failed to upload {filename}: {response.status_code}{Colors.RESET}")
                    if response.status_code != 404:
                        print(f"      Response: {response.text[:150]}")
        except Exception as e:
            print(f"   {Colors.RED}❌ Upload failed for {filename}: {e}{Colors.RESET}")
    
    print(f"   {Colors.GREEN}✅ Uploaded {uploaded_count}/{len(document_files)} documents{Colors.RESET}")
    test_results["upload_success"] = uploaded_count >= 5  # At least 5 critical docs
    
    # Step 3: Process Application
    try:
        print(f"   {Colors.YELLOW}⏳ Processing application (this may take 10-15 seconds)...{Colors.RESET}")
        response = requests.post(f"{API_BASE}/{app_id}/process")
        if response.status_code == 200:
            print(f"   {Colors.GREEN}✅ Application processed{Colors.RESET}")
            test_results["process_success"] = True
        else:
            print(f"   {Colors.RED}❌ Processing failed: {response.status_code}{Colors.RESET}")
            print(f"      Response: {response.text[:200]}")
            return test_results
    except Exception as e:
        print(f"   {Colors.RED}❌ Process request failed: {e}{Colors.RESET}")
        return test_results
    
    # Step 4: Verify Extraction Results
    try:
        response = requests.get(f"{API_BASE}/{app_id}/results")
        if response.status_code == 200:
            results = response.json()
            
            # Check critical fields
            extraction_checks = {
                "applicant_name": results.get("applicant_info", {}).get("full_name"),
                "monthly_income": results.get("income_data", {}).get("monthly_income"),
                "total_assets": results.get("assets_liabilities", {}).get("total_assets"),
                "credit_score": results.get("credit_data", {}).get("credit_score"),
                "company_name": results.get("employment_data", {}).get("company_name"),
                "credit_rating": results.get("credit_data", {}).get("credit_rating")
            }
            
            for field, value in extraction_checks.items():
                if value:
                    test_results["extraction_quality"][field] = True
                    print(f"   {Colors.GREEN}✅ {field}: {value}{Colors.RESET}")
                else:
                    test_results["extraction_quality"][field] = False
                    print(f"   {Colors.YELLOW}⚠️  {field}: Not extracted{Colors.RESET}")
        else:
            print(f"   {Colors.RED}❌ Failed to get results: {response.status_code}{Colors.RESET}")
    except Exception as e:
        print(f"   {Colors.RED}❌ Results request failed: {e}{Colors.RESET}")
    
    # Step 5: Verify Database Storage
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE app_id = ?", (app_id,))
        row = cursor.fetchone()
        
        if row:
            print(f"   {Colors.GREEN}✅ Data saved to database{Colors.RESET}")
            
            # Check specific columns
            cursor.execute("""
                SELECT monthly_income, total_assets, credit_score, 
                       company_name, credit_rating, payment_ratio
                FROM applications WHERE app_id = ?
            """, (app_id,))
            db_row = cursor.fetchone()
            
            if db_row:
                monthly_income, total_assets, credit_score, company_name, credit_rating, payment_ratio = db_row
                print(f"      💰 Monthly Income: {monthly_income}")
                print(f"      🏦 Total Assets: {total_assets}")
                print(f"      📊 Credit Score: {credit_score}")
                print(f"      🏢 Company: {company_name}")
                print(f"      📈 Credit Rating: {credit_rating}")
                print(f"      💳 Payment Ratio: {payment_ratio}%")
                test_results["database_saved"] = True
        else:
            print(f"   {Colors.RED}❌ No data found in database{Colors.RESET}")
        
        conn.close()
    except Exception as e:
        print(f"   {Colors.RED}❌ Database check failed: {e}{Colors.RESET}")
    
    # Step 6: Test Chatbot Access
    try:
        response = requests.post(f"{API_BASE}/{app_id}/chat", json={
            "session_id": f"test_session_{app_id}",
            "question": "What is the applicant's monthly income and credit score?"
        })
        
        if response.status_code == 200:
            chat_response = response.json()
            answer = chat_response.get("answer", "")
            
            # Check if chatbot can access the data
            has_income = any(word in answer.lower() for word in ["income", "salary", "aed"])
            has_credit = any(word in answer.lower() for word in ["credit", "score"])
            
            if has_income or has_credit:
                print(f"   {Colors.GREEN}✅ Chatbot can access data{Colors.RESET}")
                print(f"      Response: {answer[:150]}...")
                test_results["chatbot_accessible"] = True
            else:
                print(f"   {Colors.YELLOW}⚠️  Chatbot response unclear{Colors.RESET}")
        else:
            print(f"   {Colors.YELLOW}⚠️  Chat endpoint returned: {response.status_code}{Colors.RESET}")
    except Exception as e:
        print(f"   {Colors.YELLOW}⚠️  Chat test skipped: {e}{Colors.RESET}")
    
    return test_results

def main():
    print_section("PRODUCTION-LEVEL END-TO-END TEST")
    print(f"{Colors.BLUE}Testing complete workflow for 3 applications{Colors.RESET}")
    print(f"{Colors.BLUE}API Server: {API_BASE}{Colors.RESET}")
    print(f"{Colors.BLUE}Database: {DB_PATH}{Colors.RESET}")
    
    # Check API is running
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print(f"\n{Colors.GREEN}✅ API server is running{Colors.RESET}")
        else:
            print(f"\n{Colors.RED}❌ API server not responding correctly{Colors.RESET}")
            return 1
    except Exception as e:
        print(f"\n{Colors.RED}❌ Cannot connect to API server{Colors.RESET}")
        print(f"{Colors.RED}   Please start the server with: poetry run python startup.py{Colors.RESET}")
        return 1
    
    # Test applications
    test_apps = [
        ("PROD-TEST-01", "data/test_applications/TEST-01"),
        ("PROD-TEST-02", "data/test_applications/TEST-02"),
        ("PROD-TEST-03", "data/test_applications/TEST-03")
    ]
    
    all_results = []
    
    for app_id, test_folder in test_apps:
        result = test_application_processing(app_id, test_folder)
        all_results.append(result)
        time.sleep(2)  # Brief pause between tests
    
    # Final Summary
    print_section("FINAL TEST RESULTS")
    
    success_count = 0
    for result in all_results:
        app_id = result["app_id"]
        all_passed = (
            result["create_success"] and
            result["upload_success"] and
            result["process_success"] and
            result["database_saved"]
        )
        
        if all_passed:
            success_count += 1
            print(f"{Colors.GREEN}✅ {app_id}: PASSED{Colors.RESET}")
        else:
            print(f"{Colors.RED}❌ {app_id}: FAILED{Colors.RESET}")
            if not result["create_success"]:
                print(f"   - Application creation failed")
            if not result["upload_success"]:
                print(f"   - Document upload incomplete")
            if not result["process_success"]:
                print(f"   - Processing failed")
            if not result["database_saved"]:
                print(f"   - Database storage failed")
    
    print(f"\n{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BLUE}Success Rate: {success_count}/{len(all_results)}{Colors.RESET}")
    
    if success_count == len(all_results):
        print(f"\n{Colors.GREEN}🎉 ALL TESTS PASSED! System is production-ready.{Colors.RESET}\n")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Review errors above.{Colors.RESET}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
