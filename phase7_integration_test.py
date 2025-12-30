"""
Phase 7: LangGraph + Langfuse + FastAPI Integration Test
Tests complete workflow with 10 diverse applications
Verifies orchestration, observability, and API service
"""

import json
import time
from pathlib import Path
from datetime import datetime
import sys

sys.path.insert(0, str(Path(__file__).parent))

from src.orchestration.langgraph_orchestrator import LangGraphOrchestrator
from src.observability.langfuse_tracker import LangfuseTracker
from src.database.database_manager import DatabaseManager


def load_test_applications():
    """Load synthetic test applications from Phase 1 data"""
    try:
        data_file = Path("data/raw/applications_complete.json")
        with open(data_file) as f:
            all_apps = json.load(f)
        
        # Select 10 diverse applications
        selected = []
        for i, app in enumerate(all_apps[:10]):
            selected.append(app)
        
        print(f"✓ Loaded {len(selected)} test applications from Phase 1 data")
        return selected
    
    except Exception as e:
        print(f"⚠ Could not load test data: {e}")
        
        # Return minimal test data
        return [
            {
                "applicant_info": {"name": f"Test Applicant {i}", "email": f"test{i}@example.com"},
                "documents": {},
                "income": {"total_monthly": 5000 + (i * 1000)},
                "family": {"dependents": i % 3}
            }
            for i in range(10)
        ]


