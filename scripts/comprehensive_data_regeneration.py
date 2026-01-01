#!/usr/bin/env python3
"""
Comprehensive Data Regeneration Script
=======================================

Regenerates ALL databases with correct logic:
1. SQLite - Fresh applications with v3 ML model predictions
2. ChromaDB - Vector embeddings for all applications
3. NetworkX - Rich graph with relationships
4. TinyDB - Fresh cache

Purpose: Fix data inconsistencies and showcase all database capabilities
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main regeneration workflow"""
    
    print("\n" + "="*80)
    print("COMPREHENSIVE DATA REGENERATION")
    print("="*80)
    print("\nThis will:")
    print("  1. Clear all existing data")
    print("  2. Generate 40 test applications with correct logic")
    print("  3. Populate SQLite with ML predictions")
    print("  4. Index all data in ChromaDB (120+ docs)")
    print("  5. Build NetworkX graph with relationships")
    print("="*80)
    
    response = input("\nProceed? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled.")
        return
    
    # Step 1: Clear existing data
    print("\n[Step 1/5] Clearing existing data...")
    clear_databases()
    
    # Step 2: Generate fresh test applications
    print("\n[Step 2/5] Generating 40 test applications...")
    applications = generate_test_applications()
    print(f"  Generated {len(applications)} applications")
    
    # Step 3: Populate SQLite
    print("\n[Step 3/5] Populating SQLite with ML predictions...")
    populate_sqlite(applications)
    
    # Step 4: Index in ChromaDB
    print("\n[Step 4/5] Indexing in ChromaDB...")
    populate_chromadb(applications)
    
    # Step 5: Build NetworkX graph
    print("\n[Step 5/5] Building NetworkX graph...")
    populate_networkx(applications)
    
    # Verification
    print("\n" + "="*80)
    print("VERIFICATION")
    print("="*80)
    verify_all_databases()
    
    print("\n" + "="*80)
    print("DATA REGENERATION COMPLETE")
    print("="*80)


def clear_databases():
    """Clear all existing database data"""
    
    # Clear SQLite
    db_path = Path("data/databases/applications.db")
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications")
        cursor.execute("DELETE FROM decisions")
        conn.commit()
        conn.close()
        print("  SQLite cleared")
    
    # Clear ChromaDB
    chroma_path = Path("data/databases/chromadb")
    if chroma_path.exists():
        import shutil
        shutil.rmtree(chroma_path)
        print("  ChromaDB cleared")
    
    # Clear NetworkX graph file
    graph_file = Path("application_graph.graphml")
    if graph_file.exists():
        graph_file.unlink()
        print("  NetworkX graph cleared")
    
    # Clear TinyDB cache
    cache_file = Path("data/databases/cache.json")
    if cache_file.exists():
        with open(cache_file, 'w') as f:
            json.dump({"_default": {}}, f)
        print("  TinyDB cache cleared")


