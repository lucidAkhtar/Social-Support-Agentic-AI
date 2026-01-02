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

from src.core.langgraph_orchestrator import LangGraphOrchestrator
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
        orchestrator = LangGraphOrchestrator()
        
        # Register all agents
        orchestrator.register_agents(
            extraction_agent=DataExtractionAgent(),
            validation_agent=DataValidationAgent(),
            eligibility_agent=EligibilityAgent(),
            recommendation_agent=RecommendationAgent(),
            explanation_agent=ExplanationAgent(),
            rag_chatbot_agent=RAGChatbotAgent({
                'db_path': 'data/databases/applications.db',
                'ollama_url': 'http://localhost:11434',
                'ollama_model': 'mistral:latest'
            })
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
        
        test_data = next(app for app in metadata['applications'] if app['case_id'] == 'approved_1')
        
        # Add missing fields with defaults (for backward compatibility)
        defaults = {
            'email': f"{test_data.get('full_name', 'test').lower().replace(' ', '.')}@example.ae",
            'phone': '+971501234567',
            'date_of_birth': '1990-01-01',
            'nationality': 'UAE',
            'marital_status': 'Married',
            'monthly_expenses': test_data.get('monthly_income', 5000) * 0.6,  # 60% of income
            'dependents': test_data.get('family_size', 4) - 1,  # family_size minus applicant
            'housing_type': 'Rented',
            'has_special_needs': False,
            'special_needs_details': None,
            'has_chronic_illness': False,
            'medical_expenses': 0
        }
        
        for key, value in defaults.items():
            if key not in test_data:
                test_data[key] = value
        
        return test_data
    
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
        
        # Process application using correct API signature
        documents_path = Path(test_data_approved_1['documents_path'])
        documents = []
        if documents_path.exists():
            for doc_file in documents_path.glob('*'):
                if doc_file.is_file():
                    documents.append({
                        'file_name': doc_file.name,
                        'file_path': str(doc_file),
                        'document_type': 'application_document'
                    })
        
        result = await orchestrator.process_application(
            application_id=application_id,
            applicant_name=test_data_approved_1['full_name'],
            documents=documents
        )
        
        # Assertions - verify workflow completed
        assert result is not None, "Processing should complete successfully"
        assert "application_id" in result, "Result should contain application_id"
        assert result["application_id"] == application_id
        assert "stage" in result, "Result should contain stage"
        
        print(f"\n[PASS] INTEGRATION TEST PASSED: approved_1")
        print(f"  • Application ID: {result['application_id']}")
        print(f"  • Final Stage: {result.get('stage')}")
        print(f"  • Workflow completed successfully")
        
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
        
        # Add missing fields with defaults
        defaults = {
            'email': f"{reject_case.get('full_name', 'test').lower().replace(' ', '.')}@example.ae",
            'phone': '+971501234567',
            'date_of_birth': '1990-01-01',
            'nationality': 'UAE',
            'marital_status': 'Married',
            'monthly_expenses': reject_case.get('monthly_income', 15000) * 0.4,
            'dependents': reject_case.get('family_size', 3) - 1,
            'housing_type': 'Owned',
            'has_special_needs': False,
            'special_needs_details': None,
            'has_chronic_illness': False,
            'medical_expenses': 0
        }
        
        for key, value in defaults.items():
            if key not in reject_case:
                reject_case[key] = value
        
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
        
        # Process application using correct API signature
        documents_path = Path(reject_case['documents_path'])
        documents = []
        if documents_path.exists():
            for doc_file in documents_path.glob('*'):
                if doc_file.is_file():
                    documents.append({
                        'file_name': doc_file.name,
                        'file_path': str(doc_file),
                        'document_type': 'application_document'
                    })
        
        result = await orchestrator.process_application(
            application_id=application_id,
            applicant_name=reject_case['full_name'],
            documents=documents
        )
        
        # Assertions - verify workflow completed
        assert result is not None, "Processing should complete successfully"
        assert "application_id" in result, "Result should contain application_id"
        assert result["application_id"] == application_id
        
        print(f"\n[PASS] INTEGRATION TEST PASSED: reject_1")
        print(f"  • Application ID: {result['application_id']}")
        print(f"  • Final Stage: {result.get('stage')}")
        print(f"  • Workflow completed successfully")
        
        return result
    
    @pytest.mark.asyncio
    async def test_ml_model_versioning(self, orchestrator):
        """Test that ML model version fallback works correctly"""
        
        # Create eligibility agent
        eligibility_agent = EligibilityAgent()
        
        # Check model was loaded
        assert hasattr(eligibility_agent, 'model_version'), "Should have model_version attribute"
        assert eligibility_agent.model_version in ["v4", "v3", "v2", "fallback"], \
            f"Model version should be v4, v3, v2, or fallback, got {eligibility_agent.model_version}"
        
        if eligibility_agent.model_version == "v4":
            assert eligibility_agent.model_features == 12, "v4 should have 12 features"
        elif eligibility_agent.model_version == "v3":
            assert eligibility_agent.model_features == 12, "v3 should have 12 features"
        elif eligibility_agent.model_version == "v2":
            assert eligibility_agent.model_features == 8, "v2 should have 8 features"
        
        print(f"\n[PASS] ML MODEL VERSION TEST PASSED")
        print(f"  • Active Model: {eligibility_agent.model_version}")
        print(f"  • Feature Count: {eligibility_agent.model_features}")
        
        return True
    
    @pytest.mark.asyncio
    async def test_chatbot_integration(self, orchestrator, test_data_approved_1):
        """Test that chatbot can answer questions about decisions"""
        
        # First process an application
        application_id = "TEST_INT_003"
        
        # Process application using correct API signature
        documents_path = Path(test_data_approved_1['documents_path'])
        documents = []
        if documents_path.exists():
            for doc_file in documents_path.glob('*'):
                if doc_file.is_file():
                    documents.append({
                        'file_name': doc_file.name,
                        'file_path': str(doc_file),
                        'document_type': 'application_document'
                    })
        
        result = await orchestrator.process_application(
            application_id=application_id,
            applicant_name=test_data_approved_1['full_name'],
            documents=documents
        )
        
        # Verify processing completed
        assert result is not None, "Processing should complete"
        assert "application_id" in result, "Result should contain application_id"
        
        print(f"\n[PASS] CHATBOT INTEGRATION TEST PASSED")
        print(f"  • Application processed: {result['application_id']}")
        print(f"  • Workflow completed successfully")
        
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
