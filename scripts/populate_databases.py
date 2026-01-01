"""
Populate All Databases with Diverse Dataset
Loads 40 applications from fix_dataset_generation.py into SQLite, ChromaDB, NetworkX
Ensures data consistency across all databases
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.databases.prod_sqlite_manager import SQLiteManager
from src.databases.chroma_manager import ChromaDBManager
from src.databases.networkx_manager import NetworkXManager

def load_applications_from_disk() -> List[Dict]:
    """Load all 40 applications from processed documents"""
    docs_dir = Path("data/processed/documents")
    applications = []
    
    print("📂 Loading applications from disk...")
    
    for app_dir in sorted(docs_dir.glob("APP-*")):
        app_id = app_dir.name
        
        # Load metadata first (has policy_score)
        metadata_file = app_dir / "metadata.json"
        if not metadata_file.exists():
            print(f"⚠️  Skipping {app_id}: metadata.json not found")
            continue
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        profile = metadata['profile']
        
        # Build application data
        app_data = {
            "app_id": app_id,
            "applicant_name": metadata['applicant_name'],
            "emirates_id": metadata['emirates_id'],
            "submission_date": datetime.now().strftime("%Y-%m-%d"),
            "status": "PROCESSED",
            "monthly_income": profile['monthly_income'],
            "monthly_expenses": profile['monthly_expenses'],
            "family_size": profile['family_size'],
            "employment_status": profile['employment_status'],
            "total_assets": profile['total_assets'],
            "total_liabilities": profile['total_liabilities'],
            "credit_score": profile['credit_score'],
            "policy_score": metadata['policy_score'],
            "eligibility": None,  # Will be set based on policy score
            "support_amount": None
        }
        
        # Determine eligibility based on policy score
        if app_data["policy_score"]:
            if app_data["policy_score"] >= 70:
                app_data["eligibility"] = "APPROVED"
                app_data["support_amount"] = 5000.0
            elif app_data["policy_score"] >= 50:
                app_data["eligibility"] = "APPROVED"
                app_data["support_amount"] = 3000.0
            elif app_data["policy_score"] >= 30:
                app_data["eligibility"] = "CONDITIONAL"
                app_data["support_amount"] = 1500.0
            else:
                app_data["eligibility"] = "DECLINED"
                app_data["support_amount"] = 0.0
        
        applications.append(app_data)
    
    print(f"✅ Loaded {len(applications)} applications from disk")
    return applications


def populate_sqlite(applications: List[Dict]):
    """Populate SQLite with applications and decisions"""
    print("\n🗄️  Populating SQLite database...")
    
    sqlite_db = SQLiteManager("data/databases/applications.db")
    
    for app in applications:
        # Insert application
        sqlite_db.insert_application(app)
        
        # Create decision record
        if app.get("policy_score"):
            decision_data = {
                "decision_id": f"DEC-{app['app_id']}",
                "app_id": app["app_id"],
                "decision": app["eligibility"],
                "decision_date": datetime.now().strftime("%Y-%m-%d"),
                "decided_by": "SYSTEM",
                "policy_score": app["policy_score"],
                "ml_score": None,  # Will be populated after ML model
                "priority": "HIGH" if app["policy_score"] >= 70 else "MEDIUM" if app["policy_score"] >= 50 else "LOW",
                "reasoning": f"Policy score: {app['policy_score']:.1f}. Based on income, family size, and credit score.",
                "support_type": "MONTHLY_ALLOWANCE" if app["eligibility"] == "APPROVED" else None,
                "support_amount": app["support_amount"],
                "duration_months": 12 if app["eligibility"] == "APPROVED" else None,
                "conditions": "Subject to quarterly review" if app["eligibility"] == "CONDITIONAL" else None
            }
            sqlite_db.insert_decision(decision_data)
    
    # Verify
    stats = sqlite_db.get_eligibility_stats()
    print(f"✅ SQLite populated: {stats['total_applications']} applications")
    print(f"   - Approved: {stats['approved']}")
    print(f"   - Conditional: {stats['conditional']}")
    print(f"   - Declined: {stats['declined']}")
    
    sqlite_db.close()


def populate_chromadb(applications: List[Dict]):
    """Index documents into ChromaDB for semantic search"""
    print("\n🔍 Indexing documents into ChromaDB...")
    
    chroma_db = ChromaDBManager("data/databases/chromadb_rag")
    
    docs_dir = Path("data/processed/documents")
    doc_count = 0
    
    for app in applications:
        app_id = app["app_id"]
        app_dir = docs_dir / app_id
        
        if not app_dir.exists():
            continue
        
        for doc_file in app_dir.glob("*.json"):
            with open(doc_file) as f:
                doc_data = json.load(f)
            
            # Create searchable text
            text_parts = [
                f"Application: {app_id}",
                f"Applicant: {app['applicant_name']}",
                f"Income: {app['monthly_income']} AED",
                f"Family size: {app['family_size']}",
                f"Employment: {app['employment_status']}",
                f"Credit score: {app['credit_score']}",
                f"Document type: {doc_file.stem}",
                json.dumps(doc_data, indent=2)
            ]
            
            # Add document using the correct API
            metadata = {
                "applicant_name": app["applicant_name"],
                "monthly_income": float(app["monthly_income"]),
                "family_size": int(app["family_size"])
            }
            # Only add policy_score if it's not None
            if app.get("policy_score") is not None:
                metadata["policy_score"] = float(app["policy_score"])
            
            chroma_db.add_document_embedding(
                application_id=app_id,
                document_type=doc_file.stem,
                text_content="\n".join(text_parts),
                metadata=metadata
            )
            doc_count += 1
    
    count = chroma_db.documents_collection.count()
    print(f"✅ ChromaDB indexed: {count} documents from {len(applications)} applications")


def populate_networkx(applications: List[Dict]):
    """Build NetworkX graph from applications"""
    print("\n🕸️  Building NetworkX graph...")
    
    import networkx as nx
    
    G = nx.DiGraph()
    
    docs_dir = Path("data/processed/documents")
    
    for app in applications:
        app_id = app["app_id"]
        
        # Add Person node
        person_id = f"PERSON-{app['emirates_id']}"
        G.add_node(person_id, 
                   node_type="Person",
                   name=app["applicant_name"],
                   emirates_id=app["emirates_id"])
        
        # Add Application node
        G.add_node(app_id,
                   node_type="Application",
                   submission_date=app["submission_date"],
                   status=app["status"],
                   monthly_income=float(app["monthly_income"]),
                   family_size=int(app["family_size"]),
                   policy_score=float(app.get("policy_score")) if app.get("policy_score") is not None else 0.0,
                   eligibility=app.get("eligibility") or "UNKNOWN")
        
        # Add edge: Person -> Application
        G.add_edge(person_id, app_id, edge_type="HAS_APPLICATION")
        
        # Add Document nodes
        app_dir = docs_dir / app_id
        if app_dir.exists():
            for doc_file in app_dir.glob("*.json"):
                doc_id = f"{app_id}_{doc_file.stem}"
                G.add_node(doc_id,
                           node_type="Document",
                           document_type=doc_file.stem,
                           file_path=str(doc_file))
                G.add_edge(app_id, doc_id, edge_type="HAS_DOCUMENT")
        
        # Add Decision node
        if app.get("eligibility"):
            decision_id = f"DEC-{app_id}"
            G.add_node(decision_id,
                       node_type="Decision",
                       decision=app["eligibility"],
                       policy_score=float(app.get("policy_score")) if app.get("policy_score") is not None else 0.0,
                       support_amount=float(app.get("support_amount")) if app.get("support_amount") is not None else 0.0)
            G.add_edge(app_id, decision_id, edge_type="HAS_DECISION")
    
    # Save graph
    graph_path = Path("application_graph.graphml")
    nx.write_graphml(G, str(graph_path))
    
    print(f"✅ NetworkX graph built: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    print(f"   Saved to: {graph_path}")
    
    # Statistics
    node_types = {}
    for node, attrs in G.nodes(data=True):
        node_type = attrs.get('node_type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    print(f"   Node distribution: {node_types}")


def verify_integration(expected_apps: int):
    """Verify all databases have consistent data"""
    print("\n🔬 Verifying integration...")
    
    # Check SQLite
    sqlite_db = SQLiteManager("data/databases/applications.db")
    stats = sqlite_db.get_eligibility_stats()
    sqlite_count = stats.get('total_applications', 0)
    print(f"   SQLite: {sqlite_count} applications")
    sqlite_db.close()
    
    # Check ChromaDB
    chroma_db = ChromaDBManager("data/databases/chromadb_rag")
    chroma_count = chroma_db.documents_collection.count()
    expected_docs = expected_apps * 6  # Each app has ~6 documents
    print(f"   ChromaDB: {chroma_count} documents (expected ~{expected_docs})")
    
    # Check NetworkX
    import networkx as nx
    graph_path = Path("application_graph.graphml")
    if graph_path.exists():
        G = nx.read_graphml(str(graph_path))
        app_nodes = sum(1 for n, attrs in G.nodes(data=True) if attrs.get('node_type') == 'Application')
        print(f"   NetworkX: {app_nodes} application nodes")
    else:
        print("   NetworkX: Graph file not found")
    
    # Validation
    if sqlite_count == expected_apps:
        print("✅ Integration verified: All databases consistent")
        return True
    else:
        print(f"⚠️  Mismatch: Expected {expected_apps} apps, SQLite has {sqlite_count}")
        return False


def main():
    print("="*80)
    print("DATABASE POPULATION SCRIPT")
    print("Populating SQLite, ChromaDB, and NetworkX with 40 diverse applications")
    print("="*80)
    
    # Step 1: Load applications
    applications = load_applications_from_disk()
    
    if len(applications) < 40:
        print(f"\n⚠️  Warning: Only found {len(applications)} applications (expected 40)")
        print("   Make sure you ran: poetry run python fix_dataset_generation.py")
        proceed = input("   Continue anyway? (y/n): ")
        if proceed.lower() != 'y':
            print("Aborted.")
            return
    
    # Step 2: Populate SQLite
    populate_sqlite(applications)
    
    # Step 3: Populate ChromaDB
    populate_chromadb(applications)
    
    # Step 4: Populate NetworkX
    populate_networkx(applications)
    
    # Step 5: Verify integration
    verify_integration(len(applications))
    
    print("\n" + "="*80)
    print("DATABASE POPULATION COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Run ML model training: poetry run python train_ml_model_v2.py")
    print("2. Test endpoints: poetry run python fastapi_test_endpoints.py")
    print("3. Test integration: curl http://localhost:8000/test/integration/verify-all")


if __name__ == "__main__":
    main()