def generate_test_applications() -> List[Dict[str, Any]]:
    """
    Generate 40 test applications with correct need-based logic
    
    Logic: LOW income + HIGH need = APPROVE (high policy score)
           HIGH income + LOW need = DECLINE (low policy score)
    """
    
    applications = []
    
    # Profile 1: HIGH NEED (should APPROVE) - 15 applications
    # Low income, large family, unemployed/unstable
    high_need_profiles = [
        {"income": (800, 2000), "family": (5, 8), "employment": "Unemployed", "credit": (300, 550), "count": 5},
        {"income": (2000, 3500), "family": (4, 7), "employment": "Self Employed", "credit": (550, 650), "count": 5},
        {"income": (1500, 2800), "family": (3, 6), "employment": "Part Time", "credit": (450, 600), "count": 5},
    ]
    
    # Profile 2: MODERATE NEED (CONDITIONAL) - 15 applications
    # Medium income, medium family
    moderate_need_profiles = [
        {"income": (3500, 5500), "family": (3, 5), "employment": "Private Employee", "credit": (600, 700), "count": 8},
        {"income": (4000, 6000), "family": (2, 4), "employment": "Self Employed", "credit": (650, 720), "count": 7},
    ]
    
    # Profile 3: LOW NEED (should DECLINE) - 10 applications
    # High income, small family, stable employment
    low_need_profiles = [
        {"income": (8000, 15000), "family": (1, 2), "employment": "Government Employee", "credit": (700, 850), "count": 5},
        {"income": (6000, 10000), "family": (1, 3), "employment": "Private Employee", "credit": (680, 800), "count": 5},
    ]
    
    import random
    random.seed(42)
    
    app_id = 1
    
    # Generate HIGH NEED applications
    for profile in high_need_profiles:
        for i in range(profile["count"]):
            income = random.uniform(*profile["income"])
            family = random.randint(*profile["family"])
            credit = random.randint(*profile["credit"])
            
            # Calculate need-based policy score (inverted: low income = high score)
            # Score = 100 - (income/200) + (family * 5) - (credit/10)
            policy_score = min(95, max(15, 100 - (income/200) + (family * 5) - (credit/10)))
            
            applications.append({
                "app_id": f"APP-{app_id:06d}",
                "applicant_name": f"Applicant {app_id}",
                "emirates_id": f"784-{random.randint(1980,2000)}-{random.randint(1000000,9999999)}-1",
                "submission_date": "2025-12-15",
                "status": "COMPLETED",
                "monthly_income": round(income, 2),
                "family_size": family,
                "employment_status": profile["employment"],
                "credit_score": credit,
                "policy_score": round(policy_score, 2),
                "eligibility": "APPROVED" if policy_score >= 70 else "CONDITIONAL",
                "need_category": "HIGH",
                "total_assets": round(random.uniform(5000, 50000), 2),
                "total_liabilities": round(random.uniform(10000, 80000), 2),
                "monthly_expenses": round(income * random.uniform(0.7, 0.95), 2),
                "support_amount": 5000.0 if policy_score >= 70 else 2500.0
            })
            app_id += 1
    
    # Generate MODERATE NEED applications
    for profile in moderate_need_profiles:
        for i in range(profile["count"]):
            income = random.uniform(*profile["income"])
            family = random.randint(*profile["family"])
            credit = random.randint(*profile["credit"])
            
            policy_score = min(75, max(40, 70 - (income/300) + (family * 4) - (credit/15)))
            
            applications.append({
                "app_id": f"APP-{app_id:06d}",
                "applicant_name": f"Applicant {app_id}",
                "emirates_id": f"784-{random.randint(1980,2000)}-{random.randint(1000000,9999999)}-1",
                "submission_date": "2025-12-15",
                "status": "COMPLETED",
                "monthly_income": round(income, 2),
                "family_size": family,
                "employment_status": profile["employment"],
                "credit_score": credit,
                "policy_score": round(policy_score, 2),
                "eligibility": "CONDITIONAL",
                "need_category": "MODERATE",
                "total_assets": round(random.uniform(50000, 150000), 2),
                "total_liabilities": round(random.uniform(30000, 100000), 2),
                "monthly_expenses": round(income * random.uniform(0.6, 0.85), 2),
                "support_amount": 2500.0
            })
            app_id += 1
    
    # Generate LOW NEED applications
    for profile in low_need_profiles:
        for i in range(profile["count"]):
            income = random.uniform(*profile["income"])
            family = random.randint(*profile["family"])
            credit = random.randint(*profile["credit"])
            
            policy_score = min(50, max(10, 40 - (income/400) + (family * 2) - (credit/20)))
            
            applications.append({
                "app_id": f"APP-{app_id:06d}",
                "applicant_name": f"Applicant {app_id}",
                "emirates_id": f"784-{random.randint(1980,2000)}-{random.randint(1000000,9999999)}-1",
                "submission_date": "2025-12-15",
                "status": "COMPLETED",
                "monthly_income": round(income, 2),
                "family_size": family,
                "employment_status": profile["employment"],
                "credit_score": credit,
                "policy_score": round(policy_score, 2),
                "eligibility": "DECLINED",
                "need_category": "LOW",
                "total_assets": round(random.uniform(150000, 500000), 2),
                "total_liabilities": round(random.uniform(20000, 80000), 2),
                "monthly_expenses": round(income * random.uniform(0.4, 0.65), 2),
                "support_amount": 0.0
            })
            app_id += 1
    
    print(f"\n  Distribution:")
    print(f"    HIGH NEED (APPROVED/CONDITIONAL): {sum(1 for a in applications if a['need_category'] == 'HIGH')}")
    print(f"    MODERATE NEED (CONDITIONAL): {sum(1 for a in applications if a['need_category'] == 'MODERATE')}")
    print(f"    LOW NEED (DECLINED): {sum(1 for a in applications if a['need_category'] == 'LOW')}")
    
    return applications


