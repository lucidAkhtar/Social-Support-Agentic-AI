"""
ChromaDB Indexing Script - Production-Grade
Properly index all 40 applications into ChromaDB with chunking and embeddings

This script:
1. Loads application data from metadata.json files
2. Chunks long text appropriately
3. Generates embeddings automatically
4. Indexes into 4 collections with proper metadata

Usage:
    poetry run python index_chromadb.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.databases.chroma_manager import ChromaDBManager

def main():
    print("=" * 80)
    print("CHROMADB INDEXING - Production Grade")
    print("=" * 80)
    
    # Initialize ChromaDB
    print("\n📊 Initializing ChromaDB...")
    chroma = ChromaDBManager("data/databases/chromadb_rag")
    
    # Check existing data
    stats = chroma.get_collection_stats()
    print(f"\nCurrent document counts:")
    for collection, count in stats.items():
        print(f"   {collection}: {count} docs")
    
    # Ask for confirmation if data exists
    if stats['total'] > 0:
        response = input(f"\n⚠️  {stats['total']} documents already indexed. Reset and reindex? (yes/no): ")
        if response.lower() != 'yes':
            print("Aborted.")
            return
        
        print("\n🗑️  Resetting all collections...")
        chroma.reset_all_collections()
    
    # Load applications from disk
    docs_dir = Path("data/processed/documents")
    if not docs_dir.exists():
        print(f"\n❌ Error: {docs_dir} not found")
        print("Run generate_full_dataset.py first to create application data")
        return
    
    applications = sorted(docs_dir.glob("APP-*"))
    print(f"\n📂 Found {len(applications)} applications to index")
    
    # Index each application
    indexed_count = 0
    error_count = 0
    
    for app_dir in applications:
        app_id = app_dir.name
        
        try:
            # Load metadata
            metadata_file = app_dir / "metadata.json"
            if not metadata_file.exists():
                print(f"⚠️  Skipping {app_id}: metadata.json not found")
                error_count += 1
                continue
            
            with open(metadata_file) as f:
                metadata = json.load(f)
            
            profile = metadata['profile']
            decision = metadata.get('ml_decision', {})
            
            # 1. Index application summary
            summary_data = {
                "applicant_name": metadata['applicant_name'],
                "employment_status": profile['employment_status'],
                "monthly_income": profile['monthly_income'],
                "family_size": profile['family_size'],
                "policy_score": metadata.get('policy_score', 0),
                "eligibility": decision.get('decision_type', 'UNKNOWN')
            }
            chroma.index_application_summary(app_id, summary_data)
            
            # 2. Index income pattern
            income_data = {
                "monthly_income": profile['monthly_income'],
                "monthly_expenses": profile['monthly_expenses'],
                "net_worth": profile['total_assets'] - profile['total_liabilities'],
                "debt_to_income_ratio": profile['monthly_expenses'] / max(profile['monthly_income'], 1),
                "employment_status": profile['employment_status'],
                "credit_score": profile['credit_score']
            }
            chroma.index_income_pattern(app_id, income_data)
            
            # 3. Index case decision
            decision_data = {
                "decision_type": decision.get('decision_type', 'UNKNOWN'),
                "support_amount": decision.get('support_amount', 0),
                "policy_score": metadata.get('policy_score', 0),
                "reasoning": decision.get('reasoning', f"Policy score: {metadata.get('policy_score', 0)}")
            }
            chroma.index_case_decision(app_id, decision_data)
            
            indexed_count += 1
            
            if indexed_count % 10 == 0:
                print(f"   Indexed {indexed_count}/{len(applications)} applications...")
            
        except Exception as e:
            print(f"❌ Error indexing {app_id}: {e}")
            error_count += 1
            continue
    
    # Final statistics
    print(f"\n✅ Indexing complete!")
    print(f"   Successful: {indexed_count}")
    print(f"   Errors: {error_count}")
    
    # Verify indexing
    print("\n📊 Final document counts:")
    stats = chroma.get_collection_stats()
    for collection, count in stats.items():
        print(f"   {collection}: {count} docs")
    
    # Test semantic search
    print("\n🔍 Testing semantic search...")
    test_queries = [
        "low income large family unemployed",
        "government employee stable income",
        "high debt credit issues"
    ]
    
    for query in test_queries:
        results = chroma.query(query, n_results=3)
        result_count = len(results['ids'][0]) if results['ids'] else 0
        print(f"   '{query}': {result_count} results")
    
    print("\n" + "=" * 80)
    print("CHROMADB INDEXING COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Test API: curl http://localhost:8000/test/chromadb/collection-info")
    print("2. Test search: curl http://localhost:8000/test/chromadb/semantic-search")
    print("3. Open Swagger UI: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
