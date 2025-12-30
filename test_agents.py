"""
Agent Testing Script
Tests all 5 agents with sample data from synthetic generation
"""
import asyncio
import json
from pathlib import Path
from datetime import datetime
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.orchestrator import MasterOrchestrator
from src.core.types import Document, ApplicationState
from src.agents.extraction_agent import DataExtractionAgent
from src.agents.validation_agent import DataValidationAgent
from src.agents.eligibility_agent import EligibilityAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.explanation_agent import ExplanationAgent


async def test_agents():
    """Test all agents with synthetic data"""
    
    print("=" * 80)
    print("AGENT TESTING SUITE")
    print("=" * 80)
    
    # Initialize agents
    print("\n1. Initializing Agents...")
    extraction_agent = DataExtractionAgent()
    validation_agent = DataValidationAgent()
    eligibility_agent = EligibilityAgent()
    recommendation_agent = RecommendationAgent()
    explanation_agent = ExplanationAgent()
    print("✓ All agents initialized")
    
    # Initialize orchestrator
    print("\n2. Initializing Master Orchestrator...")
    orchestrator = MasterOrchestrator()
    orchestrator.register_agents(
        extraction_agent,
        validation_agent,
        eligibility_agent,
        recommendation_agent,
        explanation_agent
    )
    print("✓ Master Orchestrator ready")
    
    # Create test application
    print("\n3. Creating Test Application...")
    app_id = "TEST_APP_001"
    app_state = orchestrator.create_application(app_id)
    
    # Add sample documents (using generated synthetic documents)
    doc_dir = Path("data/synthetic/documents/applicant_1")
    if doc_dir.exists():
        documents = [
            Document(
                document_id="doc_001",
                document_type="emirates_id",
                filename="emirates_id.txt",
                file_path=str(doc_dir / "emirates_id.txt")
            ),
            Document(
                document_id="doc_002",
                document_type="bank_statement",
                filename="bank_statement.txt",
                file_path=str(doc_dir / "bank_statement.txt")
            ),
            Document(
                document_id="doc_003",
                document_type="resume",
                filename="resume.txt",
                file_path=str(doc_dir / "resume.txt")
            ),
            Document(
                document_id="doc_004",
                document_type="assets_liabilities",
                filename="assets_liabilities.txt",
                file_path=str(doc_dir / "assets_liabilities.txt")
            ),
            Document(
                document_id="doc_005",
                document_type="credit_report",
                filename="credit_report.txt",
                file_path=str(doc_dir / "credit_report.txt")
            )
        ]
        
        for doc in documents:
            orchestrator.add_document(app_id, doc)
        
        print(f"✓ Added {len(documents)} documents")
    else:
        print("⚠ No sample documents found. Run synthetic_data_generator.py first.")
        return
    
    # Test the full pipeline
    print("\n" + "=" * 80)
    print("RUNNING FULL PIPELINE")
    print("=" * 80)
    
    try:
        # Process application through all agents
        final_state = await orchestrator.process_application(app_id)
        
        print("\n" + "=" * 80)
        print("PIPELINE RESULTS")
        print("=" * 80)
        
        # 1. Extraction Results
        print("\n📄 EXTRACTION RESULTS:")
        print("-" * 80)
        if final_state.extracted_data:
            print(f"Applicant Name: {final_state.extracted_data.applicant_info.get('full_name', 'N/A')}")
            print(f"ID Number: {final_state.extracted_data.applicant_info.get('id_number', 'N/A')}")
            print(f"Monthly Income: {final_state.extracted_data.income_data.get('monthly_income', 0)} AED")
            print(f"Monthly Expenses: {final_state.extracted_data.income_data.get('monthly_expenses', 0)} AED")
            print(f"Employment: {final_state.extracted_data.employment_data.get('employment_status', 'N/A')}")
            print(f"Experience: {final_state.extracted_data.employment_data.get('years_of_experience', 0)} years")
            print(f"Net Worth: {final_state.extracted_data.assets_liabilities.get('net_worth', 0)} AED")
            print(f"Credit Score: {final_state.extracted_data.credit_data.get('credit_score', 'N/A')}")
        
        # 2. Validation Results
        print("\n✓ VALIDATION RESULTS:")
        print("-" * 80)
        if final_state.validation_report:
            print(f"Valid: {final_state.validation_report.is_valid}")
            print(f"Issues Found: {len(final_state.validation_report.issues)}")
            print(f"Completeness Score: {final_state.validation_report.data_completeness_score:.2f}")
            print(f"Confidence Score: {final_state.validation_report.confidence_score:.2f}")
            
            if final_state.validation_report.issues:
                print("\nValidation Issues:")
                for i, issue in enumerate(final_state.validation_report.issues[:5], 1):
                    print(f"  {i}. [{issue.severity.upper()}] {issue.message}")
        
        # 3. Eligibility Results
        print("\n🎯 ELIGIBILITY RESULTS:")
        print("-" * 80)
        if final_state.eligibility_result:
            print(f"Eligible: {final_state.eligibility_result.is_eligible}")
            print(f"Eligibility Score: {final_state.eligibility_result.eligibility_score:.4f}")
            print(f"ML Prediction: {final_state.eligibility_result.ml_prediction}")
            print(f"\nPolicy Rules Met:")
            for rule, passed in final_state.eligibility_result.policy_rules_met.items():
                status = "✓" if passed else "✗"
                print(f"  {status} {rule}")
            
            print(f"\nReasoning:")
            for i, reason in enumerate(final_state.eligibility_result.reasoning[:3], 1):
                print(f"  {i}. {reason}")
        
        # 4. Recommendation Results
        print("\n💡 RECOMMENDATION RESULTS:")
        print("-" * 80)
        if final_state.recommendation:
            print(f"Decision: {final_state.recommendation.decision.value.upper()}")
            if final_state.recommendation.financial_support_amount:
                print(f"Financial Support: {final_state.recommendation.financial_support_amount} AED/month")
                print(f"Support Type: {final_state.recommendation.financial_support_type}")
            print(f"Confidence: {final_state.recommendation.confidence_level:.2f}")
            print(f"\nEconomic Enablement Programs: {len(final_state.recommendation.economic_enablement_programs)}")
            for i, program in enumerate(final_state.recommendation.economic_enablement_programs[:3], 1):
                print(f"  {i}. {program['program_name']} ({program['category']})")
        
        # 5. Explanation Results
        print("\n📝 EXPLANATION:")
        print("-" * 80)
        if final_state.explanation:
            print(final_state.explanation.summary)
        
        # Test Chatbot
        print("\n" + "=" * 80)
        print("TESTING CHATBOT CAPABILITIES")
        print("=" * 80)
        
        # Test 1: Explanation query
        print("\n🤖 Query 1: 'Why was I approved/declined?'")
        response1 = await orchestrator.handle_chat_query(
            app_id,
            "Why was I approved?",
            "explanation"
        )
        print(f"Response: {response1.get('response', 'N/A')[:300]}...")
        
        # Test 2: Simulation query
        print("\n🤖 Query 2: 'What if my income increases?'")
        response2 = await orchestrator.handle_chat_query(
            app_id,
            "What if my income increases to 7000 AED?",
            "simulation"
        )
        print(f"Response: {response2.get('response', 'N/A')[:300]}...")
        
        # Test 3: Audit query
        print("\n🤖 Query 3: 'Show me data inconsistencies'")
        response3 = await orchestrator.handle_chat_query(
            app_id,
            "Show me any inconsistencies in my data",
            "audit"
        )
        print(f"Response: {response3.get('response', 'N/A')[:300]}...")
        
        # Save results
        print("\n" + "=" * 80)
        print("SAVING TEST RESULTS")
        print("=" * 80)
        
        results = {
            "application_id": app_id,
            "timestamp": datetime.now().isoformat(),
            "status": final_state.stage.value,
            "extraction": {
                "applicant_name": final_state.extracted_data.applicant_info.get('full_name') if final_state.extracted_data else None,
                "monthly_income": final_state.extracted_data.income_data.get('monthly_income') if final_state.extracted_data else None,
            },
            "validation": {
                "is_valid": final_state.validation_report.is_valid if final_state.validation_report else None,
                "issues_count": len(final_state.validation_report.issues) if final_state.validation_report else 0,
            },
            "eligibility": {
                "is_eligible": final_state.eligibility_result.is_eligible if final_state.eligibility_result else None,
                "score": final_state.eligibility_result.eligibility_score if final_state.eligibility_result else None,
            },
            "recommendation": {
                "decision": final_state.recommendation.decision.value if final_state.recommendation else None,
                "support_amount": final_state.recommendation.financial_support_amount if final_state.recommendation else None,
            },
            "chatbot_tests": [
                {"query": "Why was I approved?", "response_length": len(response1.get('response', ''))},
                {"query": "What if income increases?", "response_length": len(response2.get('response', ''))},
                {"query": "Show inconsistencies", "response_length": len(response3.get('response', ''))},
            ]
        }
        
        output_path = "data/synthetic/agent_test_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"✓ Results saved to: {output_path}")
        
        print("\n" + "=" * 80)
        print("✅ ALL AGENT TESTS PASSED")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Run agent tests"""
    asyncio.run(test_agents())


if __name__ == "__main__":
    main()
