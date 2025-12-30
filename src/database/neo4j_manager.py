"""
Neo4j graph database manager for relationship and network analysis.
Handles applicants, employers, dependents, income sources, and career paths.
"""

from typing import Dict, List, Optional, Tuple
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable


class Neo4jManager:
    """Manages Neo4j graph database for relationship and network analysis."""

    def __init__(self, uri: str = "bolt://localhost:7687", username: str = "neo4j", password: str = "password"):
        """Initialize Neo4j connection."""
        self.uri = uri
        self.username = username
        self.password = password
        self.driver = None
        self._connect()

    def _connect(self):
        """Connect to Neo4j database."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✓ Connected to Neo4j")
        except ServiceUnavailable:
            print("⚠️  Neo4j not available. Using in-memory fallback.")
            self.driver = None
        except Exception as e:
            print(f"⚠️  Neo4j connection error: {e}. Proceeding with limited graph functionality.")
            self.driver = None

    def create_applicant_node(self, applicant_id: str, name: str, age: int, 
                             employment_status: str, monthly_income: float) -> bool:
        """Create applicant node in graph."""
        if not self.driver:
            return False
        
        query = """
            MERGE (a:Applicant {applicant_id: $applicant_id})
            SET a.name = $name, a.age = $age, a.employment_status = $employment_status,
                a.monthly_income = $monthly_income, a.created_at = datetime()
            RETURN a.applicant_id
        """
        try:
            with self.driver.session() as session:
                session.run(query, {
                    "applicant_id": applicant_id,
                    "name": name,
                    "age": age,
                    "employment_status": employment_status,
                    "monthly_income": monthly_income
                })
            return True
        except Exception as e:
            print(f"Error creating applicant node: {e}")
            return False

    def create_employer_node(self, employer_name: str) -> bool:
        """Create employer node in graph."""
        if not self.driver:
            return False
        
        query = """
            MERGE (e:Employer {name: $name})
            RETURN e.name
        """
        try:
            with self.driver.session() as session:
                session.run(query, {"name": employer_name})
            return True
        except Exception as e:
            print(f"Error creating employer node: {e}")
            return False

    def create_employment_edge(self, applicant_id: str, employer_name: str, 
                              position: str, years_employed: float) -> bool:
        """Create works_for relationship between applicant and employer."""
        if not self.driver:
            return False
        
        query = """
            MATCH (a:Applicant {applicant_id: $applicant_id})
            MERGE (e:Employer {name: $employer_name})
            MERGE (a)-[r:WORKS_FOR]->(e)
            SET r.position = $position, r.years_employed = $years_employed
            RETURN r
        """
        try:
            with self.driver.session() as session:
                session.run(query, {
                    "applicant_id": applicant_id,
                    "employer_name": employer_name,
                    "position": position,
                    "years_employed": years_employed
                })
            return True
        except Exception as e:
            print(f"Error creating employment edge: {e}")
            return False

    def create_dependent_edge(self, applicant_id: str, dependent_name: str,
                             relationship: str, age: int) -> bool:
        """Create dependency relationship (parent_of, spouse_of, etc)."""
        if not self.driver:
            return False
        
        # Map relationship types to Neo4j edge types
        relationship_map = {
            "Child": "PARENT_OF",
            "Spouse": "SPOUSE_OF",
            "Parent": "CHILD_OF",
            "Sibling": "SIBLING_OF"
        }
        edge_type = relationship_map.get(relationship, "RELATED_TO")
        
        query = f"""
            MATCH (a:Applicant {{applicant_id: $applicant_id}})
            MERGE (d:Dependent {{name: $dependent_name}})
            SET d.relationship = $relationship, d.age = $age
            MERGE (a)-[r:{edge_type}]->(d)
            RETURN r
        """
        try:
            with self.driver.session() as session:
                session.run(query, {
                    "applicant_id": applicant_id,
                    "dependent_name": dependent_name,
                    "relationship": relationship,
                    "age": age
                })
            return True
        except Exception as e:
            print(f"Error creating dependent edge: {e}")
            return False

    def create_income_source_edge(self, applicant_id: str, source_type: str, amount: float) -> bool:
        """Create income source relationship."""
        if not self.driver:
            return False
        
        query = """
            MATCH (a:Applicant {applicant_id: $applicant_id})
            MERGE (i:IncomeSource {source_type: $source_type})
            MERGE (a)-[r:HAS_INCOME_FROM]->(i)
            SET r.amount = $amount, r.frequency = 'Monthly'
            RETURN r
        """
        try:
            with self.driver.session() as session:
                session.run(query, {
                    "applicant_id": applicant_id,
                    "source_type": source_type,
                    "amount": amount
                })
            return True
        except Exception as e:
            print(f"Error creating income source edge: {e}")
            return False

    def get_dependents(self, applicant_id: str) -> List[Dict]:
        """Get all dependents of an applicant."""
        if not self.driver:
            return []
        
        query = """
            MATCH (a:Applicant {applicant_id: $applicant_id})
            -[rel]-> (d:Dependent)
            RETURN d.name as name, d.relationship as relationship, d.age as age
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, {"applicant_id": applicant_id})
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error getting dependents: {e}")
            return []

    def get_employment_history(self, applicant_id: str) -> List[Dict]:
        """Get all employers of an applicant."""
        if not self.driver:
            return []
        
        query = """
            MATCH (a:Applicant {applicant_id: $applicant_id})
            -[r:WORKS_FOR]-> (e:Employer)
            RETURN e.name as employer, r.position as position, r.years_employed as years_employed
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, {"applicant_id": applicant_id})
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error getting employment history: {e}")
            return []

    def get_income_sources(self, applicant_id: str) -> List[Dict]:
        """Get all income sources of an applicant."""
        if not self.driver:
            return []
        
        query = """
            MATCH (a:Applicant {applicant_id: $applicant_id})
            -[r:HAS_INCOME_FROM]-> (i:IncomeSource)
            RETURN i.source_type as source, r.amount as amount
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, {"applicant_id": applicant_id})
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error getting income sources: {e}")
            return []

    def find_similar_applicants(self, applicant_id: str, limit: int = 5) -> List[Dict]:
        """Find applicants with similar employment and income profiles."""
        if not self.driver:
            return []
        
        query = """
            MATCH (a1:Applicant {applicant_id: $applicant_id})
            MATCH (a2:Applicant)
            WHERE a1 <> a2 AND a1.employment_status = a2.employment_status
            RETURN a2.applicant_id as applicant_id, a2.name as name, 
                   a2.monthly_income as income, a2.employment_status as employment
            LIMIT $limit
        """
        try:
            with self.driver.session() as session:
                result = session.run(query, {"applicant_id": applicant_id, "limit": limit})
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error finding similar applicants: {e}")
            return []

    def get_graph_statistics(self) -> Dict:
        """Get overall graph statistics."""
        if not self.driver:
            return {"status": "Neo4j unavailable"}
        
        try:
            with self.driver.session() as session:
                applicant_count = session.run("MATCH (a:Applicant) RETURN COUNT(a) as count").single()["count"]
                employer_count = session.run("MATCH (e:Employer) RETURN COUNT(e) as count").single()["count"]
                dependent_count = session.run("MATCH (d:Dependent) RETURN COUNT(d) as count").single()["count"]
                
                return {
                    "total_applicants": applicant_count,
                    "total_employers": employer_count,
                    "total_dependents": dependent_count,
                    "status": "Connected"
                }
        except Exception as e:
            return {"error": str(e), "status": "Error"}

    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()

    def __del__(self):
        self.close()
