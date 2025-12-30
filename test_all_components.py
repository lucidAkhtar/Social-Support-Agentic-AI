#!/usr/bin/env python3
"""
Test script to verify all real components work end-to-end.
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_ollama_connection():
    """Test Ollama connection."""
    print("Testing Ollama connection...")
    try:
        from langchain_community.llms import Ollama
        llm = Ollama(model="mistral:latest")
        response = llm.invoke("What is 2+2?")
        assert "4" in response, "Unexpected response"
        print("✓ Ollama connection working")
        return True
    except Exception as e:
        print(f"✗ Ollama failed: {e}")
        return False

def test_chatbot():
    """Test chatbot initialization."""
    print("\nTesting Chatbot...")
    try:
        from src.agents.chatbot import ApplicationChatbot
        chatbot = ApplicationChatbot()
        msg = chatbot.initialize_conversation()
        assert "Welcome" in msg, "Invalid initialization"
        print("✓ Chatbot working")
        return True
    except Exception as e:
        print(f"✗ Chatbot failed: {e}")
        return False

def test_ml_model():
    """Test ML model training and prediction."""
    print("\nTesting ML Model...")
    try:
        from src.ml.ml_pipeline import EligibilityMLModel
        import numpy as np
        
        model = EligibilityMLModel()
        
        applicant = {
            "monthly_income": 8000,
            "family_size": 4,
            "num_dependents": 2,
            "employment_stability": 0.8,
            "education_level": 50,
            "total_assets": 50000,
            "total_liabilities": 20000,
            "age": 35
        }
        
        result = model.predict_eligibility(applicant)
        assert 0 <= result['eligibility_score'] <= 1, "Invalid score"
        assert result['decision'] in ['eligible', 'ineligible', 'review_needed'], "Invalid decision"
        
        print(f"✓ ML Model working - Score: {result['eligibility_score']:.2%}, Decision: {result['decision']}")
        
        if result['shap_values']:
            print(f"  SHAP values: {len(result['shap_values'])} features analyzed")
        
        if result['feature_importance']:
            top_feature = max(result['feature_importance'].items(), key=lambda x: x[1])
            print(f"  Top feature: {top_feature[0]} ({top_feature[1]:.4f})")
        
        return True
    except Exception as e:
        print(f"✗ ML Model failed: {e}")
        return False

def test_llm_decision():
    """Test LLM-based decision making."""
    print("\nTesting LLM Decision Agent...")
    try:
        from src.agents.llm_decision_agent import LLMDecisionAgent
        
        agent = LLMDecisionAgent()
        
        applicant = {
            "full_name": "Ahmed Al-Mansouri",
            "monthly_income": 7500,
            "family_size": 5,
            "num_dependents": 3,
            "employment_status": "employed",
            "education": "high school",
            "total_assets": 30000,
            "total_liabilities": 15000
        }
        
        result = agent.make_decision(applicant, 0.78)
        
        assert result['success'], f"Decision failed: {result.get('error')}"
        assert result['decision'] in ['APPROVE', 'SOFT_REJECT', 'REVIEW_NEEDED'], "Invalid decision"
        assert len(result['reasoning']) > 0, "No reasoning provided"
        assert len(result['recommendations']) > 0, "No recommendations"
        
        print(f"✓ LLM Decision working")
        print(f"  Decision: {result['decision']}")
        print(f"  Confidence: {result['confidence']:.2%}")
        print(f"  Reasoning points: {len(result['reasoning'])}")
        print(f"  Recommendations: {len(result['recommendations'])}")
        
        return True
    except Exception as e:
        print(f"✗ LLM Decision failed: {e}")
        return False

def test_document_processor():
    """Test document processor initialization."""
    print("\nTesting Document Processor...")
    try:
        from src.agents.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Test with mock PDF content
        mock_pdf = """
        Account Holder: John Smith
        Account Number: ****5678
        Current Balance: 50,000 AED
        Average Monthly Income: 12,000 AED
        """
        
        result = processor.extract_from_bank_statement(mock_pdf, "test.pdf")
        assert result['success'], f"Extraction failed: {result.get('error')}"
        
        print("✓ Document Processor working")
        print(f"  Extracted: {result.get('data', {})}")
        
        return True
    except Exception as e:
        print(f"✗ Document Processor failed: {e}")
        return False

def test_fastapi_health():
    """Test FastAPI health endpoint."""
    print("\nTesting FastAPI...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:8001/health", timeout=5)
        assert response.status_code == 200, f"Status {response.status_code}"
        
        data = response.json()
        print("✓ FastAPI health check passed")
        print(f"  Services: Orchestrator={data['services']['orchestrator']}, DB={data['services']['database']}, Tracker={data['services']['tracker']}")
        
        return True
    except Exception as e:
        print(f"✗ FastAPI failed: {e}")
        return False

def main():
    print("=" * 70)
    print("COMPREHENSIVE SYSTEM TEST")
    print("=" * 70)
    
    tests = [
        test_ollama_connection,
        test_chatbot,
        test_ml_model,
        test_llm_decision,
        test_document_processor,
        test_fastapi_health
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 70)
    print(f"RESULTS: {sum(results)}/{len(results)} tests passed")
    print("=" * 70)
    
    if all(results):
        print("\n✅ ALL SYSTEMS OPERATIONAL - Ready for demo!")
        return 0
    else:
        print("\n⚠️ Some systems failed - check output above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