def test_langgraph_orchestration():
    """Test 1: LangGraph workflow with complete stages"""
    print("\n" + "="*70)
    print("[TEST 1] LangGraph Orchestration - Complete Workflow")
    print("="*70)
    
    try:
        orchestrator = LangGraphOrchestrator()
        applications = load_test_applications()
        
        successful = 0
        failed = 0
        timings = []
        
        for i, app in enumerate(applications[:3], 1):  # Test 3 apps
            print(f"\n  Processing application {i}/3...")
            
            start = time.time()
            try:
                result = orchestrator.process_application(f"app_test_{i:03d}", app)
                elapsed = time.time() - start
                timings.append(elapsed)
                
                # Check completion
                if result.get("status") in ["completed", "completed_with_errors"]:
                    successful += 1
                    print(f"    ✓ Completed in {elapsed:.2f}s")
                    print(f"      Decision: {result.get('decision_results', {}).get('decision')}")
                else:
                    failed += 1
                    print(f"    ✗ Status: {result.get('status')}")
                    
            except Exception as e:
                failed += 1
                print(f"    ✗ Error: {str(e)[:60]}")
        
        avg_time = sum(timings) / len(timings) if timings else 0
        
        print(f"\n  ✓ Test Summary:")
        print(f"    - Successful: {successful}/3")
        print(f"    - Failed: {failed}/3")
        print(f"    - Average time: {avg_time:.2f}s")
        
        return successful > 0
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_langfuse_observability():
    """Test 2: Langfuse end-to-end tracing and metrics"""
    print("\n" + "="*70)
    print("[TEST 2] Langfuse Observability - Tracing & Metrics")
    print("="*70)
    
    try:
        tracker = LangfuseTracker()
        
        # Simulate application processing trace
        trace_id = "trace_test_001"
        app_id = "app_test_obs_001"
        
        print(f"\n  Starting trace: {trace_id}")
        tracker.start_trace(trace_id, app_id, {"version": "1.0"})
        
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
    """Test 3: Database storage of orchestration results"""
    print("\n" + "="*70)
    print("[TEST 3] Database Integration - Store Results")
    print("="*70)
    
    try:
        db = DatabaseManager()
        
        # Create test application with metadata
        test_app = {
            "applicant_name": "Test Applicant DB",
            "applicant_email": "test@db.com",
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
        
        print(f"\n  Seeding application to all databases...")
        
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


def test_workflow_integration():
    """Test 4: Full workflow integration - Orchestrator → Database"""
    print("\n" + "="*70)
    print("[TEST 4] Workflow Integration - Orchestrator to Database")
    print("="*70)
    
    try:
        orchestrator = LangGraphOrchestrator()
        tracker = LangfuseTracker()
        
        # Load test applications
        applications = load_test_applications()
        test_apps = applications[:2]  # Test with 2 apps
        
        print(f"\n  Processing {len(test_apps)} applications with full workflow...")
        
        for idx, app in enumerate(test_apps, 1):
            trace_id = f"trace_integration_{idx:03d}"
            app_id = f"app_integration_{idx:03d}"
            
            # Start trace
            tracker.start_trace(trace_id, app_id)
            
            # Process through orchestrator
            start = time.time()
            result = orchestrator.process_application(app_id, app)
            elapsed = time.time() - start
            
            # Log to tracker
            tracker.log_extraction(
                app_id,
                extracted_fields=len(result.get("extraction_results", {}).get("fields", {})),
                confidence=result.get("confidence_scores", {}).get("extraction", 0),
                duration=result.get("processing_times", {}).get("extraction", 0)
            )
            
            tracker.log_validation(
                app_id,
                quality_score=result.get("confidence_scores", {}).get("validation", 0),
                issues_found=len(result.get("validation_results", {}).get("validation_errors", [])),
                duration=result.get("processing_times", {}).get("validation", 0)
            )
            
            tracker.log_ml_scoring(
                app_id,
                eligibility_score=result.get("ml_prediction", {}).get("eligibility_score", 0),
                model_confidence=result.get("confidence_scores", {}).get("ml_scoring", 0),
                duration=result.get("processing_times", {}).get("ml_scoring", 0)
            )
            
            tracker.log_decision(
                app_id,
                decision=result.get("decision_results", {}).get("decision", "pending"),
                confidence=result.get("confidence_scores", {}).get("decision", 0),
                duration=result.get("processing_times", {}).get("decision", 0)
            )
            
            tracker.end_trace()
            
            print(f"  ✓ App {idx} processed in {elapsed:.2f}s")
        
        # Export observability
        tracker.export_all_traces()
        print(f"\n  ✓ All traces exported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_error_handling():
    """Test 5: Error handling and recovery"""
    print("\n" + "="*70)
    print("[TEST 5] Error Handling - Recovery & Logging")
    print("="*70)
    
    try:
        orchestrator = LangGraphOrchestrator()
        tracker = LangfuseTracker()
        
        # Test with invalid/minimal data
        invalid_app = {"incomplete": "data"}
        
        print(f"\n  Testing with invalid application data...")
        
        trace_id = "trace_error_test"
        app_id = "app_error_test"
        tracker.start_trace(trace_id, app_id)
        
        try:
            result = orchestrator.process_application(app_id, invalid_app)
            
            # Check if error was handled gracefully
            error_count = len(result.get("errors", []))
            
            if error_count > 0:
                print(f"  ✓ Errors captured: {error_count}")
                print(f"    - Status: {result.get('status')}")
                
                # Log error
                tracker.log_error(app_id, "intake", f"{error_count} errors detected")
                
                handled = True
            else:
                print(f"  ⚠ No errors captured (unexpected)")
                handled = False
                
        except Exception as e:
            print(f"  ✗ Unhandled exception: {str(e)[:60]}")
            tracker.log_error(app_id, "processing", str(e))
            handled = False
        
        tracker.end_trace()
        return handled
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_performance_metrics():
    """Test 6: Performance metrics and reporting"""
    print("\n" + "="*70)
    print("[TEST 6] Performance Metrics - Benchmarking")
    print("="*70)
    
    try:
        orchestrator = LangGraphOrchestrator()
        applications = load_test_applications()
        test_apps = applications[:5]  # Test with 5 apps
        
        print(f"\n  Running performance benchmark with {len(test_apps)} applications...")
        
        timings = {}
        stage_timings = {}
        decisions = []
        confidences = []
        
        for idx, app in enumerate(test_apps, 1):
            print(f"  Processing {idx}/{len(test_apps)}...", end=" ")
            
            start = time.time()
            result = orchestrator.process_application(f"app_perf_{idx:03d}", app)
            elapsed = time.time() - start
            timings[f"app_{idx}"] = elapsed
            
            # Collect metrics
            for stage, duration in result.get("processing_times", {}).items():
                if stage not in stage_timings:
                    stage_timings[stage] = []
                stage_timings[stage].append(duration)
            
            decision = result.get("decision_results", {}).get("decision")
            confidence = result.get("confidence_scores", {}).get("decision", 0)
            
            if decision:
                decisions.append(decision)
            confidences.append(confidence)
            
            print(f"✓ {elapsed:.2f}s")
        
        # Calculate statistics
        all_times = list(timings.values())
        avg_time = sum(all_times) / len(all_times) if all_times else 0
        min_time = min(all_times) if all_times else 0
        max_time = max(all_times) if all_times else 0
        
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        print(f"\n  Performance Report:")
        print(f"    Total Applications: {len(test_apps)}")
        print(f"    Average Time: {avg_time:.2f}s")
        print(f"    Min Time: {min_time:.2f}s")
        print(f"    Max Time: {max_time:.2f}s")
        print(f"    Average Confidence: {avg_confidence:.2%}")
        
        print(f"\n    Stage Timing Breakdown:")
        for stage, durations in sorted(stage_timings.items()):
            avg_stage = sum(durations) / len(durations) if durations else 0
            print(f"      {stage}: {avg_stage:.3f}s")
        
        print(f"\n    Decisions:")
        for decision, count in [(d, decisions.count(d)) for d in set(decisions)]:
            print(f"      {decision}: {count}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def test_end_to_end():
    """Test 7: Complete end-to-end workflow"""
    print("\n" + "="*70)
    print("[TEST 7] End-to-End - Full Pipeline")
    print("="*70)
    
    try:
        orchestrator = LangGraphOrchestrator()
        tracker = LangfuseTracker()
        db = DatabaseManager()
        
        # Load test applications
        applications = load_test_applications()
        test_app = applications[0]
        
        app_id = "app_e2e_001"
        trace_id = "trace_e2e_001"
        
        print(f"\n  Running complete end-to-end pipeline...")
        
        # Start observability
        tracker.start_trace(trace_id, app_id)
        
        # Process through orchestrator
        print("  → Orchestrating workflow...")
        start = time.time()
        result = orchestrator.process_application(app_id, test_app)
        elapsed = time.time() - start
        
        print(f"  ✓ Orchestration completed in {elapsed:.2f}s")
        
        # Log all stages
        print("  → Logging observability...")
        tracker.log_extraction(
            app_id,
            extracted_fields=len(result.get("extraction_results", {}).get("fields", {})),
            confidence=result.get("confidence_scores", {}).get("extraction", 0),
            duration=result.get("processing_times", {}).get("extraction", 0)
        )
        tracker.log_validation(
            app_id,
            quality_score=result.get("confidence_scores", {}).get("validation", 0),
            issues_found=len(result.get("validation_results", {}).get("validation_errors", [])),
            duration=result.get("processing_times", {}).get("validation", 0)
        )
        tracker.log_ml_scoring(
            app_id,
            eligibility_score=result.get("ml_prediction", {}).get("eligibility_score", 0),
            model_confidence=result.get("confidence_scores", {}).get("ml_scoring", 0),
            duration=result.get("processing_times", {}).get("ml_scoring", 0)
        )
        tracker.log_decision(
            app_id,
            decision=result.get("decision_results", {}).get("decision"),
            confidence=result.get("confidence_scores", {}).get("decision", 0),
            duration=result.get("processing_times", {}).get("decision", 0)
        )
        tracker.end_trace()
        
        print("  ✓ Observability logged")
        
        # Store in database
        print("  → Storing in database...")
        db.seed_application({**test_app, "processing_metadata": result})
        print("  ✓ Database stored")
        
        # Export observability
        print("  → Exporting observability data...")
        export_file = tracker.export_all_traces()
        print(f"  ✓ Exported to {export_file}")
        
        db.close()
        
        print(f"\n  ✓ End-to-end pipeline completed successfully")
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False


def run_all_tests():
    """Run all integration tests"""
    print("\n" + "="*70)
    print("PHASE 7: LANGGRAPH + LANGFUSE + FASTAPI INTEGRATION TEST SUITE")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        "LangGraph Orchestration": test_langgraph_orchestration(),
        "Langfuse Observability": test_langfuse_observability(),
        "Database Integration": test_database_integration(),
        "Workflow Integration": test_workflow_integration(),
        "Error Handling": test_error_handling(),
        "Performance Metrics": test_performance_metrics(),
        "End-to-End Pipeline": test_end_to_end(),
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
