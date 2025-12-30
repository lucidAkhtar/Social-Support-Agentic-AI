"""
Comprehensive API Test Suite
Tests all FastAPI endpoints before deployment.
"""

import requests
import json
import time
from pathlib import Path
import sys

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Test Results
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}


def log_test(test_name: str, passed: bool, message: str = ""):
    """Log test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"   {message}")
    
    if passed:
        test_results["passed"] += 1
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{test_name}: {message}")


def test_health_check():
    """Test 1: Health check endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        log_test("Health Check", True, f"Version: {data['version']}")
        return True
    except Exception as e:
        log_test("Health Check", False, str(e))
        return False


def test_create_application():
    """Test 2: Create application."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/applications/create",
            data={"applicant_name": "Test User"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "application_id" in data
        assert data["status"] == "created"
        application_id = data["application_id"]
        log_test("Create Application", True, f"ID: {application_id}")
        return application_id
    except Exception as e:
        log_test("Create Application", False, str(e))
        return None


def test_upload_documents(application_id: str):
    """Test 3: Upload documents."""
    try:
        # Create test files
        test_dir = Path("data/test_files")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create mock Emirates ID
        emirates_id_file = test_dir / "test_emirates_id.txt"
        emirates_id_file.write_text("""
        Emirates ID Document
        Name: Test User
        ID Number: 784-1990-1234567-8
        Date of Birth: 01/01/1990
        """)
        
        # Create mock resume
        resume_file = test_dir / "test_resume.txt"
        resume_file.write_text("""
        Test User - Software Engineer
        
        Experience:
        - Software Engineer at ABC Corp (2018-2024)
        - 6 years of experience
        
        Education:
        - Bachelor of Computer Science
        """)
        
        # Upload files
        files = [
            ("documents", ("emirates_id.txt", open(emirates_id_file, "rb"), "text/plain")),
            ("documents", ("resume.txt", open(resume_file, "rb"), "text/plain"))
        ]
        
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/upload",
            files=files
        )
        
        # Close files
        for _, (_, file, _) in files:
            file.close()
        
        assert response.status_code == 200
        data = response.json()
        assert data["uploaded_count"] == 2
        log_test("Upload Documents", True, f"Uploaded {data['uploaded_count']} files")
        return True
    except Exception as e:
        log_test("Upload Documents", False, str(e))
        return False


def test_get_status(application_id: str):
    """Test 4: Get application status."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/applications/{application_id}/status"
        )
        if response.status_code != 200:
            raise Exception(f"Status code: {response.status_code}, Response: {response.text}")
        assert response.status_code == 200
        data = response.json()
        assert "current_stage" in data
        assert "progress_percentage" in data
        log_test("Get Status", True, f"Stage: {data['current_stage']}")
        return True
    except Exception as e:
        log_test("Get Status", False, str(e))
        return False


def test_process_application(application_id: str):
    """Test 5: Process application through all agents."""
    try:
        print("   ⏳ Processing (this may take 30-60 seconds)...")
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/process",
            timeout=120  # 2 minute timeout
        )
        assert response.status_code == 200
        data = response.json()
        assert data["current_stage"] == "completed"
        log_test("Process Application", True, f"Stage: {data['current_stage']}")
        return True
    except Exception as e:
        log_test("Process Application", False, str(e))
        return False


