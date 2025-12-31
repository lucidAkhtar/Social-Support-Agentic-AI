"""
Trace exactly where data is lost in the pipeline
"""
import asyncio
import sys
sys.path.insert(0, '/Users/marghubakhtar/Documents/social_support_agentic_ai')

from src.agents.extraction_agent import DataExtractionAgent
from src.core.types import ApplicationState, ProcessingStage, Document
from pathlib import Path

async def test():
    # Create state
    state = ApplicationState(
        application_id="TRACE_TEST",
        applicant_name="Test User",
        stage=ProcessingStage.PENDING
    )
    
    # Add documents
    state.documents = [
        Document(
            document_id="DOC_1",
            document_type="credit_report",
            filename="credit_report.pdf",
            file_path="data/test_applications/TEST-07/credit_report.pdf"
        ),
        Document(
            document_id="DOC_2",
            document_type="employment_letter",
            filename="employment_letter.pdf",
            file_path="data/test_applications/TEST-07/employment_letter.pdf"
        )
    ]
    
    # Run extraction
    agent = DataExtractionAgent()
    input_data = {
        "application_id": state.application_id,
        "documents": [doc.__dict__ for doc in state.documents]
    }
    
    result = await agent.execute(input_data)
    state.extracted_data = result["extracted_data"]
    
    # Check what's in state
    print("=== AFTER EXTRACTION ===")
    print(f"Credit Data Keys: {list(state.extracted_data.credit_data.keys())}")
    print(f"Credit Score: {state.extracted_data.credit_data.get('credit_score')}")
    print(f"Credit Rating: {state.extracted_data.credit_data.get('credit_rating')}")
    print(f"Payment Ratio: {state.extracted_data.credit_data.get('payment_ratio')}")
    print(f"\\nEmployment Data Keys: {list(state.extracted_data.employment_data.keys())}")
    print(f"Company: {state.extracted_data.employment_data.get('company_name')}")
    print(f"Salary: {state.extracted_data.employment_data.get('monthly_salary')}")
    
    # Simulate database prep (like API does)
    print("\\n=== DATABASE PREP ===")
    app_data = {
        "credit_score": state.extracted_data.credit_data.get("credit_score", 0),
        "credit_rating": state.extracted_data.credit_data.get("credit_rating"),
        "payment_ratio": state.extracted_data.credit_data.get("payment_history", {}).get("payment_ratio"),
        "company_name": state.extracted_data.employment_data.get("company_name"),
        "monthly_salary": state.extracted_data.employment_data.get("monthly_salary"),
    }
    print(f"Credit Score (for DB): {app_data['credit_score']}")
    print(f"Credit Rating (for DB): {app_data['credit_rating']}")
    print(f"Payment Ratio (for DB): {app_data['payment_ratio']}")
    print(f"Company (for DB): {app_data['company_name']}")
    print(f"Salary (for DB): {app_data['monthly_salary']}")

asyncio.run(test())
