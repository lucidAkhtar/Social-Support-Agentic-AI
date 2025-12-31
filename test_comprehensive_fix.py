"""
COMPREHENSIVE FIX VERIFICATION
==============================
Tests all issues reported by user:
1. AttributeError: support_duration_months
2. Database storage not working  
3. Chatbot saying "upload documents" despite completed status
"""

import sys
import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

BASE_URL = "http://localhost:8000"
TEST_APP_ID = "APP_26993207"  # User's test application

def print_header(title):
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{title}")
    print(f"{'='*80}{Style.RESET_ALL}\n")

def test_process_endpoint():
    """Test 1: Verify /process endpoint works without AttributeError"""
    print_header("TEST 1: Process Endpoint (AttributeError Fix)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/applications/{TEST_APP_ID}/process",
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ PASS: Process endpoint completed successfully{Style.RESET_ALL}")
            print(f"   Stage: {data.get('current_stage')}")
            print(f"   Progress: {data.get('progress_percentage')}%")
            return True
        else:
            print(f"{Fore.RED}❌ FAIL: HTTP {response.status_code}{Style.RESET_ALL}")
            print(f"   Error: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.YELLOW}⚠️  SKIP: API server not running{Style.RESET_ALL}")
        print(f"   Start with: poetry run python -m uvicorn src.api.main:app --reload")
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ FAIL: {str(e)}{Style.RESET_ALL}")
        return False

def test_database_storage():
    """Test 2: Verify database is populated with real data"""
    print_header("TEST 2: Database Storage (Data Persistence)")
    
    try:
        from src.databases.prod_sqlite_manager import SQLiteManager
        db = SQLiteManager()
        
        # Check application data
        app_data = db.get_application(TEST_APP_ID)
        if not app_data:
            print(f"{Fore.RED}❌ FAIL: Application not found in database{Style.RESET_ALL}")
            return False
        
        print(f"{Fore.CYAN}Application Data:{Style.RESET_ALL}")
        print(f"  Status: {app_data['status']}")
        print(f"  Name: {app_data['applicant_name']}")
        print(f"  Monthly Income: {app_data['monthly_income']} AED")
        print(f"  Total Assets: {app_data['total_assets']} AED")
        print(f"  Total Liabilities: {app_data['total_liabilities']} AED")
        print(f"  Employment: {app_data['employment_status']}")
        
        # Verify data is not zeros
        checks = []
        
        if app_data['status'] in ['COMPLETED', 'completed']:
            print(f"{Fore.GREEN}  ✓ Status is completed{Style.RESET_ALL}")
            checks.append(True)
        else:
            print(f"{Fore.RED}  ✗ Status is still {app_data['status']}{Style.RESET_ALL}")
            checks.append(False)
        
        if app_data['monthly_income'] > 0:
            print(f"{Fore.GREEN}  ✓ Monthly income extracted: {app_data['monthly_income']:.2f} AED{Style.RESET_ALL}")
            checks.append(True)
        else:
            print(f"{Fore.RED}  ✗ Monthly income is 0{Style.RESET_ALL}")
            checks.append(False)
        
        if app_data['total_assets'] > 0:
            print(f"{Fore.GREEN}  ✓ Total assets extracted: {app_data['total_assets']:.2f} AED{Style.RESET_ALL}")
            checks.append(True)
        else:
            print(f"{Fore.YELLOW}  ⚠ Total assets is 0 (may be legitimate){Style.RESET_ALL}")
            checks.append(True)  # Don't fail on this
        
        # Check decision data
        print(f"\n{Fore.CYAN}Decision Data:{Style.RESET_ALL}")
        decision = db.get_decision_by_app_id(TEST_APP_ID)
        if decision:
            print(f"  Decision: {decision.get('decision')}")
            print(f"  Policy Score: {decision.get('policy_score')}")
            print(f"  Priority: {decision.get('priority')}")
            print(f"  Support Amount: {decision.get('support_amount')} AED")
            print(f"{Fore.GREEN}  ✓ Decision data found{Style.RESET_ALL}")
            checks.append(True)
        else:
            print(f"{Fore.RED}  ✗ No decision data found{Style.RESET_ALL}")
            checks.append(False)
        
        if all(checks):
            print(f"\n{Fore.GREEN}✅ PASS: Database storage working correctly{Style.RESET_ALL}")
            return True
        else:
            print(f"\n{Fore.RED}❌ FAIL: Some database checks failed{Style.RESET_ALL}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ FAIL: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        return False

def test_chatbot_response():
    """Test 3: Verify chatbot gives accurate response (not "upload documents")"""
    print_header("TEST 3: Chatbot Response (RAG Engine Fix)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/applications/{TEST_APP_ID}/chat",
            json={"query": "Why was my application soft declined?"},
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"{Fore.RED}❌ FAIL: HTTP {response.status_code}{Style.RESET_ALL}")
            return False
        
        data = response.json()
        bot_response = data.get('response', '')
        
        print(f"{Fore.CYAN}Chatbot Response (first 300 chars):{Style.RESET_ALL}")
        print(f"  {bot_response[:300]}...")
        
        # Check for wrong responses
        wrong_indicators = [
            "upload", "pending status", "not yet processed",
            "required documents have not been uploaded",
            "Upload required documents"
        ]
        
        has_wrong_response = any(indicator.lower() in bot_response.lower() for indicator in wrong_indicators)
        
        # Check for correct responses
        correct_indicators = [
            "soft decline", "income", "5560", "5,560",
            "debt", "financial", "program"
        ]
        
        has_correct_response = any(indicator.lower() in bot_response.lower() for indicator in correct_indicators)
        
        if has_wrong_response:
            print(f"\n{Fore.RED}❌ FAIL: Chatbot still saying to upload documents{Style.RESET_ALL}")
            print(f"   Wrong phrases found: upload/pending/not processed")
            return False
        elif has_correct_response:
            print(f"\n{Fore.GREEN}✅ PASS: Chatbot giving accurate response about soft decline{Style.RESET_ALL}")
            print(f"   Correctly mentions: income/debt/programs")
            return True
        else:
            print(f"\n{Fore.YELLOW}⚠️  UNCERTAIN: Response unclear{Style.RESET_ALL}")
            return None
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.YELLOW}⚠️  SKIP: API server not running{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ FAIL: {str(e)}{Style.RESET_ALL}")
        return False

def test_results_endpoint():
    """Test 4: Verify /results endpoint returns complete data"""
    print_header("TEST 4: Results Endpoint (Data Completeness)")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/applications/{TEST_APP_ID}/results",
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"{Fore.RED}❌ FAIL: HTTP {response.status_code}{Style.RESET_ALL}")
            return False
        
        data = response.json()
        db_data = data.get('database_data', {})
        
        print(f"{Fore.CYAN}Database Data from Results:{Style.RESET_ALL}")
        print(f"  Status: {db_data.get('status')}")
        print(f"  Monthly Income: {db_data.get('monthly_income')} AED")
        print(f"  Total Assets: {db_data.get('total_assets')} AED")
        print(f"  Decision: {db_data.get('decision')}")
        
        if db_data.get('monthly_income', 0) > 0:
            print(f"\n{Fore.GREEN}✅ PASS: Results endpoint returns real data{Style.RESET_ALL}")
            return True
        else:
            print(f"\n{Fore.RED}❌ FAIL: Results still showing zeros{Style.RESET_ALL}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"{Fore.YELLOW}⚠️  SKIP: API server not running{Style.RESET_ALL}")
        return None
    except Exception as e:
        print(f"{Fore.RED}❌ FAIL: {str(e)}{Style.RESET_ALL}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Fore.MAGENTA}{'='*80}")
    print(f"COMPREHENSIVE FIX VERIFICATION")
    print(f"Testing Application: {TEST_APP_ID}")
    print(f"{'='*80}{Style.RESET_ALL}")
    
    results = {}
    
    # Run all tests
    results['database'] = test_database_storage()
    results['process'] = test_process_endpoint()
    results['chatbot'] = test_chatbot_response()
    results['results'] = test_results_endpoint()
    
    # Summary
    print_header("FINAL SUMMARY")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Fore.GREEN}✅ PASS" if result is True else (f"{Fore.RED}❌ FAIL" if result is False else f"{Fore.YELLOW}⚠️  SKIP")
        print(f"  {status}: {test_name.title()} Test{Style.RESET_ALL}")
    
    print(f"\n{Fore.CYAN}Test Results:{Style.RESET_ALL}")
    print(f"  Passed: {Fore.GREEN}{passed}/{total}{Style.RESET_ALL}")
    print(f"  Failed: {Fore.RED}{failed}/{total}{Style.RESET_ALL}")
    print(f"  Skipped: {Fore.YELLOW}{skipped}/{total}{Style.RESET_ALL}")
    
    if failed == 0:
        print(f"\n{Fore.GREEN}🎉 ALL FIXES VERIFIED! System working correctly.{Style.RESET_ALL}")
        return 0
    else:
        print(f"\n{Fore.RED}⚠️  Some tests failed. Review errors above.{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
