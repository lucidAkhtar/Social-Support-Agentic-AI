"""
Unified DatabaseManager orchestrating SQLite, ChromaDB, and Neo4j.
Single interface for all database operations.
"""

from typing import Dict, List, Optional, Any
from .sqlite_client import SQLiteClient
from .chromadb_manager import ChromaDBManager
from .neo4j_manager import Neo4jManager
import json


class DatabaseManager:
    """Unified database manager for SQLite + ChromaDB + Neo4j."""

    def __init__(self, sqlite_path: str = "data/databases/social_support.db",
                 chromadb_path: str = "data/databases/chromadb",
                 neo4j_uri: str = "bolt://localhost:7687"):
        """Initialize all three database managers."""
        self.sqlite = SQLiteClient(sqlite_path)
        self.chromadb = ChromaDBManager(chromadb_path)
        self.neo4j = Neo4jManager(neo4j_uri)

    def seed_application(self, app_data: Dict) -> Dict:
        """
        Seed a complete application across all databases.
        
        Args:
            app_data: Application data from synthetic generator
            
        Returns:
            Success status and app_id
        """
        try:
            app_id = app_data.get("application_id")
            applicant_id = app_id.replace("APP-", "APPLICANT-")

            # 1. SQLite: Store relational data
            self.sqlite.insert_application(app_data)
            
            # 2. ChromaDB: Create embeddings for similarity search
            # Application summary
            app_summary = self._create_app_summary(app_data)
            self.chromadb.add_application_summary(
                app_id,
                app_summary,
                {"applicant_name": app_data.get("full_name"), "employment": app_data.get("employment_status")}
            )
            
            # Resume/Skills summary
            if app_data.get("has_resume"):
                resume_text = f"Resume: {app_data.get('education_level')} in {app_data.get('position', 'General')}. Years of experience: {app_data.get('years_employed', 0)}"
                self.chromadb.add_resume(
                    app_id,
                    resume_text,
                    {"education": app_data.get("education_level")}
                )
            
            # Income pattern
            income_summary = f"Monthly income: {app_data.get('monthly_income', 0)}, Credit score: {app_data.get('credit_score', 0)}, Status: {app_data.get('credit_rating', 'Unknown')}"
            self.chromadb.add_income_pattern(
                app_id,
                income_summary,
                {"income": app_data.get("monthly_income"), "credit_score": app_data.get("credit_score")}
            )
            
            # 3. Neo4j: Create relationship graph
            # Create applicant node
            self.neo4j.create_applicant_node(
                applicant_id,
                app_data.get("full_name"),
                app_data.get("age", 0),
                app_data.get("employment_status"),
                app_data.get("monthly_income", 0)
            )
            
            # Create employment relationship
            if app_data.get("employer"):
                self.neo4j.create_employer_node(app_data.get("employer"))
                self.neo4j.create_employment_edge(
                    applicant_id,
                    app_data.get("employer"),
                    app_data.get("position", "Unknown"),
                    app_data.get("years_employed", 0)
                )
            
            # Create income source
            self.neo4j.create_income_source_edge(
                applicant_id,
                "Primary Employment",
                app_data.get("monthly_income", 0)
            )
            
            # Create dependent edges
            for i in range(app_data.get("dependents", 0)):
                self.neo4j.create_dependent_edge(
                    applicant_id,
                    f"Dependent-{i+1}",
                    "Child",
                    0
                )

            return {
                "success": True,
                "app_id": app_id,
                "applicant_id": applicant_id,
                "message": "Application seeded to SQLite, ChromaDB, and Neo4j"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "app_id": app_data.get("application_id")
            }

    def _create_app_summary(self, app_data: Dict) -> str:
        """Create a text summary of application for embeddings."""
        return (
            f"{app_data.get('full_name')} is a {app_data.get('age')}-year-old "
            f"{app_data.get('employment_status')} employee at {app_data.get('employer', 'Unknown')}. "
            f"Monthly income: {app_data.get('monthly_income', 0)} AED. "
            f"Family size: {app_data.get('family_size', 1)} with {app_data.get('dependents', 0)} dependents. "
            f"Education: {app_data.get('education_level')}. "
            f"Credit score: {app_data.get('credit_score', 0)}. "
            f"Housing: {app_data.get('housing_type')}. "
            f"Assets: {app_data.get('total_assets', 0)} AED, Liabilities: {app_data.get('total_liabilities', 0)} AED."
        )

    def process_application(self, app_id: str, extracted_data: Dict, 
                           validation_results: Dict, decision_result: Dict) -> bool:
        """
        Process complete application through all stages.
        
        Args:
            app_id: Application ID
            extracted_data: Extraction results
            validation_results: Validation metrics
            decision_result: Decision output
            
        Returns:
            Success status
        """
        try:
            # Store extraction
            self.sqlite.insert_extraction_result(
                app_id,
                extracted_data,
                extracted_data.get("confidence", 0.5)
            )
            
            # Store validation
            self.sqlite.insert_validation_result(
                app_id,
                validation_results.get("quality_score", 0),
                validation_results.get("consistency_score", 0),
                validation_results.get("completeness_score", 0)
            )
            
            # Store decision
            self.sqlite.insert_decision(
                app_id,
                decision_result.get("decision_type", "PENDING"),
                decision_result.get("decision_score", 0),
                decision_result.get("ml_confidence", 0),
                decision_result.get("business_rule_score", 0),
                decision_result.get("rationale", ""),
                decision_result.get("recommended_actions", [])
            )
            
            # Add decision case to ChromaDB for precedent lookup
            decision_summary = f"Decision: {decision_result.get('decision_type')}. Score: {decision_result.get('decision_score')}. Rationale: {decision_result.get('rationale')}"
            self.chromadb.add_decision_case(
                f"decision_{app_id}",
                decision_summary,
                {"decision_type": decision_result.get("decision_type"), "score": decision_result.get("decision_score")}
            )
            
            return True
        except Exception as e:
            print(f"Error processing application {app_id}: {e}")
            return False

    def get_application_graph(self, applicant_id: str) -> Dict:
        """Get complete relationship graph for an applicant."""
        return {
            "dependents": self.neo4j.get_dependents(applicant_id),
            "employment_history": self.neo4j.get_employment_history(applicant_id),
            "income_sources": self.neo4j.get_income_sources(applicant_id)
        }

    def find_similar_profiles(self, query_app_id: str) -> Dict:
        """Find similar applications using all databases."""
        return {
            "neo4j_similar": self.neo4j.find_similar_applicants(query_app_id),
            "chromadb_summary_similar": self.chromadb.find_similar_applications(
                f"Find similar to {query_app_id}",
                n_results=3
            )
        }

    def get_statistics(self) -> Dict:
        """Get statistics from all databases."""
        return {
            "sqlite": self.sqlite.get_statistics(),
            "chromadb": self.chromadb.get_collection_stats(),
            "neo4j": self.neo4j.get_graph_statistics()
        }

    def close(self):
        """Close all database connections."""
        self.sqlite.close()
        self.chromadb.close()
        self.neo4j.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
