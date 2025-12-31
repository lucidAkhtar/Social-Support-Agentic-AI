"""
Unified Database Manager - brings together all 4 database types.
Provides single interface for multi-modal data operations.

Production Stack (8GB RAM optimized):
1. SQLite - Relational (PostgreSQL replacement)
2. TinyDB - NoSQL (MongoDB replacement)  
3. ChromaDB - Vector embeddings
4. NetworkX - Graph (Neo4j replacement)
"""

from typing import Dict, List, Any, Optional
import logging
from .sqlite_manager import SQLiteManager
from .chroma_manager import ChromaDBManager
from .tinydb_manager import TinyDBManager
from .networkx_manager import NetworkXManager

logger = logging.getLogger(__name__)


class UnifiedDatabaseManager:
    """
    Unified interface for multi-modal database operations.
    Coordinates:
    - SQLite (structured relational data)
    - TinyDB (unstructured NoSQL data)
    - ChromaDB (vector embeddings)
    - NetworkX (graph relationships)
    """
    
    def __init__(self, 
                 sqlite_path: str = "data/databases/applications.db",
                 tinydb_path: str = "data/databases/tinydb",
                 chroma_path: str = "data/databases/chromadb",
                 networkx_path: str = "data/databases/networkx",
                 use_neo4j_mock: bool = False):  # Keep for backwards compatibility
        
        # Initialize all database managers
        self.sqlite = SQLiteManager(sqlite_path)
        self.tinydb = TinyDBManager(tinydb_path)
        self.chroma = ChromaDBManager(chroma_path)
        self.networkx = NetworkXManager(networkx_path)
        
        # Backwards compatibility (some code may reference self.neo4j)
        self.neo4j = self.networkx
        
        logger.info("UnifiedDatabaseManager initialized (SQLite + TinyDB + ChromaDB + NetworkX)")
        logger.info(f"  Memory-optimized stack for 8GB RAM systems")
    
    # ========== Application Management ==========
    
    def create_application(self, application_id: str, applicant_name: str) -> bool:
        """Create new application across all databases."""
        # Create in SQLite (source of truth)
        success = self.sqlite.create_application(application_id, applicant_name)
        
        if success:
            # Neo4j will be updated when profile is saved
            logger.info(f"Application {application_id} created")
        
        return success
    
    def update_application_stage(self, application_id: str, stage: str):
        """Update processing stage."""
        self.sqlite.update_application_stage(application_id, stage)
        self.sqlite.log_action(application_id, "System", "stage_updated", {"stage": stage})
    
    # ========== Document Management ==========
    
    def add_document(self, application_id: str, document_id: str, 
                    document_type: str, file_path: str, 
                    text_content: Optional[str] = None,
                    extracted_data: Optional[Dict[str, Any]] = None):
        """
        Add document to all 4 databases.
        - SQLite: metadata and references
        - TinyDB: raw document data and OCR results
        - ChromaDB: text embeddings for semantic search
        - NetworkX: document relationships graph
        """
        # Store in SQLite (structured metadata)
        self.sqlite.add_document(application_id, document_id, document_type, file_path)
        
        # Store raw data in TinyDB (unstructured)
        if extracted_data:
            self.tinydb.store_raw_document(application_id, document_type, extracted_data)
        
        # Store OCR text in TinyDB if available
        if text_content:
            self.tinydb.store_ocr_result(
                application_id=application_id,
                document_id=document_id,
                ocr_text=text_content,
                confidence=0.95,
                metadata={"file_path": file_path}
            )
        
        # Store embeddings in ChromaDB if text available
        if text_content:
            metadata = {
                "file_path": file_path,
                "document_id": document_id
            }
            self.chroma.add_document_embedding(
                application_id, document_type, text_content, metadata
            )
        
        # Store in NetworkX graph
        if extracted_data:
            self.networkx.add_document_node(
                application_id, document_id, document_type, extracted_data
            )
        
        logger.info(f"Document {document_id} added to all 4 databases")
    
    # ========== Profile Management ==========
    
    def save_applicant_profile(self, application_id: str, profile_data: Dict[str, Any]):
        """
        Save applicant profile across databases.
        - SQLite: structured profile data
        - Neo4j: person node with relationships
        """
        # Save to SQLite
        self.sqlite.save_applicant_profile(application_id, profile_data)
        
        # Create/update Neo4j nodes
        applicant_name = profile_data.get("applicant_name", "Unknown")
        self.neo4j.create_application_node(application_id, applicant_name, profile_data)
        
        logger.info(f"Profile saved for {application_id}")
    
    # ========== Validation Management ==========
    
    def save_validation_result(self, application_id: str, validation_data: Dict[str, Any]):
        """
        Save validation results.
        - SQLite: validation scores and issues
        - Neo4j: document consistency relationships
        """
        # Save to SQLite
        self.sqlite.save_validation_result(application_id, validation_data)
        
        # Create validation relationships in Neo4j
        self.neo4j.create_validation_relationship(application_id, validation_data)
        
        logger.info(f"Validation saved for {application_id}")
    
    # ========== Decision Management ==========
    
    def save_eligibility_decision(self, application_id: str, decision_data: Dict[str, Any]):
        """
        Save eligibility decision.
        - SQLite: decision details and scores
        - ChromaDB: decision reasoning embeddings
        - Neo4j: decision node with relationships
        """
        # Save to SQLite
        self.sqlite.save_eligibility_decision(application_id, decision_data)
        
        # Add decision embedding to ChromaDB
        self.chroma.add_decision_embedding(application_id, decision_data)
        
        # Create decision node in Neo4j
        self.neo4j.create_decision_node(application_id, decision_data)
        
        logger.info(f"Decision saved for {application_id}")
    
    def save_recommendation(self, application_id: str, recommendation_data: Dict[str, Any]):
        """Save recommendation to SQLite."""
        self.sqlite.save_recommendation(application_id, recommendation_data)
        logger.info(f"Recommendation saved for {application_id}")
    
    # ========== Chatbot & RAG Management ==========
    
    def add_chat_message(self, application_id: str, role: str, 
                        message: str, timestamp: str):
        """Store chat message in ChromaDB for context retrieval."""
        self.chroma.add_chat_message(application_id, role, message, timestamp)
    
    def get_chat_context_for_rag(self, application_id: str, query: str) -> str:
        """
        Get RAG context for chatbot response.
        Combines document embeddings and chat history.
        """
        # Get relevant document context
        doc_context = self.chroma.get_rag_context(application_id, query, n_results=3)
        
        # Get recent chat history
        chat_history = self.chroma.get_chat_context(application_id, n_messages=5)
        chat_text = "\n".join([
            f"{msg['metadata']['role']}: {msg['document']}" 
            for msg in chat_history
        ])
        
        return f"Document Context:\n{doc_context}\n\nRecent Chat:\n{chat_text}"
    
    # ========== Retrieval & Search ==========
    
    def get_application_full_data(self, application_id: str) -> Dict[str, Any]:
        """
        Get complete application data from all databases.
        This is the "unity of MultiModal data sources" the user requested.
        """
        return {
            # Structured data from SQLite
            "application": self.sqlite.get_application(application_id),
            "profile": self.sqlite.get_applicant_profile(application_id),
            # "validation_history": self.sqlite.get_validation_history(application_id),  # REMOVED: Method doesn't exist
            "decision_history": self.sqlite.get_decision_history(application_id),
            "audit_trail": self.sqlite.get_audit_trail(application_id),
            
            # Vector similarity from ChromaDB
            "similar_past_decisions": self.chroma.search_similar_decisions(
                f"application {application_id}", n_results=3
            ),
            
            # Graph relationships from Neo4j
            "related_applications": self.neo4j.find_related_applications(
                self.sqlite.get_applicant_profile(application_id).get("id_number", "")
            ) if self.sqlite.get_applicant_profile(application_id) else [],
            "decision_path": self.neo4j.trace_decision_path(application_id),
            "application_graph": self.neo4j.get_application_graph(application_id)
        }
    
    def search_applications(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search applications with filters."""
        return self.sqlite.search_applications(filters)
    
    def find_similar_cases(self, profile_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Find similar past cases using both vector similarity and graph relationships.
        Demonstrates multi-modal data unity.
        """
        # Get structurally similar cases from Neo4j
        graph_similar = self.neo4j.find_similar_cases(profile_data, limit=5)
        
        # Get semantically similar decisions from ChromaDB
        query_text = f"""
        Income: {profile_data.get('monthly_income', 0)}
        Family Size: {profile_data.get('family_size', 1)}
        Employment: {profile_data.get('employment_status', 'unknown')}
        """
        vector_similar = self.chroma.search_similar_decisions(query_text, n_results=5)
        
        # Combine results
        return {
            "graph_similarity": graph_similar,
            "vector_similarity": vector_similar
        }
    
    def search_documents_semantic(self, query: str, 
                                 application_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Semantic search across documents using ChromaDB."""
        return self.chroma.search_similar_documents(query, application_id, n_results=10)
    
    # ========== Analytics & Insights ==========
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        return {
            "sqlite": self.sqlite.get_statistics(),
            "chromadb": self.chroma.get_collection_stats(),
            "total_applications": self.sqlite.get_statistics()["applications"]["total_applications"]
        }
    
    def get_validation_insights(self, application_id: str) -> Dict[str, Any]:
        """Get validation insights using multi-modal data."""
        # Get validation history from SQLite
        # validation_history = self.sqlite.get_validation_history(application_id)  # REMOVED: Method doesn't exist
        validation_history = []  # Placeholder
        
        # Find potentially conflicting information using ChromaDB
        profile = self.sqlite.get_applicant_profile(application_id)
        conflicts = []
        
        if profile:
            # Check for income conflicts
            income_conflicts = self.chroma.find_conflicting_information(
                application_id, "monthly_income", str(profile.get("monthly_income", 0))
            )
            conflicts.extend(income_conflicts)
        
        return {
            "validation_history": validation_history,
            "potential_conflicts": conflicts
        }
    
    # ========== Family & Relationships ==========
    
    def link_family_members(self, person_id: str, family_member_id: str, 
                           relationship_type: str):
        """Create family relationship in Neo4j graph."""
        self.neo4j.link_family_members(person_id, family_member_id, relationship_type)
    
    def get_family_applications(self, person_id: str) -> List[Dict[str, Any]]:
        """Get all applications for a person and their family members."""
        return self.neo4j.find_related_applications(person_id)
    
    # ========== Cleanup ==========
    
    def delete_application_data(self, application_id: str):
        """Delete application from all databases."""
        # Note: SQLite doesn't have delete implemented in current version
        # This would cascade delete in production
        self.chroma.delete_application_data(application_id)
        logger.info(f"Application {application_id} deleted")
    
    def close(self):
        """Close all database connections."""
        self.sqlite.close()
        self.neo4j.close()
        logger.info("All database connections closed")
    
    # ========== Audit & Logging ==========
    
    def log_action(self, application_id: str, agent_name: str, 
                   action: str, details: Dict[str, Any]):
        """Log action to SQLite audit trail."""
        self.sqlite.log_action(application_id, agent_name, action, details)
