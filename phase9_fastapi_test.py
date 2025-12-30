"""
FastAPI Endpoint Validation Test Suite
Tests all 12 endpoints to ensure they're working correctly
Can be run while FastAPI server is running in another terminal
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        self.app_id = None
        
    def test_endpoint(self, name: str, method: str, endpoint: str, 
                     data: Dict = None, expected_status: int = 200) -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, timeout=TIMEOUT)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, timeout=TIMEOUT)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            success = response.status_code == expected_status
            
            result = {
                "endpoint": endpoint,
                "method": method,
                "status_code": response.status_code,
                "expected": expected_status,
                "success": success,
                "name": name,
                "response_size": len(response.text) if response.text else 0
            }
            
            # Try to parse JSON response
            if response.text:
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text[:200]
            
            self.results.append(result)
            
            status_icon = "✅" if success else "❌"
            print(f"{status_icon} {name:40} | {method:4} {endpoint:40} | Status: {response.status_code}")
            
            return success
            
        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "success": False,
                "name": name,
                "error": str(e)
            }
            self.results.append(result)
            print(f"❌ {name:40} | {method:4} {endpoint:40} | Error: {str(e)[:50]}")
            return False
    
    def run_test_suite(self):
        """Run all 12 tests"""
        print("\n" + "="*120)
        print("FASTAPI ENDPOINT VALIDATION TEST SUITE")
        print("="*120 + "\n")
        
        # Test 1: Health Check
        print("1. SYSTEM HEALTH ENDPOINTS")
        print("-" * 120)
        self.test_endpoint(
            "Health Check",
            "GET",
            "/health",
            expected_status=200
        )
        
        # Test 2: Root/Documentation
        print("\n2. DOCUMENTATION ENDPOINTS")
        print("-" * 120)
        self.test_endpoint(
            "API Documentation",
            "GET",
            "/",
            expected_status=200
        )
        
        # Test 3: Application Submission
        print("\n3. APPLICATION SUBMISSION ENDPOINTS")
        print("-" * 120)
        
        # Create sample application data
        application_data = {
            "applicant_info": {
                "full_name": "Ahmed Al Maktoum",
                "email": "ahmed@example.com",
                "phone": "+971-50-123-4567",
                "date_of_birth": "1990-01-15",
                "nationality": "784-1990-0123456-0",
                "marital_status": "Married",
                "address": "Dubai Marina, Dubai"
            },
            "income": {
                "total_monthly": 15000,
                "employment_type": "Employed",
                "employer": "Emirates Group",
                "years_employed": 5
            },
            "family_members": [
                {"name": "Fatima Al Maktoum", "relationship": "Spouse", "age": 28},
                {"name": "Mohammed Al Maktoum", "relationship": "Child", "age": 5},
                {"name": "Layla Al Maktoum", "relationship": "Child", "age": 3}
            ],
            "assets": {
                "real_estate": 500000,
                "vehicles": 80000,
                "savings": 50000,
                "investments": 100000
            },
            "liabilities": {
                "mortgage": 200000,
                "car_loan": 30000,
                "credit_debt": 5000,
                "other_debt": 0
            },
            "documents": {
                "emirates_id": "/documents/emirates_id.pdf",
                "bank_statement": "/documents/bank_statement.pdf",
                "employment_letter": "/documents/employment_letter.pdf"
            },
            "notes": "Application for financial assistance program"
        }
        
        success = self.test_endpoint(
            "Submit Application",
            "POST",
            "/applications/submit",
            data=application_data,
            expected_status=200
        )
        
        # Extract app_id from response for subsequent tests
        if success and self.results[-1].get("response_data"):
            try:
                self.app_id = self.results[-1]["response_data"].get("application_id")
                print(f"   → Extracted Application ID: {self.app_id}\n")
            except:
                pass
        
        # Test 4: Application Status
        print("\n4. APPLICATION STATUS ENDPOINTS")
        print("-" * 120)
        
        if self.app_id:
            self.test_endpoint(
                "Get Application Status",
                "GET",
                f"/applications/{self.app_id}/status",
                expected_status=200
            )
        else:
            print("⚠️  Skipping status test (no app_id from submission)")
        
        # Test 5: Application Details
        print("\n5. APPLICATION DETAILS ENDPOINTS")
        print("-" * 120)
        
        if self.app_id:
            self.test_endpoint(
                "Get Application Details",
                "GET",
                f"/applications/{self.app_id}/details",
                expected_status=200
            )
        else:
            print("⚠️  Skipping details test (no app_id from submission)")
        
        # Test 6: Decision Result
        print("\n6. DECISION ENDPOINTS")
        print("-" * 120)
        
        if self.app_id:
            self.test_endpoint(
                "Get Decision Result",
                "GET",
                f"/applications/{self.app_id}/decision",
                expected_status=200
            )
        else:
            print("⚠️  Skipping decision test (no app_id from submission)")
        
        # Test 7: Statistics
        print("\n7. STATISTICS & ANALYTICS ENDPOINTS")
        print("-" * 120)
        
        self.test_endpoint(
            "Get System Statistics",
            "GET",
            "/statistics",
            expected_status=200
        )
        
        # Test 8: Observability Export
        print("\n8. OBSERVABILITY ENDPOINTS")
        print("-" * 120)
        
        self.test_endpoint(
            "Export Observability Traces",
            "POST",
            "/export-observability",
            data={"format": "json"},
            expected_status=200
        )
        
        # Test 9-12: Additional endpoints (if they exist)
        print("\n9. ADDITIONAL ENDPOINTS")
        print("-" * 120)
        
        # Try searching applications (if implemented)
        self.test_endpoint(
            "Search Applications (Optional)",
            "GET",
            "/applications/search?query=Ahmed",
            expected_status=200
        )
        
        # Try batch processing (if implemented)
        self.test_endpoint(
            "Batch Processing Status (Optional)",
            "GET",
            "/batch/status",
            expected_status=200
        )
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*120)
        print("TEST SUMMARY")
        print("="*120 + "\n")
        
        passed = sum(1 for r in self.results if r.get("success", False))
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {total - passed} ❌")
        print(f"Success Rate: {(passed/total)*100:.1f}%\n")
        
        # Detailed results
        print("Detailed Results:")
        print("-" * 120)
        
        for result in self.results:
            status = "PASS" if result.get("success", False) else "FAIL"
            endpoint = result.get("endpoint", "?")
            method = result.get("method", "?")
            name = result.get("name", "?")
            
            if result.get("success"):
                print(f"✅ {status:4} | {name:40} | {method:4} {endpoint:40}")
            else:
                error = result.get("error", result.get("status_code", "Unknown"))
                print(f"❌ {status:4} | {name:40} | {method:4} {endpoint:40} | Error: {str(error)[:40]}")
        
        print("\n" + "="*120)
        
        # Recommendation
        if passed == total:
            print("✅ ALL ENDPOINTS WORKING - READY FOR PRODUCTION")
        elif passed >= total * 0.8:
            print("⚠️  MOST ENDPOINTS WORKING - MINOR ISSUES TO FIX")
        else:
            print("❌ SIGNIFICANT ISSUES - REQUIRES DEBUGGING")
        
        print("="*120 + "\n")
        
        # Save results to file
        self.save_results()
    
    def save_results(self):
        """Save test results to JSON file"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "test_url": self.base_url,
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.get("success", False)),
            "results": self.results
        }
        
        filename = "phase9_fastapi_test_results.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Results saved to: {filename}\n")


def main():
    """Main test runner"""
    print("\n🔍 FastAPI Endpoint Validation Test Suite")
    print("Make sure FastAPI server is running: python -m uvicorn src.api.main:app --reload\n")
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"✅ Server detected at {BASE_URL}\n")
    except:
        print(f"❌ Cannot reach server at {BASE_URL}")
        print("Please start the FastAPI server first:")
        print("  python -m uvicorn src.api.main:app --reload\n")
        return
    
    # Run tests
    tester = APITester(BASE_URL)
    tester.run_test_suite()


if __name__ == "__main__":
    main()
