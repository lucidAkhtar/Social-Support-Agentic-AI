"""
Neo4j Manager for graph relationships.
Stores family connections, document cross-references, and decision flows.
"""

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("Neo4j driver not installed. Graph features will be disabled.")

logger = logging.getLogger(__name__)


class Neo4jManager:
    """Manages graph relationships in Neo4j."""
    
    def __init__(self, uri: str = "bolt://localhost:7687", 
                 user: str = "neo4j", 
                 password: str = "password",
                 use_mock: bool = False):
        self.uri = uri
        self.user = user
        self.use_mock = use_mock or not NEO4J_AVAILABLE
        
        if self.use_mock:
            logger.info("Using mock Neo4j (driver not available)")
            self.driver = None
        else:
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                self._initialize_constraints()
                logger.info(f"Neo4j connected at {uri}")
            except Exception as e:
                logger.warning(f"Neo4j connection failed: {e}. Using mock mode.")
                self.use_mock = True
                self.driver = None
    
    def _initialize_constraints(self):
        """Create indexes and constraints."""
        if self.use_mock:
            return
        
        with self.driver.session() as session:
            # Application node constraints
            session.run("""
                CREATE CONSTRAINT application_id IF NOT EXISTS
                FOR (a:Application) REQUIRE a.application_id IS UNIQUE
            """)
            
            # Person node constraints
            session.run("""
                CREATE CONSTRAINT person_id IF NOT EXISTS
                FOR (p:Person) REQUIRE p.id_number IS UNIQUE
            """)
            
            # Document node constraints
            session.run("""
                CREATE CONSTRAINT document_id IF NOT EXISTS
                FOR (d:Document) REQUIRE d.document_id IS UNIQUE
            """)
    
    def create_application_node(self, application_id: str, applicant_name: str,
                               profile_data: Dict[str, Any]):
        """Create application and person nodes with relationship."""
        if self.use_mock:
            logger.debug(f"Mock: Created application {application_id}")
            return
        
        with self.driver.session() as session:
            session.run("""
                MERGE (a:Application {application_id: $app_id})
                SET a.created_at = datetime(),
                    a.status = 'pending',
                    a.current_stage = 'not_started'
                
                MERGE (p:Person {id_number: $id_number})
                SET p.name = $name,
                    p.monthly_income = $income,
                    p.employment_status = $employment,
                    p.credit_score = $credit_score,
                    p.family_size = $family_size
                
                MERGE (p)-[:APPLIED_FOR]->(a)
            """, 
                app_id=application_id,
                name=applicant_name,
                id_number=profile_data.get("id_number", "unknown"),
                income=profile_data.get("monthly_income", 0.0),
                employment=profile_data.get("employment_status", "unknown"),
                credit_score=profile_data.get("credit_score", 0),
                family_size=profile_data.get("family_size", 1)
            )
    
    def add_document_node(self, application_id: str, document_id: str,
                         document_type: str, extracted_data: Dict[str, Any]):
        """Add document node and link to application."""
        if self.use_mock:
            logger.debug(f"Mock: Added document {document_id}")
            return
        
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Application {application_id: $app_id})
                MERGE (d:Document {document_id: $doc_id})
                SET d.type = $doc_type,
                    d.uploaded_at = datetime()
                MERGE (d)-[:BELONGS_TO]->(a)
            """,
                app_id=application_id,
                doc_id=document_id,
                doc_type=document_type
            )
    
    def create_validation_relationship(self, application_id: str, 
                                      validation_result: Dict[str, Any]):
        """Create validation relationships between documents."""
        if self.use_mock:
            return
        
        with self.driver.session() as session:
            # Link documents that were validated together
            session.run("""
                MATCH (a:Application {application_id: $app_id})
                MATCH (d:Document)-[:BELONGS_TO]->(a)
                WITH COLLECT(d) as docs
                UNWIND docs as d1
                UNWIND docs as d2
                WITH d1, d2 WHERE id(d1) < id(d2)
                MERGE (d1)-[r:VALIDATED_WITH]->(d2)
                SET r.is_consistent = $is_valid,
                    r.confidence = $confidence,
                    r.validated_at = datetime()
            """,
                app_id=application_id,
                is_valid=validation_result.get("is_valid", False),
                confidence=validation_result.get("confidence_score", 0.0)
            )
    
    def create_decision_node(self, application_id: str, 
                            decision_data: Dict[str, Any]):
        """Create decision node and link to application."""
        if self.use_mock:
            return
        
        with self.driver.session() as session:
            session.run("""
                MATCH (a:Application {application_id: $app_id})
                CREATE (dec:Decision {
                    decision_id: randomUUID(),
                    decision_type: $decision_type,
                    eligibility_score: $score,
                    decided_at: datetime()
                })
                CREATE (dec)-[:FOR_APPLICATION]->(a)
                
                WITH a, dec
                MATCH (p:Person)-[:APPLIED_FOR]->(a)
                CREATE (dec)-[:ABOUT_PERSON]->(p)
            """,
                app_id=application_id,
                decision_type=decision_data.get("final_decision", "DECLINED"),
                score=decision_data.get("eligibility_score", 0.0)
            )
    
    def link_family_members(self, person_id: str, family_member_id: str, 
                           relationship_type: str):
        """Create family relationship between persons."""
        if self.use_mock:
            return
        
        with self.driver.session() as session:
            session.run("""
                MATCH (p1:Person {id_number: $person1})
                MATCH (p2:Person {id_number: $person2})
                MERGE (p1)-[r:FAMILY_MEMBER {type: $rel_type}]->(p2)
            """,
                person1=person_id,
                person2=family_member_id,
                rel_type=relationship_type
            )
    
    def find_related_applications(self, person_id: str) -> List[Dict[str, Any]]:
        """Find all applications related to a person or their family."""
        if self.use_mock:
            return []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person {id_number: $person_id})
                OPTIONAL MATCH (p)-[:FAMILY_MEMBER*1..2]-(family:Person)
                WITH COLLECT(DISTINCT p) + COLLECT(DISTINCT family) as people
                UNWIND people as person
                MATCH (person)-[:APPLIED_FOR]->(a:Application)
                RETURN DISTINCT a.application_id as application_id,
                       a.status as status,
                       a.created_at as created_at,
                       person.name as applicant_name
                ORDER BY a.created_at DESC
            """, person_id=person_id)
            
            return [dict(record) for record in result]
    
    def trace_decision_path(self, application_id: str) -> List[Dict[str, Any]]:
        """Trace the full path from application to decision."""
        if self.use_mock:
            return []
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH path = (p:Person)-[:APPLIED_FOR]->(a:Application)
                             <-[:BELONGS_TO]-(d:Document)
                WHERE a.application_id = $app_id
                OPTIONAL MATCH (dec:Decision)-[:FOR_APPLICATION]->(a)
                RETURN p.name as applicant,
                       a.application_id as application,
                       COLLECT(DISTINCT d.type) as documents,
                       dec.decision_type as decision,
                       dec.eligibility_score as score
            """, app_id=application_id)
            
            return [dict(record) for record in result]
    
    def find_similar_cases(self, profile_data: Dict[str, Any], 
                          limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar past cases based on profile similarity."""
        if self.use_mock:
            return []
        
        income = profile_data.get("monthly_income", 0)
        family_size = profile_data.get("family_size", 1)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (p:Person)-[:APPLIED_FOR]->(a:Application)
                      <-[:FOR_APPLICATION]-(dec:Decision)
                WHERE p.monthly_income >= $income * 0.8 
                  AND p.monthly_income <= $income * 1.2
                  AND p.family_size = $family_size
                RETURN a.application_id as application_id,
                       p.name as applicant_name,
                       p.monthly_income as income,
                       dec.decision_type as decision,
                       dec.eligibility_score as score
                ORDER BY ABS(p.monthly_income - $income)
                LIMIT $limit
            """, 
                income=income,
                family_size=family_size,
                limit=limit
            )
            
            return [dict(record) for record in result]
    
    def get_application_graph(self, application_id: str) -> Dict[str, Any]:
        """Get the complete graph structure for an application."""
        if self.use_mock:
            return {"nodes": [], "relationships": []}
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (a:Application {application_id: $app_id})
                OPTIONAL MATCH (a)<-[r1]-(n1)
                OPTIONAL MATCH (a)-[r2]->(n2)
                RETURN a, 
                       COLLECT(DISTINCT {node: n1, rel: r1}) as incoming,
                       COLLECT(DISTINCT {node: n2, rel: r2}) as outgoing
            """, app_id=application_id)
            
            record = result.single()
            if not record:
                return {"nodes": [], "relationships": []}
            
            # Format for visualization
            return self._format_graph(record)
    
    def _format_graph(self, record) -> Dict[str, Any]:
        """Format Neo4j result for graph visualization."""
        nodes = []
        relationships = []
        
        # Add application node
        app = record["a"]
        nodes.append({
            "id": app["application_id"],
            "label": "Application",
            "properties": dict(app)
        })
        
        # Add connected nodes
        for item in record["incoming"] + record["outgoing"]:
            if item["node"]:
                node = item["node"]
                nodes.append({
                    "id": node.element_id,
                    "label": list(node.labels)[0],
                    "properties": dict(node)
                })
                
                if item["rel"]:
                    rel = item["rel"]
                    relationships.append({
                        "type": rel.type,
                        "properties": dict(rel)
                    })
        
        return {
            "nodes": nodes,
            "relationships": relationships
        }
    
    def close(self):
        """Close Neo4j connection."""
        if self.driver and not self.use_mock:
            self.driver.close()
            logger.info("Neo4j connection closed")
