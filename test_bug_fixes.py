#!/usr/bin/env python3
"""
Comprehensive Test Suite for Bug Fixes
Tests all 3 fixed endpoints + RAG chatbot improvements

Run: python test_bug_fixes.py
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_success(msg: str):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg: str):
    print(f"{RED}✗ {msg}{RESET}")

def print_info(msg: str):
    print(f"{BLUE}ℹ {msg}{RESET}")

def print_warning(msg: str):
    print(f"{YELLOW}⚠ {msg}{RESET}")

def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"{BLUE}{title.center(60)}{RESET}")
    print(f"{'='*60}\n")

def test_results_endpoint():
    """Test /api/applications/{id}/results endpoint"""
    print_section("TEST 1: Results Endpoint")
    
    test_apps = [
        "APP-000017",  # Approved
        "APP-000009",  # Conditional
        "APP-000004",  # Declined
        "APP-999999"   # Non-existent
    ]
    
    for app_id in test_apps:
        try:
            print_info(f"Testing {app_id}...")
            response = requests.get(f"{BASE_URL}/api/applications/{app_id}/results")
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"{app_id}: SUCCESS")
                print(f"  Status: {data.get('current_stage', 'N/A')}")
                
                if 'database_data' in data:
                    db_data = data['database_data']
                    print(f"  Name: {db_data.get('applicant_name', 'N/A')}")
                    print(f"  Decision: {db_data.get('decision', 'N/A')}")
                    print(f"  Score: {db_data.get('policy_score', 'N/A')}")
                    print(f"  Support: {db_data.get('support_amount', 0)} AED")
                
            elif response.status_code == 404:
                print_warning(f"{app_id}: Not found (expected for non-existent)")
                print(f"  Message: {response.json().get('detail', 'N/A')}")
                
            else:
                print_error(f"{app_id}: Unexpected status {response.status_code}")
                
        except Exception as e:
            print_error(f"{app_id}: Exception - {str(e)}")
    
    print()

def test_simulate_endpoint():
    """Test /api/applications/{id}/simulate endpoint"""
    print_section("TEST 2: Simulate Endpoint")
    
    test_cases = [
        {
            "app_id": "APP-000017",
            "changes": {"monthly_income": 10000},
            "description": "Increase income for approved app"
        },
        {
            "app_id": "APP-000009",
            "changes": {"credit_score": 750},
            "description": "Improve credit score for conditional app"
        },
        {
            "app_id": "APP-000004",
            "changes": {"employment_status": "Government Employee"},
            "description": "Change employment for declined app"
        }
    ]
    
    for test in test_cases:
        try:
            print_info(f"Testing: {test['description']}")
            
            payload = {
                "application_id": test['app_id'],
                "changes": test['changes']
            }
            
            response = requests.post(
                f"{BASE_URL}/api/applications/{test['app_id']}/simulate",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"{test['app_id']}: SUCCESS")
                print(f"  Simulation response: {data.get('response', 'N/A')[:100]}...")
                
            elif response.status_code == 400:
                print_warning(f"{test['app_id']}: Not processed yet (expected)")
                print(f"  Message: {response.json().get('detail', 'N/A')}")
                
            elif response.status_code == 404:
                print_error(f"{test['app_id']}: Not found")
                print(f"  Message: {response.json().get('detail', 'N/A')}")
                
            else:
                print_error(f"{test['app_id']}: Unexpected status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                
        except Exception as e:
            print_error(f"{test['app_id']}: Exception - {str(e)}")
    
    print()

def test_chat_endpoint():
    """Test /api/applications/{id}/chat endpoint with RAG improvements"""
    print_section("TEST 3: Chat Endpoint (RAG Improvements)")
    
    test_queries = [
        {
            "app_id": "APP-000017",
            "query": "Why was my application approved?",
            "query_type": "explanation",
            "expected_keywords": ["approved", "income", "score", "support"]
        },
        {
            "app_id": "APP-000009",
            "query": "How can I improve my application?",
            "query_type": "improvement",
            "expected_keywords": ["improve", "credit", "income", "employment"]
        },
        {
            "app_id": "APP-000004",
            "query": "What is my current status?",
            "query_type": "status",
            "expected_keywords": ["status", "decision", "application"]
        },
        {
            "app_id": "APP-000017",
            "query": "Tell me about my financial situation",
            "query_type": "general",
            "expected_keywords": ["income", "expenses", "AED", "financial"]
        }
    ]
    
    for test in test_queries:
        try:
            print_info(f"Testing: '{test['query']}' for {test['app_id']}")
            
            payload = {
                "application_id": test['app_id'],
                "query": test['query'],
                "query_type": test['query_type']
            }
            
            response = requests.post(
                f"{BASE_URL}/api/applications/{test['app_id']}/chat",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                response_text = data.get('response', '')
                
                # Check if response contains expected keywords
                keywords_found = [kw for kw in test['expected_keywords'] 
                                 if kw.lower() in response_text.lower()]
                
                if len(keywords_found) >= 2:  # At least 2 keywords should be present
                    print_success(f"{test['app_id']}: SUCCESS - Context-aware response")
                    print(f"  Keywords found: {', '.join(keywords_found)}")
                    print(f"  Response preview: {response_text[:150]}...")
                else:
                    print_warning(f"{test['app_id']}: Response may be generic")
                    print(f"  Keywords found: {', '.join(keywords_found) if keywords_found else 'None'}")
                    print(f"  Response: {response_text[:200]}...")
                
            elif response.status_code == 404:
                print_error(f"{test['app_id']}: Not found")
                print(f"  Message: {response.json().get('detail', 'N/A')}")
                
            else:
                print_error(f"{test['app_id']}: Unexpected status {response.status_code}")
                print(f"  Response: {response.text[:200]}")
                
        except Exception as e:
            print_error(f"{test['app_id']}: Exception - {str(e)}")
    
    print()

def test_health_check():
    """Test health endpoint to ensure server is running"""
    print_section("TEST 0: Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        
        if response.status_code == 200:
            data = response.json()
            print_success("Server is healthy")
            print(f"  Status: {data.get('status', 'N/A')}")
            
            if 'databases' in data:
                for db_name, db_status in data['databases'].items():
                    status = db_status.get('status', 'unknown')
                    if status == 'healthy':
                        print_success(f"  {db_name}: {status}")
                    else:
                        print_error(f"  {db_name}: {status}")
        else:
            print_error(f"Health check failed: {response.status_code}")
            
    except requests.ConnectionError:
        print_error("Cannot connect to server. Is it running?")
        print_info("Start server with: uvicorn src.api.main:app --reload")
        return False
    except Exception as e:
        print_error(f"Health check exception: {str(e)}")
        return False
    
    print()
    return True

def test_sample_applications():
    """Display sample applications for manual testing"""
    print_section("Sample Applications for Manual Testing")
    
    samples = {
        "APPROVED": [
            {"id": "APP-000017", "name": "Anwar Al Shehhi", "score": 80.0, "support": 5000},
            {"id": "APP-000011", "name": "Reem Al Awani", "score": 75.0, "support": 5000},
            {"id": "APP-000014", "name": "Noura Al Mazroui", "score": 75.0, "support": 5000}
        ],
        "CONDITIONAL (Soft Decline)": [
            {"id": "APP-000009", "name": "Jassem Al Memari", "score": 40.0, "support": 1500},
            {"id": "APP-000027", "name": "Rashid Al Shehhi", "score": 35.0, "support": 1500},
            {"id": "APP-000002", "name": "Kamal Al Shehhi", "score": 30.0, "support": 1500}
        ],
        "DECLINED (Hard Decline)": [
            {"id": "APP-000004", "name": "Abdullah Al Kalbani", "score": 25.0, "support": 0},
            {"id": "APP-000023", "name": "Maha Al Ameri", "score": 25.0, "support": 0},
            {"id": "APP-000029", "name": "Mona Al Kalbani", "score": 25.0, "support": 0}
        ]
    }
    
    for category, apps in samples.items():
        print(f"\n{YELLOW}{category}{RESET}")
        for app in apps:
            print(f"  {app['id']}: {app['name']}")
            print(f"    Score: {app['score']} | Support: {app['support']} AED")
    
    print()

def main():
    """Run all tests"""
    print(f"\n{BLUE}{'='*60}")
    print(f"  COMPREHENSIVE TEST SUITE - Bug Fixes Verification")
    print(f"{'='*60}{RESET}\n")
    
    # Test 0: Health check
    if not test_health_check():
        print_error("Server is not running. Please start it first.")
        return
    
    # Test 1: Results endpoint
    test_results_endpoint()
    
    # Test 2: Simulate endpoint
    test_simulate_endpoint()
    
    # Test 3: Chat endpoint (RAG improvements)
    test_chat_endpoint()
    
    # Display sample applications
    test_sample_applications()
    
    # Final summary
    print_section("Test Suite Complete")
    print_info("Review the results above to verify all fixes are working correctly.")
    print_info("For manual testing in Swagger UI, use the sample application IDs listed above.")
    print_info(f"\nSwagger UI: {BASE_URL}/docs")
    print()

if __name__ == "__main__":
    main()
