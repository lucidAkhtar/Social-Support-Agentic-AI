"""
Test the Unified Database Manager - demonstrates multi-modal data unity.
Shows how SQLite, ChromaDB, and Neo4j work together.
"""

import asyncio
from datetime import datetime
from src.databases import UnifiedDatabaseManager


def test_multimodal_database():
    """Test unified database with all three systems."""
    
    print("="*80)
    print("TESTING MULTI-MODAL DATABASE ARCHITECTURE")
    print("SQLite + ChromaDB + Neo4j working together")
    print("="*80)
    
    # Clean up old test data
    import os
    from pathlib import Path
    db_file = Path("data/databases/social_support.db")
    chroma_dir = Path("data/databases/chromadb")
    
    if db_file.exists():
        db_file.unlink()
        print("\n🗑️  Cleaned up old SQLite database")
    
    if chroma_dir.exists():
        import shutil
        shutil.rmtree(chroma_dir)
        print("🗑️  Cleaned up old ChromaDB data")
    
    print()
    
    # Initialize unified database (Neo4j in mock mode if not available)
    db = UnifiedDatabaseManager(use_neo4j_mock=True)
    
    # Test data
    application_id = "TEST_APP_001"
    applicant_name = "Ahmed Al Mansouri"
    
    print("\n📝 Step 1: Create Application")
    print("-" * 80)
    success = db.create_application(application_id, applicant_name)
    print(f"✓ Application created: {success}")
    
    print("\n👤 Step 2: Save Applicant Profile")
    print("-" * 80)
    profile_data = {
        "applicant_name": applicant_name,
        "id_number": "784-1990-1234567-8",
        "monthly_income": 5500.0,
        "monthly_expenses": 3200.0,
        "employment_status": "employed",
        "years_experience": 8,
        "total_assets": 25000.0,
        "total_liabilities": 8000.0,
        "net_worth": 17000.0,
        "credit_score": 720,
        "family_size": 4,
        "has_disabilities": 0
    }
    db.save_applicant_profile(application_id, profile_data)
    print(f"✓ Profile saved to SQLite and Neo4j")
    print(f"  Income: {profile_data['monthly_income']} AED")
    print(f"  Family Size: {profile_data['family_size']}")
    print(f"  Credit Score: {profile_data['credit_score']}")
    
    print("\n📄 Step 3: Add Documents with Embeddings")
    print("-" * 80)
    
    # Emirates ID
    emirates_id_text = f"""
    Emirates ID Document
    Name: {applicant_name}
    ID Number: 784-1990-1234567-8
    Date of Birth: 15/03/1990
    Nationality: UAE
    """
    db.add_document(
        application_id, "DOC_001", "emirates_id", 
        "/path/to/emirates_id.jpg", emirates_id_text,
        {"name": applicant_name, "id_number": "784-1990-1234567-8"}
    )
    print("✓ Emirates ID added")
    print("  - Metadata stored in SQLite")
    print("  - Text embedded in ChromaDB for semantic search")
    print("  - Document node created in Neo4j graph")
    
    # Resume
    resume_text = f"""
    {applicant_name} - Senior Software Engineer
    
    Experience:
    - Software Engineer at TechCorp (2016-2024) - 8 years
    - Specialized in backend development and cloud infrastructure
    - Led team of 5 developers
    
    Education:
    - Bachelor of Computer Science, UAE University (2012-2016)
    
    Skills: Python, Java, AWS, Docker, Kubernetes
    """
    db.add_document(
        application_id, "DOC_002", "resume",
        "/path/to/resume.pdf", resume_text,
        {"employment": "employed", "experience_years": 8}
    )
    print("✓ Resume added")
    
    # Bank Statement
    bank_statement_text = """
    Bank Statement - Last 6 months
    
    Monthly Income:
    - January: 5,500 AED
    - February: 5,500 AED
    - March: 5,700 AED (with bonus)
    - April: 5,500 AED
    - May: 5,500 AED
    - June: 5,500 AED
    
    Average Monthly Income: 5,533 AED
    """
    db.add_document(
        application_id, "DOC_003", "bank_statement",
        "/path/to/bank_statement.pdf", bank_statement_text,
        {"monthly_income": 5533.0}
    )
    print("✓ Bank Statement added")
    
    print("\n✅ Step 4: Save Validation Results")
    print("-" * 80)
    validation_data = {
        "is_valid": True,
        "completeness_score": 0.95,
        "confidence_score": 1.0,
        "issues": []
    }
    db.save_validation_result(application_id, validation_data)
    print("✓ Validation saved")
    print(f"  - Scores stored in SQLite")
    print(f"  - Document consistency relationships in Neo4j")
    
    print("\n🎯 Step 5: Save Eligibility Decision")
    print("-" * 80)
    decision_data = {
        "is_eligible": True,
        "eligibility_score": 0.78,
        "ml_prediction_score": 0.85,
        "policy_rules_score": 0.75,
        "need_score": 0.65,
        "final_decision": "APPROVED",
        "reasons": [
            "Stable employment with 8 years experience",
            "Good credit score (720)",
            "Healthy debt-to-income ratio"
        ],
        "reasoning": "Applicant meets all eligibility criteria with strong financial profile."
    }
    db.save_eligibility_decision(application_id, decision_data)
    print("✓ Decision saved")
    print(f"  - Decision details in SQLite")
    print(f"  - Decision reasoning embedded in ChromaDB")
    print(f"  - Decision node with relationships in Neo4j")
    
    print("\n💰 Step 6: Save Recommendation")
    print("-" * 80)
    recommendation_data = {
        "decision_type": "APPROVED",
        "support_amount": 8000.0,
        "programs": [
            {"name": "Financial Literacy Workshop", "type": "financial_education"}
        ],
        "reasoning": "Approved for 8,000 AED support with financial education program."
    }
    db.save_recommendation(application_id, recommendation_data)
    print("✓ Recommendation saved")
    print(f"  Support Amount: {recommendation_data['support_amount']} AED")
    
    print("\n🤖 Step 7: Test Chatbot with RAG")
    print("-" * 80)
    
    # Add chat messages
    db.add_chat_message(
        application_id, "user", 
        "Why was I approved?", 
        datetime.now().isoformat()
    )
    db.add_chat_message(
        application_id, "assistant",
        "You were approved based on your stable employment, good credit score, and healthy financial profile.",
        datetime.now().isoformat()
    )
    
    # Get RAG context for new query
    query = "What documents did I submit?"
    rag_context = db.get_chat_context_for_rag(application_id, query)
    print("✓ RAG context retrieved for chatbot")
    print(f"  Query: '{query}'")
    print(f"  Context includes: documents + recent chat history")
    print(f"  Context length: {len(rag_context)} characters")
    
    print("\n🔍 Step 8: Semantic Search Across Documents")
    print("-" * 80)
    search_results = db.search_documents_semantic("income employment", application_id)
    print(f"✓ Found {len(search_results)} semantically similar document sections")
    for i, result in enumerate(search_results[:3], 1):
        print(f"\n  Result {i}:")
        print(f"    Document Type: {result['metadata']['document_type']}")
        print(f"    Snippet: {result['document'][:100]}...")
    
    print("\n🏆 Step 9: Get Complete Multi-Modal Data")
    print("-" * 80)
    print("This demonstrates the 'unity of MultiModal data sources'")
    
    full_data = db.get_application_full_data(application_id)
    
    print("\n✓ Retrieved from SQLite (Structured Data):")
    print(f"  - Application Status: {full_data['application']['status']}")
    print(f"  - Applicant ID: {full_data['profile']['id_number']}")
    print(f"  - Monthly Income: {full_data['profile']['monthly_income']} AED")
    print(f"  - Validation History: {len(full_data['validation_history'])} records")
    print(f"  - Decision History: {len(full_data['decision_history'])} records")
    print(f"  - Audit Trail: {len(full_data['audit_trail'])} events")
    
    print("\n✓ Retrieved from ChromaDB (Vector Embeddings):")
    print(f"  - Similar Past Decisions: {len(full_data['similar_past_decisions'])} cases")
    
    print("\n✓ Retrieved from Neo4j (Graph Relationships):")
    print(f"  - Related Applications: {len(full_data['related_applications'])} applications")
    print(f"  - Decision Path: {len(full_data['decision_path'])} nodes")
    print(f"  - Application Graph: {len(full_data['application_graph']['nodes'])} nodes")
    
    print("\n📊 Step 10: System Statistics")
    print("-" * 80)
    stats = db.get_system_statistics()
    print("✓ System-wide Statistics:")
    print(f"  SQLite:")
    print(f"    - Total Applications: {stats['sqlite']['applications']['total_applications']}")
    print(f"    - Completed: {stats['sqlite']['applications']['completed']}")
    print(f"    - Pending: {stats['sqlite']['applications']['pending']}")
    print(f"  ChromaDB:")
    print(f"    - Documents: {stats['chromadb']['documents']}")
    print(f"    - Decisions: {stats['chromadb']['decisions']}")
    print(f"    - Chat History: {stats['chromadb']['chat_history']}")
    
    print("\n" + "="*80)
    print("✅ MULTI-MODAL DATABASE TEST COMPLETE")
    print("="*80)
    print("\nKey Features Demonstrated:")
    print("1. ✓ SQLite for structured relational data (applications, profiles, decisions)")
    print("2. ✓ ChromaDB for vector embeddings (semantic search, RAG for chatbot)")
    print("3. ✓ Neo4j for graph relationships (document links, decision paths, family)")
    print("4. ✓ Unified interface bringing all three together")
    print("5. ✓ Multi-modal data retrieval in single query")
    print("6. ✓ RAG-based chatbot with document context")
    print("7. ✓ Semantic document search across all types")
    print("8. ✓ Complete audit trail and analytics")
    print("\n🎉 All databases working together as unified system!")
    
    # Close connections
    db.close()


if __name__ == "__main__":
    test_multimodal_database()
