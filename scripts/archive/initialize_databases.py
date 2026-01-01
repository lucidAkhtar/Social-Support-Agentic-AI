#!/usr/bin/env python
"""
Production Database Initialization Script
Initializes ALL 4 databases with schema, indexes, and sample data

Databases:
1. SQLite (Relational) - Applications, profiles, decisions
2. MongoDB (NoSQL) - Unstructured data, raw documents, OCR results
3. ChromaDB (Vector) - Embeddings for semantic search
4. Neo4j (Graph) - Relationships, family trees, document connections
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_sqlite():
    """Initialize SQLite with full production schema"""
    print("\n" + "="*70)
    print("1. INITIALIZING SQLITE (RELATIONAL DATABASE)")
    print("="*70)
    
    db_path = "data/databases/applications.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Applications table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            application_id TEXT PRIMARY KEY,
            applicant_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            current_stage TEXT DEFAULT 'not_started'
        )
    """)
    
    # Applicant profiles table with FULL details
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applicant_profiles (
            application_id TEXT PRIMARY KEY,
            full_name TEXT,
            id_number TEXT,
            date_of_birth TEXT,
            nationality TEXT,
            contact_number TEXT,
            email TEXT,
            address TEXT,
            monthly_income REAL,
            monthly_expenses REAL,
            employment_status TEXT,
            current_position TEXT,
            years_experience INTEGER,
            industry TEXT,
            total_assets REAL,
            total_liabilities REAL,
            net_worth REAL,
            credit_score INTEGER,
            outstanding_debt REAL,
            family_size INTEGER,
            dependents INTEGER,
            has_disabilities INTEGER DEFAULT 0,
            special_needs TEXT,
            profile_data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(application_id)
        )
    """)
    
    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            document_type TEXT NOT NULL,
            file_path TEXT,
            file_size INTEGER,
            mime_type TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed INTEGER DEFAULT 0,
            extraction_status TEXT DEFAULT 'pending',
            FOREIGN KEY (application_id) REFERENCES applications(application_id)
        )
    """)
    
    # Validation results table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS validation_results (
            validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            is_valid INTEGER NOT NULL,
            data_completeness_score REAL,
            confidence_score REAL,
            critical_issues INTEGER DEFAULT 0,
            warnings INTEGER DEFAULT 0,
            info_notices INTEGER DEFAULT 0,
            issues_json TEXT,
            validation_metadata_json TEXT,
            validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(application_id)
        )
    """)
    
    # Decisions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            decision_type TEXT NOT NULL,
            eligibility_score REAL,
            ml_prediction TEXT,
            ml_confidence REAL,
            policy_rules_met INTEGER,
            need_level TEXT,
            income_level TEXT,
            wealth_level TEXT,
            employment_level TEXT,
            reasons_json TEXT,
            reasoning TEXT,
            decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(application_id)
        )
    """)
    
    # Recommendations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            decision_type TEXT NOT NULL,
            financial_support_amount REAL,
            financial_support_type TEXT,
            programs_json TEXT,
            key_factors_json TEXT,
            reasoning TEXT,
            recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(application_id)
        )
    """)
    
    # Audit log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT,
            agent_name TEXT NOT NULL,
            action TEXT NOT NULL,
            action_category TEXT,
            details_json TEXT,
            user_id TEXT,
            ip_address TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            query_type TEXT,
            response_sources TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (application_id) REFERENCES applications(application_id)
        )
    """)
    
    # Create indexes for performance
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_stage ON applications(current_stage)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_app ON documents(application_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_docs_type ON documents(document_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_val_app ON validation_results(application_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dec_app ON decisions(application_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_rec_app ON recommendations(application_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_app ON audit_log(application_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_time ON audit_log(timestamp)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chat_app ON chat_history(application_id)")
    
    conn.commit()
    
    # Verify tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print(f"✅ SQLite initialized: {db_path}")
    print(f"   Tables created: {len(tables)}")
    for table in tables:
        print(f"      - {table}")
    
    conn.close()
    return True


def initialize_mongodb():
    """Initialize MongoDB with collections"""
    print("\n" + "="*70)
    print("2. INITIALIZING MONGODB (NoSQL DATABASE)")
    print("="*70)
    
    try:
        from pymongo import MongoClient, ASCENDING, DESCENDING
        
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        
        db = client['social_support_system']
        
        # Collections for unstructured data
        collections = [
            'raw_documents',       # Original document data
            'ocr_results',         # Raw OCR text output
            'llm_responses',       # LLM analysis results
            'extraction_cache',    # Cached extraction results
            'validation_cache',    # Cached validation results
            'user_sessions',       # User interaction data
            'system_metrics',      # Performance metrics
            'error_logs'           # Error tracking
        ]
        
        for coll_name in collections:
            if coll_name not in db.list_collection_names():
                db.create_collection(coll_name)
        
        # Create indexes
        db.raw_documents.create_index([("application_id", ASCENDING)])
        db.raw_documents.create_index([("document_type", ASCENDING)])
        db.raw_documents.create_index([("uploaded_at", DESCENDING)])
        
        db.ocr_results.create_index([("application_id", ASCENDING)])
        db.ocr_results.create_index([("document_id", ASCENDING)])
        
        db.llm_responses.create_index([("application_id", ASCENDING)])
        db.llm_responses.create_index([("query_type", ASCENDING)])
        db.llm_responses.create_index([("timestamp", DESCENDING)])
        
        db.extraction_cache.create_index([("application_id", ASCENDING)], unique=True)
        db.validation_cache.create_index([("application_id", ASCENDING)], unique=True)
        
        db.user_sessions.create_index([("session_id", ASCENDING)], unique=True)
        db.user_sessions.create_index([("created_at", DESCENDING)])
        
        db.system_metrics.create_index([("metric_type", ASCENDING)])
        db.system_metrics.create_index([("timestamp", DESCENDING)])
        
        db.error_logs.create_index([("level", ASCENDING)])
        db.error_logs.create_index([("timestamp", DESCENDING)])
        
        print(f"✅ MongoDB initialized: social_support_system")
        print(f"   Collections created: {len(collections)}")
        for coll in collections:
            print(f"      - {coll}")
        
        client.close()
        return True
        
    except ImportError:
        print("⚠️  PyMongo not installed. Installing...")
        os.system("poetry add pymongo")
        print("   Please run this script again after installation")
        return False
    except Exception as e:
        print(f"❌ MongoDB initialization failed: {e}")
        print("   Make sure MongoDB is running: brew services start mongodb-community")
        return False


def initialize_chromadb():
    """Initialize ChromaDB with collections"""
    print("\n" + "="*70)
    print("3. INITIALIZING CHROMADB (VECTOR DATABASE)")
    print("="*70)
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        chroma_path = "data/databases/chromadb"
        Path(chroma_path).mkdir(parents=True, exist_ok=True)
        
        client = chromadb.PersistentClient(
            path=chroma_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections for different data types
        collections_config = {
            'documents': 'Document text embeddings for semantic search',
            'decisions': 'Decision reasoning embeddings',
            'chat_history': 'Chat message embeddings for context',
            'profiles': 'Applicant profile embeddings',
            'programs': 'Enablement program descriptions',
            'policies': 'Policy text embeddings for compliance'
        }
        
        created = []
        for coll_name, description in collections_config.items():
            try:
                collection = client.get_or_create_collection(
                    name=coll_name,
                    metadata={
                        "hnsw:space": "cosine",
                        "description": description
                    }
                )
                created.append(coll_name)
            except Exception as e:
                print(f"   Warning: Could not create {coll_name}: {e}")
        
        print(f"✅ ChromaDB initialized: {chroma_path}")
        print(f"   Collections created: {len(created)}")
        for coll in created:
            print(f"      - {coll}: {collections_config[coll]}")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB initialization failed: {e}")
        return False


def initialize_neo4j():
    """Initialize Neo4j with schema"""
    print("\n" + "="*70)
    print("4. INITIALIZING NEO4J (GRAPH DATABASE)")
    print("="*70)
    
    try:
        from neo4j import GraphDatabase
        
        driver = GraphDatabase.driver(
            'bolt://localhost:7687',
            auth=('neo4j', 'password')
        )
        
        with driver.session() as session:
            # Test connection
            session.run("RETURN 1")
            
            # Create constraints (unique IDs)
            constraints = [
                "CREATE CONSTRAINT application_id_unique IF NOT EXISTS FOR (a:Application) REQUIRE a.application_id IS UNIQUE",
                "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id_number IS UNIQUE",
                "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.document_id IS UNIQUE",
                "CREATE CONSTRAINT program_name_unique IF NOT EXISTS FOR (pr:Program) REQUIRE pr.name IS UNIQUE"
            ]
            
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception:
                    pass  # Constraint might already exist
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX application_status IF NOT EXISTS FOR (a:Application) ON (a.status)",
                "CREATE INDEX person_name IF NOT EXISTS FOR (p:Person) ON (p.name)",
                "CREATE INDEX document_type IF NOT EXISTS FOR (d:Document) ON (d.document_type)"
            ]
            
            for index in indexes:
                try:
                    session.run(index)
                except Exception:
                    pass
            
            # Add sample enablement programs
            programs = [
                {
                    "name": "UAE Job Placement Service",
                    "category": "Employment",
                    "description": "Connect job seekers with employment opportunities",
                    "target_audience": "unemployed,low_income"
                },
                {
                    "name": "Professional Skills Bootcamp",
                    "category": "Skills Training",
                    "description": "Intensive training in high-demand skills",
                    "target_audience": "low_experience,career_change"
                },
                {
                    "name": "Financial Wellness Program",
                    "category": "Financial Management",
                    "description": "Budgeting, debt management, and financial planning",
                    "target_audience": "financial_stress,high_debt"
                },
                {
                    "name": "Small Business Development",
                    "category": "Entrepreneurship",
                    "description": "Support for starting and growing businesses",
                    "target_audience": "entrepreneurial,business_owner"
                }
            ]
            
            for program in programs:
                session.run("""
                    MERGE (p:Program {name: $name})
                    SET p.category = $category,
                        p.description = $description,
                        p.target_audience = $target_audience
                """, **program)
            
            # Get node count
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()['count']
            
            print(f"✅ Neo4j initialized: bolt://localhost:7687")
            print(f"   Constraints: 4 (Application, Person, Document, Program)")
            print(f"   Indexes: 3 (status, name, type)")
            print(f"   Programs loaded: {len(programs)}")
            print(f"   Total nodes: {node_count}")
        
        driver.close()
        return True
        
    except ImportError:
        print("⚠️  Neo4j driver not installed. Installing...")
        os.system("poetry add neo4j")
        print("   Please run this script again after installation")
        return False
    except Exception as e:
        print(f"❌ Neo4j initialization failed: {e}")
        print("   Make sure Neo4j is running:")
        print("   - Docker: docker run -p 7687:7687 -p 7474:7474 -e NEO4J_AUTH=neo4j/password neo4j:latest")
        print("   - Or install locally: brew install neo4j && neo4j start")
        return False


def main():
    """Initialize all databases"""
    print("\n" + "="*70)
    print("PRODUCTION DATABASE INITIALIZATION")
    print("Social Support Agentic AI System")
    print("="*70)
    
    results = {
        'SQLite': False,
        'MongoDB': False,
        'ChromaDB': False,
        'Neo4j': False
    }
    
    # Initialize all databases
    results['SQLite'] = initialize_sqlite()
    results['MongoDB'] = initialize_mongodb()
    results['ChromaDB'] = initialize_chromadb()
    results['Neo4j'] = initialize_neo4j()
    
    # Summary
    print("\n" + "="*70)
    print("INITIALIZATION SUMMARY")
    print("="*70)
    
    for db_name, success in results.items():
        status = "✅ READY" if success else "❌ FAILED"
        print(f"{db_name:20} {status}")
    
    total_success = sum(results.values())
    print(f"\n{total_success}/4 databases initialized successfully")
    
    if total_success == 4:
        print("\n🎉 ALL DATABASES ARE PRODUCTION READY!")
    else:
        print("\n⚠️  Some databases need attention. Check logs above.")
    
    print("="*70)


if __name__ == "__main__":
    main()
