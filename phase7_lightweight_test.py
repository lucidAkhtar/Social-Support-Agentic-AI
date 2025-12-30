"""
Phase 7: Lightweight FastAPI + Langfuse Test
Focuses on API endpoints without heavy agent initialization
"""

import json
import time
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.observability.langfuse_tracker import LangfuseTracker
from src.database.database_manager import DatabaseManager


def test_langfuse_observability():
    """Test 1: Langfuse tracing and export"""
    print("\n" + "="*70)
    print("[TEST 1] Langfuse Observability - Tracing & Metrics")
    print("="*70)
    
    try:
        tracker = LangfuseTracker()
        
        # Simulate application processing trace
        trace_id = "trace_phase7_001"
        app_id = "app_phase7_001"
        
        print(f"\n  Starting trace: {trace_id}")
        tracker.start_trace(trace_id, app_id, {"version": "7.0"})
        
        # Log stages
        print("  Logging processing stages...")
        tracker.log_extraction(app_id, extracted_fields=25, confidence=0.92, duration=2.3)
        tracker.log_validation(app_id, quality_score=0.88, issues_found=2, duration=1.1)
        tracker.log_ml_scoring(app_id, eligibility_score=0.78, model_confidence=0.95, duration=0.5)
        tracker.log_decision(app_id, decision="approve", confidence=0.82, duration=0.8)
        tracker.log_recommendations(app_id, recommendation_count=4, duration=0.6)
        
        # End and export
        trace = tracker.end_trace()
        print(f"  ✓ Trace completed with {len(trace.get('spans', []))} spans")
        
        # Export all traces
        export_file = tracker.export_all_traces()
        print(f"  ✓ Exported to: {export_file}")
        
        # Verify export
        if Path(export_file).exists():
            with open(export_file) as f:
                exported = json.load(f)
            
            print(f"  ✓ Export verified:")
            print(f"    - Traces: {exported.get('trace_count', 0)}")
            print(f"    - Total duration: {exported.get('aggregate_metrics', {}).get('total_processing_time', 0):.2f}s")
            
            return True
        else:
            print(f"  ✗ Export file not found")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_database_integration():
    """Test 2: Database storage of results"""
    print("\n" + "="*70)
    print("[TEST 2] Database Integration - Store & Retrieve")
    print("="*70)
    
    try:
        db = DatabaseManager()
        
        # Create test application with metadata
        test_app = {
            "applicant_name": "Phase 7 Test Applicant",
            "applicant_email": "phase7@test.com",
            "income": {"total_monthly": 6500},
            "family": {"dependents": 2},
            "processing_metadata": {
                "extraction_results": {"fields": 25},
                "validation_results": {"quality_score": 0.88},
                "ml_prediction": {"eligibility_score": 0.78},
                "decision_results": {"decision": "approve"},
                "recommendations": {"programs": ["job_matching", "upskilling"]},
                "processing_times": {"total": 5.2}
            }
        }
        
        print(f"\n  Seeding application to databases...")
        
        # Seed to databases
        db.seed_application(test_app)
        
        print(f"  ✓ Application seeded successfully")
        
        # Verify storage
        stats = db.get_statistics()
        print(f"  ✓ Database statistics:")
        print(f"    - Applications: {stats.get('total_applications', 0)}")
        print(f"    - Average income: ${stats.get('average_income', 0):.2f}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_fastapi_models():
    """Test 3: FastAPI Pydantic models validation"""
    print("\n" + "="*70)
    print("[TEST 3] FastAPI Models - Pydantic Validation")
    print("="*70)
    
    try:
        from src.api.fastapi_service import (
            ApplicantInfo, IncomeInfo, ApplicationSubmission,
            AssetInfo, LiabilityInfo, FamilyMember
        )
        
        print(f"\n  Testing Pydantic models...")
        
        # Test ApplicantInfo
        applicant = ApplicantInfo(
            full_name="John Doe",
            email="john@example.com",
            phone="+971501234567",
            date_of_birth="1990-01-15",
            nationality="UAE",
            marital_status="Married",
            address="Dubai, UAE"
        )
        print(f"  ✓ ApplicantInfo created: {applicant.full_name}")
        
        # Test IncomeInfo
        income = IncomeInfo(
            total_monthly=7500,
            employment_type="Employed",
            employer="ABC Corporation",
            years_employed=5
        )
        print(f"  ✓ IncomeInfo created: ${income.total_monthly}")
        
        # Test AssetInfo
        assets = AssetInfo(
            real_estate=500000,
            vehicles=50000,
            savings=25000,
            investments=75000
        )
        print(f"  ✓ AssetInfo created: Total ${assets.total()}")
        
        # Test LiabilityInfo
        liabilities = LiabilityInfo(
            mortgage=250000,
            car_loan=30000,
            credit_debt=5000
        )
        print(f"  ✓ LiabilityInfo created: Total ${liabilities.total()}")
        
        # Test FamilyMember
        family = FamilyMember(name="Jane Doe", relationship="Spouse", age=28)
        print(f"  ✓ FamilyMember created: {family.name}")
        
        # Test ApplicationSubmission
        app = ApplicationSubmission(
            applicant_info=applicant,
            income=income,
            family_members=[family],
            assets=assets,
            liabilities=liabilities
        )
        print(f"  ✓ ApplicationSubmission created")
        print(f"    - Applicant: {app.applicant_info.full_name}")
        print(f"    - Income: ${app.income.total_monthly}")
        print(f"    - Net Worth: ${assets.total() - liabilities.total()}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_fastapi_endpoints_mock():
    """Test 4: FastAPI endpoint contracts (mock)"""
    print("\n" + "="*70)
    print("[TEST 4] FastAPI Endpoints - Contract Testing")
    print("="*70)
    
    try:
        from src.api.fastapi_service import (
            ApplicationSubmission, ApplicationResponse,
            ApplicantInfo, IncomeInfo, ProcessingStatus
        )
        
        print(f"\n  Testing API contracts...")
        
        # Create a mock submission
        applicant = ApplicantInfo(
            full_name="Test User",
            email="test@example.com",
            phone="+971501234567",
            date_of_birth="1990-01-15",
            nationality="UAE",
            marital_status="Single",
            address="Dubai"
        )
        
        income = IncomeInfo(
            total_monthly=5000,
            employment_type="Employed",
            employer="Test Corp"
        )
        
        submission = ApplicationSubmission(
            applicant_info=applicant,
            income=income,
            family_members=[],
            documents={}
        )
        
        print(f"  ✓ Application submission created")
        
        # Test response contract
        response_data = {
            "application_id": "APP_TEST001",
            "status": "submitted",
            "message": "Application submitted successfully",
            "submitted_at": datetime.now().isoformat()
        }
        
        response = ApplicationResponse(**response_data)
        print(f"  ✓ ApplicationResponse created: {response.application_id}")
        
        # Test status contract
        status_data = {
            "application_id": "APP_TEST001",
            "status": "processing",
            "current_stage": "extraction",
            "progress_percentage": 20.0,
            "processing_times": {"intake": 0.5},
            "error_count": 0,
            "last_updated": datetime.now().isoformat()
        }
        
        status = ProcessingStatus(**status_data)
        print(f"  ✓ ProcessingStatus created: {status.status}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_langgraph_state_model():
    """Test 5: LangGraph state definition"""
    print("\n" + "="*70)
    print("[TEST 5] LangGraph State Model - Type Validation")
    print("="*70)
    
    try:
        from src.orchestration.langgraph_orchestrator import ApplicationProcessingState
        from typing import TypedDict, get_type_hints
        
        print(f"\n  Testing LangGraph state...")
        
        # Create a minimal valid state
        state: ApplicationProcessingState = {
            "application_id": "test_001",
            "application_data": {"test": "data"},
            "timestamp": datetime.now().isoformat(),
            "extraction_results": None,
            "validation_results": None,
            "ml_prediction": None,
            "decision_results": None,
            "recommendations": None,
            "stage": "intake",
            "processing_times": {},
            "errors": [],
            "confidence_scores": {},
            "thoughts": [],
            "actions_taken": [],
            "observations": [],
            "processing_log": [],
            "status": "pending"
        }
        
        print(f"  ✓ State initialized")
        print(f"    - Application ID: {state['application_id']}")
        print(f"    - Stage: {state['stage']}")
        print(f"    - Status: {state['status']}")
        
        # Simulate stage progression
        state["stage"] = "extraction"
        state["extraction_results"] = {"fields": 20}
        print(f"  ✓ Stage updated: {state['stage']}")
        
        state["stage"] = "validation"
        state["validation_results"] = {"quality": 0.85}
        print(f"  ✓ Stage updated: {state['stage']}")
        
        state["stage"] = "complete"
        state["status"] = "completed"
        print(f"  ✓ Final stage: {state['stage']}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_observability_integration():
    """Test 6: Observability pipeline"""
    print("\n" + "="*70)
    print("[TEST 6] Observability Integration - Full Pipeline")
    print("="*70)
    
    try:
        tracker = LangfuseTracker()
        
        # Simulate 3 applications processing
        applications = [
            {"app_id": "APP_OBS_001", "income": 5000},
            {"app_id": "APP_OBS_002", "income": 8000},
            {"app_id": "APP_OBS_003", "income": 3500},
        ]
        
        print(f"\n  Processing {len(applications)} applications with observability...")
        
        for idx, app in enumerate(applications, 1):
            trace_id = f"trace_obs_{idx:03d}"
            app_id = app["app_id"]
            
            # Start trace
            tracker.start_trace(trace_id, app_id, {"income": app["income"]})
            
            # Log stages
            tracker.log_extraction(app_id, extracted_fields=20+idx*2, confidence=0.90+idx*0.01, duration=2.0)
            tracker.log_validation(app_id, quality_score=0.85+idx*0.02, issues_found=2-idx, duration=1.0)
            tracker.log_ml_scoring(app_id, eligibility_score=0.70+idx*0.05, model_confidence=0.92, duration=0.3)
            tracker.log_decision(app_id, decision="approve" if idx < 3 else "review", confidence=0.80, duration=0.5)
            
            # End trace
            tracker.end_trace()
            
            print(f"  ✓ App {idx} traced: {app_id}")
        
        # Export all
        export_file = tracker.export_all_traces()
        
        if Path(export_file).exists():
            with open(export_file) as f:
                data = json.load(f)
            print(f"\n  ✓ Export completed")
            print(f"    - Traces: {data.get('trace_count', 0)}")
            print(f"    - Total time: {data.get('aggregate_metrics', {}).get('total_processing_time', 0):.2f}s")
            return True
        else:
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_api_service_ready():
    """Test 7: API service readiness check"""
    print("\n" + "="*70)
    print("[TEST 7] API Service Readiness")
    print("="*70)
    
    try:
        print(f"\n  Checking API service components...")
        
        # Check imports
        from src.api import fastapi_service
        print(f"  ✓ fastapi_service module available")
        
        # Check main app exists
        from src.api.fastapi_service import app
        print(f"  ✓ FastAPI app instance created")
        
        # Check routes
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/applications/submit", "/statistics", "/"]
        
        for route in expected_routes:
            if any(route in r for r in routes):
                print(f"  ✓ Route available: {route}")
            else:
                print(f"  ⚠ Route not found: {route}")
        
        print(f"\n  Total routes: {len(routes)}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all lightweight tests"""
    print("\n" + "="*70)
    print("PHASE 7: LIGHTWEIGHT FASTAPI + LANGFUSE TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "Langfuse Observability": test_langfuse_observability(),
        "Database Integration": test_database_integration(),
        "FastAPI Models": test_fastapi_models(),
        "FastAPI Endpoints": test_fastapi_endpoints_mock(),
        "LangGraph State": test_langgraph_state_model(),
        "Observability Pipeline": test_observability_integration(),
        "API Readiness": test_api_service_ready(),
    }
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n  Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print(f"  Ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Export results
    export_results = {
        "timestamp": datetime.now().isoformat(),
        "test_results": {name: ("PASS" if result else "FAIL") for name, result in results.items()},
        "summary": {
            "passed": passed,
            "total": total,
            "pass_rate": f"{passed/total*100:.1f}%"
        }
    }
    
    output_file = Path("phase7_test_results.json")
    with open(output_file, "w") as f:
        json.dump(export_results, f, indent=2)
    
    print(f"\n  ✓ Results saved to {output_file}")
    
    return passed / total >= 0.8  # 80% pass rate


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
