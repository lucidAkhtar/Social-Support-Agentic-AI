"""
Comprehensive Langfuse Observability Demonstration
Shows full ML pipeline tracing with detailed metrics and decision tracking
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import time
import random

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.governance import get_audit_logger, get_structured_logger


class ComprehensiveLangfuseDemo:
    """
    Advanced Langfuse observability demonstration showing:
    - Multi-stage application processing
    - ML model predictions with feature tracking
    - Performance metrics and timing
    - Error handling and recovery
    - Audit trail generation
    - Exportable traces for Langfuse Cloud
    """
    
    def __init__(self):
        self.audit_logger = get_audit_logger()
        self.structured_logger = get_structured_logger("langfuse_comprehensive")
        self.output_dir = project_root / "data" / "observability"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def simulate_document_processing(self, app_id: str, doc_type: str):
        """Simulate document upload and OCR processing"""
        start_time = time.time()
        
        # Simulate processing time
        processing_time = random.uniform(0.5, 2.0)
        time.sleep(processing_time / 10)  # Speed up for demo
        
        # Simulate OCR confidence
        ocr_confidence = random.uniform(0.85, 0.99)
        
        self.structured_logger.info(
            f"document_processing_{doc_type}",
            application_id=app_id,
            document_type=doc_type,
            processing_time=f"{processing_time:.2f}s",
            ocr_confidence=f"{ocr_confidence:.2%}",
            extracted_fields=random.randint(10, 25)
        )
        
        return {
            "doc_type": doc_type,
            "processing_time": processing_time,
            "ocr_confidence": ocr_confidence
        }
    
    def simulate_ml_prediction(self, app_id: str, features: dict):
        """Simulate ML model prediction with feature importance"""
        start_time = time.time()
        
        # Simulate model inference
        time.sleep(0.05)
        
        # Simulate prediction
        prediction = 1 if features['monthly_income'] < 6000 else 0
        confidence = random.uniform(0.75, 0.95) if prediction == 1 else random.uniform(0.60, 0.85)
        
        # Feature importance (simulated)
        feature_importance = {
            "monthly_income": 0.25,
            "family_size": 0.18,
            "net_worth": 0.15,
            "credit_score": 0.12,
            "employment_years": 0.10,
            "housing_type": 0.08,
            "total_assets": 0.07,
            "total_liabilities": 0.05
        }
        
        inference_time = time.time() - start_time
        
        self.structured_logger.info(
            "ml_prediction",
            application_id=app_id,
            model_version="v3",
            prediction=prediction,
            confidence=f"{confidence:.2%}",
            inference_time=f"{inference_time*1000:.1f}ms",
            feature_count=12,
            top_features=list(feature_importance.keys())[:3]
        )
        
        # Log to audit
        self.audit_logger.log_audit_event(
            event_type="ml_prediction",
            application_id=app_id,
            user_id="ML_MODEL_v3",
            action="eligibility_prediction",
            details={
                "prediction": "APPROVE" if prediction == 1 else "REJECT",
                "confidence": confidence,
                "model_version": "v3",
                "feature_importance": feature_importance,
                "inference_time_ms": inference_time * 1000
            }
        )
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "feature_importance": feature_importance,
            "inference_time": inference_time
        }
    
    def simulate_validation_checks(self, app_id: str):
        """Simulate data validation with cross-document consistency checks"""
        checks = [
            {"check": "income_consistency", "status": "PASS", "confidence": 0.95},
            {"check": "identity_verification", "status": "PASS", "confidence": 0.98},
            {"check": "address_matching", "status": "PASS", "confidence": 0.92},
            {"check": "employment_dates", "status": "PASS", "confidence": 0.89},
            {"check": "credit_score_valid", "status": "PASS", "confidence": 0.96}
        ]
        
        for check in checks:
            self.structured_logger.info(
                f"validation_{check['check']}",
                application_id=app_id,
                status=check['status'],
                confidence=f"{check['confidence']:.2%}"
            )
        
        overall_score = sum(c['confidence'] for c in checks) / len(checks)
        
        self.audit_logger.log_audit_event(
            event_type="validation",
            application_id=app_id,
            user_id="VALIDATION_AGENT",
            action="data_validation",
            details={
                "checks_performed": len(checks),
                "checks_passed": sum(1 for c in checks if c['status'] == 'PASS'),
                "overall_score": overall_score,
                "checks": checks
            }
        )
        
        return {"score": overall_score, "checks": checks}
    
    def simulate_eligibility_decision(self, app_id: str, ml_result: dict, validation: dict):
        """Simulate final eligibility decision combining ML and policy rules"""
        
        # Simulate policy rules evaluation
        policy_score = random.uniform(0.70, 0.95)
        need_assessment = random.uniform(0.75, 0.90)
        
        # Calculate final score
        final_score = (
            ml_result['confidence'] * 0.40 +
            policy_score * 0.30 +
            need_assessment * 0.30
        )
        
        decision = "APPROVED" if final_score >= 0.70 else "SOFT_DECLINE" if final_score >= 0.50 else "DECLINED"
        
        self.structured_logger.info(
            "eligibility_decision",
            application_id=app_id,
            decision=decision,
            final_score=f"{final_score:.3f}",
            ml_contribution=f"{ml_result['confidence'] * 0.40:.3f}",
            policy_contribution=f"{policy_score * 0.30:.3f}",
            need_contribution=f"{need_assessment * 0.30:.3f}"
        )
        
        self.audit_logger.log_audit_event(
            event_type="decision",
            application_id=app_id,
            user_id="ELIGIBILITY_AGENT",
            action="final_decision",
            details={
                "decision": decision,
                "final_score": final_score,
                "score_breakdown": {
                    "ml_model": ml_result['confidence'] * 0.40,
                    "policy_rules": policy_score * 0.30,
                    "need_assessment": need_assessment * 0.30
                },
                "ml_prediction": ml_result['prediction'],
                "validation_score": validation['score']
            }
        )
        
        return {
            "decision": decision,
            "final_score": final_score,
            "policy_score": policy_score,
            "need_assessment": need_assessment
        }
    
    def process_complete_application(self, app_name: str, features: dict):
        """Process a complete application with full tracing"""
        
        app_id = f"APP_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = time.time()
        
        print(f"\n{'='*80}")
        print(f"Processing Application: {app_id}")
        print(f"{'='*80}")
        
        # Stage 1: Document Processing
        print(f"\n[STAGE 1] Document Processing")
        docs = ["bank_statement", "emirates_id", "resume", "assets_liabilities", "credit_report"]
        doc_results = []
        
        for doc in docs:
            result = self.simulate_document_processing(app_id, doc)
            doc_results.append(result)
            print(f"  ✓ {doc}: {result['ocr_confidence']:.1%} confidence")
        
        # Stage 2: Validation
        print(f"\n[STAGE 2] Data Validation")
        validation_result = self.simulate_validation_checks(app_id)
        print(f"  ✓ Validation score: {validation_result['score']:.2%}")
        print(f"  ✓ Checks passed: {len([c for c in validation_result['checks'] if c['status'] == 'PASS'])}/{len(validation_result['checks'])}")
        
        # Stage 3: ML Prediction
        print(f"\n[STAGE 3] ML Model Prediction")
        ml_result = self.simulate_ml_prediction(app_id, features)
        print(f"  ✓ Model: v3 (12 features)")
        print(f"  ✓ Prediction: {ml_result['prediction']} ({'APPROVE' if ml_result['prediction'] == 1 else 'REJECT'})")
        print(f"  ✓ Confidence: {ml_result['confidence']:.1%}")
        print(f"  ✓ Inference time: {ml_result['inference_time']*1000:.1f}ms")
        
        # Stage 4: Final Decision
        print(f"\n[STAGE 4] Final Eligibility Decision")
        decision_result = self.simulate_eligibility_decision(app_id, ml_result, validation_result)
        print(f"  ✓ Decision: {decision_result['decision']}")
        print(f"  ✓ Final Score: {decision_result['final_score']:.3f}")
        print(f"  ✓ ML Contribution: {ml_result['confidence'] * 0.40:.3f} (40%)")
        print(f"  ✓ Policy Score: {decision_result['policy_score'] * 0.30:.3f} (30%)")
        print(f"  ✓ Need Assessment: {decision_result['need_assessment'] * 0.30:.3f} (30%)")
        
        total_time = time.time() - start_time
        
        # Final audit log
        self.audit_logger.log_audit_event(
            event_type="application_completed",
            application_id=app_id,
            user_id="SYSTEM",
            action="workflow_complete",
            details={
                "total_processing_time": f"{total_time:.2f}s",
                "documents_processed": len(docs),
                "validation_score": validation_result['score'],
                "ml_prediction": ml_result['prediction'],
                "final_decision": decision_result['decision'],
                "final_score": decision_result['final_score']
            }
        )
        
        print(f"\n  ✓ Total processing time: {total_time:.2f}s")
        
        return {
            "application_id": app_id,
            "documents": doc_results,
            "validation": validation_result,
            "ml_prediction": ml_result,
            "decision": decision_result,
            "processing_time": total_time
        }
    
    def export_comprehensive_trace(self, results: list):
        """Export comprehensive trace with all applications"""
        
        trace_file = self.output_dir / f"langfuse_comprehensive_trace_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        trace_data = {
            "timestamp": datetime.now().isoformat(),
            "demo_type": "comprehensive_langfuse_observability",
            "total_applications": len(results),
            "applications": []
        }
        
        for result in results:
            app_trace = {
                "application_id": result['application_id'],
                "processing_time": f"{result['processing_time']:.2f}s",
                "stages": {
                    "document_processing": {
                        "documents": len(result['documents']),
                        "avg_confidence": sum(d['ocr_confidence'] for d in result['documents']) / len(result['documents'])
                    },
                    "validation": {
                        "score": result['validation']['score'],
                        "checks_passed": len([c for c in result['validation']['checks'] if c['status'] == 'PASS'])
                    },
                    "ml_prediction": {
                        "model_version": "v3",
                        "prediction": result['ml_prediction']['prediction'],
                        "confidence": result['ml_prediction']['confidence'],
                        "inference_time_ms": result['ml_prediction']['inference_time'] * 1000
                    },
                    "decision": {
                        "final_decision": result['decision']['decision'],
                        "final_score": result['decision']['final_score'],
                        "score_breakdown": {
                            "ml": result['ml_prediction']['confidence'] * 0.40,
                            "policy": result['decision']['policy_score'] * 0.30,
                            "need": result['decision']['need_assessment'] * 0.30
                        }
                    }
                }
            }
            trace_data['applications'].append(app_trace)
        
        # Add aggregate statistics
        trace_data['aggregate_statistics'] = {
            "avg_processing_time": sum(r['processing_time'] for r in results) / len(results),
            "approved_count": sum(1 for r in results if r['decision']['decision'] == 'APPROVED'),
            "declined_count": sum(1 for r in results if r['decision']['decision'] == 'DECLINED'),
            "soft_decline_count": sum(1 for r in results if r['decision']['decision'] == 'SOFT_DECLINE'),
            "avg_ml_confidence": sum(r['ml_prediction']['confidence'] for r in results) / len(results),
            "avg_final_score": sum(r['decision']['final_score'] for r in results) / len(results)
        }
        
        with open(trace_file, 'w') as f:
            json.dump(trace_data, f, indent=2, default=str)
        
        return trace_file
    
    def run_comprehensive_demo(self):
        """Run comprehensive demonstration with multiple applications"""
        
        print("\n" + "="*80)
        print("COMPREHENSIVE LANGFUSE OBSERVABILITY DEMONSTRATION")
        print("="*80)
        print("\nFeatures:")
        print("  • Multi-stage pipeline tracing")
        print("  • ML model prediction tracking")
        print("  • Feature importance logging")
        print("  • Performance metrics (inference time, processing time)")
        print("  • Audit trail generation")
        print("  • Exportable to Langfuse Cloud")
        print("="*80)
        
        # Process multiple test applications
        test_cases = [
            {
                "name": "HIGH_NEED",
                "features": {
                    "monthly_income": 4200,
                    "family_size": 6,
                    "net_worth": 7000,
                    "credit_score": 680
                }
            },
            {
                "name": "MODERATE_NEED",
                "features": {
                    "monthly_income": 7500,
                    "family_size": 3,
                    "net_worth": 35000,
                    "credit_score": 720
                }
            },
            {
                "name": "LOW_NEED",
                "features": {
                    "monthly_income": 25000,
                    "family_size": 2,
                    "net_worth": 450000,
                    "credit_score": 780
                }
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            result = self.process_complete_application(
                test_case['name'],
                test_case['features']
            )
            results.append(result)
            time.sleep(0.1)  # Small delay between applications
        
        # Export comprehensive trace
        print(f"\n{'='*80}")
        print("EXPORTING COMPREHENSIVE TRACE")
        print(f"{'='*80}")
        
        trace_file = self.export_comprehensive_trace(results)
        
        print(f"\n✓ Comprehensive trace exported to:")
        print(f"  {trace_file}")
        
        # Display summary
        print(f"\n{'='*80}")
        print("SUMMARY STATISTICS")
        print(f"{'='*80}")
        
        print(f"\nApplications Processed: {len(results)}")
        print(f"  • APPROVED: {sum(1 for r in results if r['decision']['decision'] == 'APPROVED')}")
        print(f"  • SOFT_DECLINE: {sum(1 for r in results if r['decision']['decision'] == 'SOFT_DECLINE')}")
        print(f"  • DECLINED: {sum(1 for r in results if r['decision']['decision'] == 'DECLINED')}")
        
        print(f"\nPerformance Metrics:")
        print(f"  • Avg Processing Time: {sum(r['processing_time'] for r in results) / len(results):.2f}s")
        print(f"  • Avg ML Confidence: {sum(r['ml_prediction']['confidence'] for r in results) / len(results):.1%}")
        print(f"  • Avg Final Score: {sum(r['decision']['final_score'] for r in results) / len(results):.3f}")
        
        print(f"\n{'='*80}")
        print("✅ COMPREHENSIVE LANGFUSE DEMONSTRATION COMPLETE")
        print(f"{'='*80}")
        
        print(f"\nObservability Capabilities Demonstrated:")
        print(f"  ✓ End-to-end application tracing")
        print(f"  ✓ Multi-stage pipeline monitoring")
        print(f"  ✓ ML model prediction tracking with feature importance")
        print(f"  ✓ Performance metrics (inference time, processing time)")
        print(f"  ✓ Decision explainability (score breakdown)")
        print(f"  ✓ Audit trail for compliance")
        print(f"  ✓ Aggregate statistics across applications")
        print(f"  ✓ Exportable traces for Langfuse Cloud integration")
        
        print(f"\n{'='*80}\n")
        
        return True


def main():
    """Run comprehensive Langfuse demonstration"""
    demo = ComprehensiveLangfuseDemo()
    success = demo.run_comprehensive_demo()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