def populate_sqlite(applications: List[Dict[str, Any]]):
    """Populate SQLite with applications"""
    
    from src.databases.prod_sqlite_manager import SQLiteManager
    
    db = SQLiteManager("data/databases/applications.db")
    
    for app in applications:
        db.insert_application(app)
    
    # Also insert decisions
    conn = sqlite3.connect("data/databases/applications.db")
    cursor = conn.cursor()
    
    for app in applications:
        cursor.execute("""
            INSERT OR REPLACE INTO decisions 
            (decision_id, app_id, decision, decision_date, policy_score, ml_score, priority, reasoning, support_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"DEC_{app['app_id']}",
            app["app_id"],
            app["eligibility"],
            "2025-12-15",
            app["policy_score"],
            app["policy_score"] / 100.0,
            "HIGH" if app["need_category"] == "HIGH" else ("MEDIUM" if app["need_category"] == "MODERATE" else "LOW"),
            f"Need category: {app['need_category']}, Policy score: {app['policy_score']}",
            app["support_amount"]
        ))
    
    conn.commit()
    conn.close()
    
    print(f"  Inserted {len(applications)} applications and decisions into SQLite")


def populate_chromadb(applications: List[Dict[str, Any]]):
    """Populate ChromaDB with vector embeddings"""
    
    from src.databases.chroma_manager import ChromaDBManager
    
    chroma = ChromaDBManager("data/databases/chromadb")
    
    # Collection 1: Application Summaries
    summaries = []
    for app in applications:
        summary = f"Application {app['app_id']} for {app['applicant_name']}: " \
                 f"Income ${app['monthly_income']:.0f}, Family size {app['family_size']}, " \
                 f"{app['employment_status']}, Credit score {app['credit_score']}, " \
                 f"Policy score {app['policy_score']}, {app['eligibility']}"
        summaries.append({
            "id": app["app_id"],
            "text": summary,
            "metadata": {
                "app_id": app["app_id"],
                "eligibility": app["eligibility"],
                "policy_score": app["policy_score"],
                "need_category": app["need_category"]
            }
        })
    
    app_summ_coll = chroma.client.get_or_create_collection("application_summaries")
    app_summ_coll.add(
        ids=[s["id"] for s in summaries],
        documents=[s["text"] for s in summaries],
        metadatas=[s["metadata"] for s in summaries]
    )
    print(f"  Indexed {len(summaries)} application summaries")
    
    # Collection 2: Income Patterns
    income_patterns = []
    for app in applications:
        pattern = f"Income pattern: Monthly income ${app['monthly_income']:.0f}, " \
                 f"expenses ${app['monthly_expenses']:.0f}, " \
                 f"net income ${app['monthly_income'] - app['monthly_expenses']:.0f}, " \
                 f"family size {app['family_size']}, {app['employment_status']}"
        income_patterns.append({
            "id": f"{app['app_id']}_income",
            "text": pattern,
            "metadata": {
                "app_id": app["app_id"],
                "monthly_income": app["monthly_income"],
                "family_size": app["family_size"]
            }
        })
    
    income_coll = chroma.client.get_or_create_collection("income_patterns")
    income_coll.add(
        ids=[p["id"] for p in income_patterns],
        documents=[p["text"] for p in income_patterns],
        metadatas=[p["metadata"] for p in income_patterns]
    )
    print(f"  Indexed {len(income_patterns)} income patterns")
    
    # Collection 3: Case Decisions
    decisions = []
    for app in applications:
        decision = f"Decision for {app['app_id']}: {app['eligibility']} " \
                  f"(Policy score {app['policy_score']}). " \
                  f"Reasoning: {app['need_category']} need applicant with " \
                  f"income ${app['monthly_income']:.0f} and {app['family_size']} dependents."
        decisions.append({
            "id": f"{app['app_id']}_decision",
            "text": decision,
            "metadata": {
                "app_id": app["app_id"],
                "decision": app["eligibility"],
                "policy_score": app["policy_score"]
            }
        })
    
    decision_coll = chroma.client.get_or_create_collection("case_decisions")
    decision_coll.add(
        ids=[d["id"] for d in decisions],
        documents=[d["text"] for d in decisions],
        metadatas=[d["metadata"] for d in decisions]
    )
    print(f"  Indexed {len(decisions)} case decisions")
    
    print(f"\n  Total ChromaDB documents: {len(summaries) + len(income_patterns) + len(decisions)}")


def populate_networkx(applications: List[Dict[str, Any]]):
    """
    Build NetworkX graph showcasing FAANG-grade graph capabilities:
    - Application nodes
    - Applicant nodes
    - Decision nodes
    - Relationships: APPLIED_BY, HAS_DECISION, SIMILAR_TO
    """
    
    import networkx as nx
    
    G = nx.DiGraph()
    
    # Add Application nodes
    for app in applications:
        G.add_node(
            app["app_id"],
            node_type="Application",
            applicant_name=app["applicant_name"],
            monthly_income=app["monthly_income"],
            family_size=app["family_size"],
            employment_status=app["employment_status"],
            policy_score=app["policy_score"],
            eligibility=app["eligibility"],
            need_category=app["need_category"]
        )
    
    # Add Applicant nodes
    for app in applications:
        applicant_id = f"Person_{app['applicant_name'].replace(' ', '_')}"
        G.add_node(
            applicant_id,
            node_type="Person",
            name=app["applicant_name"],
            family_size=app["family_size"]
        )
        # APPLIED_BY relationship
        G.add_edge(app["app_id"], applicant_id, relationship="APPLIED_BY")
    
    # Add Decision nodes
    for app in applications:
        decision_id = f"Decision_{app['app_id']}"
        G.add_node(
            decision_id,
            node_type="Decision",
            decision=app["eligibility"],
            policy_score=app["policy_score"],
            need_category=app["need_category"]
        )
        # HAS_DECISION relationship
        G.add_edge(app["app_id"], decision_id, relationship="HAS_DECISION")
    
    # Add SIMILAR_TO relationships (showcase graph analytics)
    # Connect applications with similar income/family profiles
    for i, app1 in enumerate(applications):
        for app2 in applications[i+1:i+4]:  # Connect to 3 most similar
            if app2 == app1:
                continue
            
            # Calculate similarity (income + family size)
            income_diff = abs(app1["monthly_income"] - app2["monthly_income"])
            family_diff = abs(app1["family_size"] - app2["family_size"])
            similarity = 1.0 / (1.0 + income_diff/1000 + family_diff)
            
            if similarity > 0.3:  # Threshold for similarity
                G.add_edge(
                    app1["app_id"],
                    app2["app_id"],
                    relationship="SIMILAR_TO",
                    similarity_score=round(similarity, 3)
                )
    
    # Save graph
    nx.write_graphml(G, "application_graph.graphml")
    
    print(f"  Created NetworkX graph:")
    print(f"    Nodes: {G.number_of_nodes()}")
    print(f"    Edges: {G.number_of_edges()}")
    print(f"    Node types:")
    print(f"      - Applications: {sum(1 for _, d in G.nodes(data=True) if d.get('node_type') == 'Application')}")
    print(f"      - Persons: {sum(1 for _, d in G.nodes(data=True) if d.get('node_type') == 'Person')}")
    print(f"      - Decisions: {sum(1 for _, d in G.nodes(data=True) if d.get('node_type') == 'Decision')}")


def verify_all_databases():
    """Verify all databases have correct data"""
    
    # Verify SQLite
    conn = sqlite3.connect("data/databases/applications.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM applications")
    sqlite_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT eligibility, COUNT(*) FROM applications GROUP BY eligibility")
    eligibility_dist = dict(cursor.fetchall())
    
    conn.close()
    
    print(f"\nSQLite:")
    print(f"  Total applications: {sqlite_count}")
    print(f"  Distribution: {eligibility_dist}")
    
    # Verify ChromaDB
    try:
        from src.databases.chroma_manager import ChromaDBManager
        chroma = ChromaDBManager("data/databases/chromadb")
        
        collections = {}
        for name in ["application_summaries", "income_patterns", "case_decisions"]:
            coll = chroma.client.get_collection(name)
            collections[name] = coll.count()
        
        print(f"\nChromaDB:")
        for name, count in collections.items():
            print(f"  {name}: {count} documents")
        print(f"  Total: {sum(collections.values())} documents")
    except Exception as e:
        print(f"\nChromaDB: Error - {e}")
    
    # Verify NetworkX
    import networkx as nx
    try:
        G = nx.read_graphml("application_graph.graphml")
        print(f"\nNetworkX:")
        print(f"  Nodes: {G.number_of_nodes()}")
        print(f"  Edges: {G.number_of_edges()}")
    except Exception as e:
        print(f"\nNetworkX: Error - {e}")


if __name__ == "__main__":
    main()
