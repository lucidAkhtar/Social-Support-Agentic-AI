"""
Integration Tests - End-to-End Application Processing
Tests complete workflow from document upload to final decision
"""

import pytest
import sys
import os
from pathlib import Path
import json
import asyncio

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.orchestrator import MasterOrchestrator
from src.agents.extraction_agent import DataExtractionAgent
from src.agents.validation_agent import DataValidationAgent
from src.agents.eligibility_agent import EligibilityAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.explanation_agent import ExplanationAgent
from src.agents.rag_chatbot_agent import RAGChatbotAgent
from src.core.types import ApplicationState, ProcessingStage


class TestEndToEndIntegration:
    """Complete end-to-end integration tests"""
    
    @pytest.fixture
    def orchestrator(self):
        """Setup orchestrator with all agents"""
        orchestrator = MasterOrchestrator()
        
        # Register all agents
        orchestrator.register_agents(
            DataExtractionAgent(),
            DataValidationAgent(),
            EligibilityAgent(),
            RecommendationAgent(),
            ExplanationAgent(),
            RAGChatbotAgent()
        )
        
        return orchestrator
    
    @pytest.fixture
    def test_data_approved_1(self):
        """Load approved_1 test case"""
        metadata_file = project_root / "data" / "test_applications_metadata.json"
        
        if not metadata_file.exists():
            pytest.skip("Test data not generated. Run: python scripts/generate_production_test_data.py")
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        return next(app for app in metadata['applications'] if app['case_id'] == 'approved_1')
    
    @pytest.mark.asyncio
    async def test_approved_1_full_workflow(self, orchestrator, test_data_approved_1):
        """
        Test complete workflow for approved_1 case
        Expected: HIGH need applicant should be APPROVED
        """
        # Prepare application data
        application_id = "TEST_INT_001"
        
        input_data = {
            "application_id": application_id,
            "applicant_info": {
                "full_name": test_data_approved_1['full_name'],
                "email": test_data_approved_1['email'],
                "phone": test_data_approved_1['phone'],
                "date_of_birth": test_data_approved_1['date_of_birth'],
                "nationality": test_data_approved_1['nationality'],
                "marital_status": test_data_approved_1['marital_status']
            },
            "income_data": {
                "monthly_income": test_data_approved_1['monthly_income'],
                "monthly_expenses": test_data_approved_1['monthly_expenses']
            },
            "family_info": {
                "family_size": test_data_approved_1['family_size'],
                "dependents": test_data_approved_1['dependents'],
                "housing_type": test_data_approved_1['housing_type']
            },
            "assets_liabilities": {
                "total_assets": test_data_approved_1['total_assets'],
                "total_liabilities": test_data_approved_1['total_liabilities'],
                "net_worth": test_data_approved_1['net_worth']
            },
            "employment_data": {
                "employment_status": test_data_approved_1['employment_status'],
                "years_of_experience": test_data_approved_1['employment_years']
            },
            "credit_data": {
                "credit_score": test_data_approved_1['credit_score']
            }
        }
        
        # Process application
        result = await orchestrator.process_application(input_data)
        
        # Assertions
        assert result is not None, "Processing should complete successfully"
        assert "recommendation" in result, "Result should contain recommendation"
        assert "eligibility_result" in result, "Result should contain eligibility"
        
        recommendation = result["recommendation"]
        eligibility = result["eligibility_result"]
        
        # Check ML prediction
        ml_prediction = eligibility.ml_prediction
        assert ml_prediction is not None, "ML prediction should exist"
        assert ml_prediction.get("model_version") in ["v3", "v2", "fallback"], "Should use valid model version"
        
        # For approved_1: Low income (4200 AED) + Large family (6) + Low net worth (7000 AED)
        # Expected: HIGH NEED = APPROVAL
        assert ml_prediction.get("prediction") == 1, f"ML should predict APPROVE (1) for high-need case, got {ml_prediction.get('prediction')}"
        assert ml_prediction.get("probability") > 0.7, f"Confidence should be >70% for clear case, got {ml_prediction.get('probability')}"
        
        # Check final decision
        assert recommendation.decision.value in ["APPROVED", "CONDITIONAL"], \
            f"High-need applicant should be APPROVED or CONDITIONAL, got {recommendation.decision.value}"
        
        # Check eligibility score
        assert eligibility.eligibility_score > 0.65, \
            f"High-need case should score >0.65, got {eligibility.eligibility_score}"
        
        # Check explanation exists
        assert "explanation" in result, "Should provide explanation"
        assert result["explanation"].summary, "Explanation should have summary"
        
        print(f"\n✅ INTEGRATION TEST PASSED: approved_1")
        print(f"  • ML Model: {ml_prediction.get('model_version')}")
        print(f"  • ML Prediction: {ml_prediction.get('prediction')} (probability: {ml_prediction.get('probability'):.2%})")
        print(f"  • Final Decision: {recommendation.decision.value}")
        print(f"  • Eligibility Score: {eligibility.eligibility_score:.3f}")
        
        return result
    
    @pytest.mark.asyncio
    async def test_reject_1_full_workflow(self, orchestrator):
        """
        Test complete workflow for reject_1 case
        Expected: High income applicant should be REJECTED
        """
        metadata_file = project_root / "data" / "test_applications_metadata.json"
        
        if not metadata_file.exists():
            pytest.skip("Test data not generated")
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        reject_case = next(app for app in metadata['applications'] if app['case_id'] == 'reject_1')
        
        application_id = "TEST_INT_002"
        
        input_data = {
            "application_id": application_id,
            "applicant_info": {
                "full_name": reject_case['full_name'],
                "email": reject_case['email'],
                "phone": reject_case['phone'],
                "date_of_birth": reject_case['date_of_birth'],
                "nationality": reject_case['nationality'],
                "marital_status": reject_case['marital_status']
            },
            "income_data": {
                "monthly_income": reject_case['monthly_income'],
                "monthly_expenses": reject_case['monthly_expenses']
            },
            "family_info": {
                "family_size": reject_case['family_size'],
                "dependents": reject_case['dependents'],
                "housing_type": reject_case['housing_type']
            },
            "assets_liabilities": {
                "total_assets": reject_case['total_assets'],
                "total_liabilities": reject_case['total_liabilities'],
                "net_worth": reject_case['net_worth']
            },
            "employment_data": {
                "employment_status": reject_case['employment_status'],
                "years_of_experience": reject_case['employment_years']
            },
            "credit_data": {
                "credit_score": reject_case['credit_score']
            }
        }
        
        result = await orchestrator.process_application(input_data)
        
        recommendation = result["recommendation"]
        eligibility = result["eligibility_result"]
        ml_prediction = eligibility.ml_prediction
        
        # For reject_1: High income (25000+ AED) + High net worth (400000+ AED)
        # Expected: LOW NEED = REJECTION
        assert ml_prediction.get("prediction") == 0, \
            f"ML should predict REJECT (0) for low-need case, got {ml_prediction.get('prediction')}"
        
        assert recommendation.decision.value in ["SOFT_DECLINE", "DECLINED"], \
            f"High-income applicant should be DECLINED, got {recommendation.decision.value}"
        
        print(f"\n✅ INTEGRATION TEST PASSED: reject_1")
        print(f"  • ML Prediction: {ml_prediction.get('prediction')} (probability: {ml_prediction.get('probability'):.2%})")
        print(f"  • Final Decision: {recommendation.decision.value}")
        
        return result
    
    @pytest.mark.asyncio
    async def test_ml_model_versioning(self, orchestrator):
        """Test that ML model version fallback works correctly"""
        
        # Create eligibility agent
        eligibility_agent = EligibilityAgent()
        
        # Check model was loaded
        assert hasattr(eligibility_agent, 'model_version'), "Should have model_version attribute"
        assert eligibility_agent.model_version in ["v3", "v2", "fallback"], \
            f"Model version should be v3, v2, or fallback, got {eligibility_agent.model_version}"
        
        if eligibility_agent.model_version == "v3":
            assert eligibility_agent.model_features == 12, "v3 should have 12 features"
        elif eligibility_agent.model_version == "v2":
            assert eligibility_agent.model_features == 8, "v2 should have 8 features"
        
        print(f"\n✅ ML MODEL VERSION TEST PASSED")
        print(f"  • Active Model: {eligibility_agent.model_version}")
        print(f"  • Feature Count: {eligibility_agent.model_features}")
        
        return True
    
    @pytest.mark.asyncio
    async def test_chatbot_integration(self, orchestrator, test_data_approved_1):
        """Test that chatbot can answer questions about decisions"""
        
        # First process an application
        application_id = "TEST_INT_003"
        
        input_data = {
            "application_id": application_id,
            "applicant_info": {
                "full_name": test_data_approved_1['full_name'],
                "email": test_data_approved_1['email']
            },
            "income_data": {
                "monthly_income": test_data_approved_1['monthly_income'],
                "monthly_expenses": test_data_approved_1['monthly_expenses']
            },
            "family_info": {
                "family_size": test_data_approved_1['family_size']
            },
            "assets_liabilities": {
                "net_worth": test_data_approved_1['net_worth']
            },
            "credit_data": {
                "credit_score": test_data_approved_1['credit_score']
            }
        }
        
        result = await orchestrator.process_application(input_data)
        
        # Now test chatbot query
        rag_agent = RAGChatbotAgent()
        
        chat_input = {
            "query": "Why was this application approved?",
            "application_context": result
        }
        
        chat_response = await rag_agent.execute(chat_input)
        
        assert "response" in chat_response, "Chatbot should return response"
        assert len(chat_response["response"]) > 50, "Response should be meaningful"
        
        print(f"\n✅ CHATBOT INTEGRATION TEST PASSED")
        print(f"  • Response length: {len(chat_response['response'])} chars")
        
        return True


def run_integration_tests():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("INTEGRATION TEST SUITE - END-TO-END WORKFLOW")
    print("="*80)
    
    # Run pytest
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-s"  # Show print statements
    ])


if __name__ == "__main__":
    run_integration_tests()
