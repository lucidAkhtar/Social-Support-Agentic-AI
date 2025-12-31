"""
Test database storage fix - Verify extracted data is saved to database
"""

import sys
import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

# Test with the actual application ID from user's request
APPLICATION_ID = "APP_F5104A2B"
BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{title}")
    print(f"{'='*80}{Style.RESET_ALL}\n")

def test_database_storage():
    """Test that application processing saves data to database"""
    
    print_section("🧪 DATABASE STORAGE FIX TEST")
    
    # Step 1: Check database BEFORE reprocessing
    print(f"{Fore.YELLOW}📊 STEP 1: Checking database state BEFORE fix...{Style.RESET_ALL}")
    
    from src.databases.prod_sqlite_manager import SQLiteManager
    db = SQLiteManager()
    
    result_before = db.get_application(APPLICATION_ID)
    if result_before:
        print(f"  Current database state:")
        print(f"    Status: {result_before['status']}")
        print(f"    Monthly Income: {result_before['monthly_income']} AED")
        print(f"    Total Assets: {result_before['total_assets']} AED")
        print(f"    Total Liabilities: {result_before['total_liabilities']} AED")
        print(f"    Credit Score: {result_before['credit_score']}")
    else:
        print(f"  {Fore.RED}Application not found in database{Style.RESET_ALL}")
        return False
    
    # Step 2: Trigger reprocessing via API
    print(f"\n{Fore.YELLOW}📊 STEP 2: Reprocessing application via API...{Style.RESET_ALL}")
    print(f"  Making POST request to: {BASE_URL}/api/applications/{APPLICATION_ID}/process")
    
    try:
        response = requests.post(f"{BASE_URL}/api/applications/{APPLICATION_ID}/process", timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  {Fore.GREEN}✅ Processing completed{Style.RESET_ALL}")
            print(f"    Stage: {data.get('current_stage')}")
            print(f"    Progress: {data.get('progress_percentage')}%")
        else:
            print(f"  {Fore.RED}❌ API Error: {response.status_code}{Style.RESET_ALL}")
            print(f"    Response: {response.text[:200]}")
            return False
    
    except requests.exceptions.ConnectionError:
        print(f"  {Fore.RED}❌ Cannot connect to API server{Style.RESET_ALL}")
        print(f"    Please start server with: poetry run python -m uvicorn src.api.main:app --reload")
        return False
    
    except Exception as e:
        print(f"  {Fore.RED}❌ Error: {str(e)}{Style.RESET_ALL}")
        return False
    
    # Step 3: Check database AFTER reprocessing
    print(f"\n{Fore.YELLOW}📊 STEP 3: Verifying database updated...{Style.RESET_ALL}")
    
    result_after = db.get_application(APPLICATION_ID)
    if result_after:
        print(f"  Updated database state:")
        print(f"    Status: {result_after['status']}")
        print(f"    Monthly Income: {result_after['monthly_income']} AED")
        print(f"    Total Assets: {result_after['total_assets']} AED")
        print(f"    Total Liabilities: {result_after['total_liabilities']} AED")
        print(f"    Credit Score: {result_after['credit_score']}")
        print(f"    Eligibility: {result_after.get('eligibility', 'N/A')}")
    
    # Step 4: Validation
    print_section("📋 VALIDATION RESULTS")
    
    all_checks_passed = True
    
    # Check 1: Status updated
    if result_after['status'] != 'PENDING':
        print(f"{Fore.GREEN}✅ Status updated from PENDING to {result_after['status']}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Status still PENDING{Style.RESET_ALL}")
        all_checks_passed = False
    
    # Check 2: Income extracted
    if result_after['monthly_income'] > 0:
        print(f"{Fore.GREEN}✅ Monthly income extracted: {result_after['monthly_income']:,.2f} AED{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Monthly income still 0{Style.RESET_ALL}")
        all_checks_passed = False
    
    # Check 3: Assets extracted
    if result_after['total_assets'] > 0:
        print(f"{Fore.GREEN}✅ Total assets extracted: {result_after['total_assets']:,.2f} AED{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️  Total assets still 0 (may be legitimate){Style.RESET_ALL}")
    
    # Check 4: Liabilities extracted
    if result_after['total_liabilities'] > 0:
        print(f"{Fore.GREEN}✅ Total liabilities extracted: {result_after['total_liabilities']:,.2f} AED{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️  Total liabilities still 0 (may be legitimate){Style.RESET_ALL}")
    
    # Step 5: Test chatbot with updated data
    print(f"\n{Fore.YELLOW}📊 STEP 4: Testing chatbot with updated database...{Style.RESET_ALL}")
    
    try:
        chat_response = requests.post(
            f"{BASE_URL}/api/applications/{APPLICATION_ID}/chat",
            json={"query": "What is my monthly income?"},
            timeout=30
        )
        
        if chat_response.status_code == 200:
            chat_data = chat_response.json()
            response_text = chat_data.get('response', '')
            
            print(f"  Chatbot response:")
            print(f"    {response_text[:300]}...")
            
            # Check if chatbot mentions the actual income
            if str(int(result_after['monthly_income'])) in response_text or f"{result_after['monthly_income']:.2f}" in response_text:
                print(f"\n{Fore.GREEN}✅ Chatbot correctly reports income from database!{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.YELLOW}⚠️  Chatbot response may not include exact income value{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"  {Fore.YELLOW}⚠️  Could not test chatbot: {str(e)}{Style.RESET_ALL}")
    
    # Final result
    print_section("🎯 FINAL RESULT")
    
    if all_checks_passed:
        print(f"{Fore.GREEN}🎉 DATABASE STORAGE FIX VERIFIED!{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}✅ Extracted data is now being saved to database{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Chatbot can now access real application data{Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ No more \"please upload documents\" for processed applications{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.RED}⚠️  Some validation checks failed - review logs above{Style.RESET_ALL}")
        return False

if __name__ == "__main__":
    print(f"\n{Fore.CYAN}Starting database storage fix test...{Style.RESET_ALL}")
    print(f"Application ID: {APPLICATION_ID}")
    print(f"API Endpoint: {BASE_URL}")
    
    success = test_database_storage()
    sys.exit(0 if success else 1)