def test_get_results(application_id: str):
    """Test 6: Get application results."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/applications/{application_id}/results"
        )
        assert response.status_code == 200
        data = response.json()
        assert "extracted_data" in data
        assert "validation" in data
        assert "eligibility" in data
        assert "recommendation" in data
        
        # Validate structure
        if data["extracted_data"]:
            log_test("Get Results", True, "All data extracted successfully")
        else:
            log_test("Get Results", True, "Results retrieved (no extraction yet)")
        return data
    except Exception as e:
        log_test("Get Results", False, str(e))
        return None


def test_chat_before_validation(application_id: str):
    """Test 7: Chat before validation (should be disabled)."""
    try:
        # Create fresh application
        response = requests.post(
            f"{API_BASE_URL}/api/applications/create",
            data={"applicant_name": "Chat Test User"}
        )
        new_app_id = response.json()["application_id"]
        
        # Try to chat
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{new_app_id}/chat",
            json={
                "application_id": new_app_id,
                "query": "Test query",
                "query_type": "explanation"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["chatbot_enabled"] == False
        log_test("Chat Before Validation", True, "Correctly disabled")
        return True
    except Exception as e:
        log_test("Chat Before Validation", False, str(e))
        return False


def test_chat_after_processing(application_id: str):
    """Test 8: Chat after processing (should be enabled)."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/chat",
            json={
                "application_id": application_id,
                "query": "Why was I approved or declined?",
                "query_type": "explanation"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0
        log_test("Chat After Processing", True, "Chatbot responding")
        return True
    except Exception as e:
        log_test("Chat After Processing", False, str(e))
        return False


def test_statistics():
    """Test 9: Get system statistics."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/statistics")
        assert response.status_code == 200
        data = response.json()
        assert "total_applications" in data
        assert "sqlite_stats" in data
        assert "chromadb_stats" in data
        log_test("Get Statistics", True, f"Total apps: {data['total_applications']}")
        return True
    except Exception as e:
        log_test("Get Statistics", False, str(e))
        return False


def test_error_handling():
    """Test 10: Error handling for invalid requests."""
    try:
        # Test 1: Invalid application ID
        response = requests.get(
            f"{API_BASE_URL}/api/applications/INVALID_ID/status"
        )
        assert response.status_code == 404
        
        # Test 2: Upload without application
        response = requests.post(
            f"{API_BASE_URL}/api/applications/INVALID_ID/upload",
            files=[("documents", ("test.txt", b"test", "text/plain"))]
        )
        assert response.status_code == 404
        
        log_test("Error Handling", True, "404 errors handled correctly")
        return True
    except Exception as e:
        log_test("Error Handling", False, str(e))
        return False


def run_all_tests():
    """Run all API tests in sequence."""
    print("="*80)
    print("FASTAPI COMPREHENSIVE TEST SUITE")
    print("="*80)
    print()
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=2)
        if response.status_code != 200:
            print("❌ CRITICAL: API server is not responding!")
            print("Please start the server with:")
            print("  poetry run python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000")
            sys.exit(1)
    except Exception as e:
        print("❌ CRITICAL: Cannot connect to API server!")
        print(f"Error: {e}")
        print("Please start the server with:")
        print("  poetry run python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    print("✅ API server is running\n")
    
    # Run tests
    print("Running tests...\n")
    
    # Test 1: Health check
    if not test_health_check():
        print("\n❌ Health check failed. Aborting tests.")
        return False
    
    # Test 2: Create application
    application_id = test_create_application()
    if not application_id:
        print("\n❌ Application creation failed. Aborting tests.")
        return False
    
    # Test 3: Upload documents
    if not test_upload_documents(application_id):
        print("\n⚠️  Document upload failed, continuing...")
    
    # Test 4: Get status
    test_get_status(application_id)
    
    # Test 5: Process application (LONG RUNNING)
    if not test_process_application(application_id):
        print("\n⚠️  Processing failed, continuing with remaining tests...")
    
    # Test 6: Get results
    test_get_results(application_id)
    
    # Test 7: Chat before validation
    test_chat_before_validation(application_id)
    
    # Test 8: Chat after processing
    test_chat_after_processing(application_id)
    
    # Test 9: Statistics
    test_statistics()
    
    # Test 10: Error handling
    test_error_handling()
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"📊 Total:  {test_results['passed'] + test_results['failed']}")
    
    if test_results['failed'] > 0:
        print("\n⚠️  FAILURES:")
        for error in test_results['errors']:
            print(f"  - {error}")
        print("\n❌ Some tests failed. Please fix before deployment.")
        return False
    else:
        print("\n🎉 ALL TESTS PASSED! API is ready for production.")
        return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
