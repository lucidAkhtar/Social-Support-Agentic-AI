"""
ChromaDB Manager for vector embeddings and semantic search.
Stores document embeddings for similarity search and RAG-based chatbot.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import hashlib

logger = logging.getLogger(__name__)


class ChromaDBManager:
    """Manages vector embeddings for semantic search and RAG."""
    
    def __init__(self, persist_directory: str = "data/databases/chromadb"):
        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Create collections
        self.documents_collection = self._get_or_create_collection("documents")
        self.decisions_collection = self._get_or_create_collection("decisions")
        self.chat_history_collection = self._get_or_create_collection("chat_history")
        
        logger.info(f"ChromaDB initialized at {self.persist_directory}")
    
    def _get_or_create_collection(self, name: str):
        """Get or create a collection."""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def _generate_id(self, *parts: str) -> str:
        """Generate a unique ID from parts."""
        combined = "_".join(str(p) for p in parts)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def add_document_embedding(self, application_id: str, document_type: str, 
                              text_content: str, metadata: Dict[str, Any]):
        """Add document text embedding for semantic search."""
        doc_id = self._generate_id(application_id, document_type)
        
        self.documents_collection.add(
            ids=[doc_id],
            documents=[text_content],
            metadatas=[{
                "application_id": application_id,
                "document_type": document_type,
                **metadata
            }]
        )
        logger.info(f"Added document embedding: {doc_id}")
    
    def add_decision_embedding(self, application_id: str, decision_data: Dict[str, Any]):
        """Add decision reasoning embedding for similarity search."""
        decision_text = f"""
        Decision: {decision_data.get('final_decision', 'UNKNOWN')}
        Eligibility Score: {decision_data.get('eligibility_score', 0.0)}
        Reasons: {', '.join(decision_data.get('reasons', []))}
        Reasoning: {decision_data.get('reasoning', '')}
        """
        
        decision_id = self._generate_id(application_id, "decision")
        
        self.decisions_collection.add(
            ids=[decision_id],
            documents=[decision_text],
            metadatas=[{
                "application_id": application_id,
                "decision_type": decision_data.get('final_decision', 'UNKNOWN'),
                "eligibility_score": decision_data.get('eligibility_score', 0.0)
            }]
        )
        logger.info(f"Added decision embedding: {decision_id}")
    
    def add_chat_message(self, application_id: str, role: str, 
                        message: str, timestamp: str):
        """Store chat message for context retrieval."""
        chat_id = self._generate_id(application_id, timestamp, role)
        
        self.chat_history_collection.add(
            ids=[chat_id],
            documents=[message],
            metadatas=[{
                "application_id": application_id,
                "role": role,
                "timestamp": timestamp
            }]
        )
    
    def search_similar_documents(self, query_text: str, 
                                application_id: Optional[str] = None,
                                n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents using semantic similarity."""
        where_filter = {"application_id": application_id} if application_id else None
        
        results = self.documents_collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )
        
        return self._format_results(results)
    
    def search_similar_decisions(self, query_text: str, 
                                n_results: int = 5) -> List[Dict[str, Any]]:
        """Search for similar past decisions (for case-based reasoning)."""
        results = self.decisions_collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        return self._format_results(results)
    
    def get_chat_context(self, application_id: str, 
                        n_messages: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent chat history for context."""
        results = self.chat_history_collection.query(
            query_texts=[""],  # Empty query to get recent items
            n_results=n_messages,
            where={"application_id": application_id}
        )
        
        return self._format_results(results)
    
    def find_conflicting_information(self, application_id: str, 
                                    field_name: str,
                                    field_value: str) -> List[Dict[str, Any]]:
        """Find documents with potentially conflicting information."""
        query = f"{field_name}: {field_value}"
        
        results = self.documents_collection.query(
            query_texts=[query],
            n_results=10,
            where={"application_id": application_id}
        )
        
        return self._format_results(results)
    
    def get_rag_context(self, application_id: str, query: str, 
                       n_results: int = 3) -> str:
        """Get relevant context for RAG-based chatbot responses."""
        results = self.search_similar_documents(query, application_id, n_results)
        
        context_parts = []
        for result in results:
            context_parts.append(f"[{result['metadata']['document_type']}]: {result['document'][:200]}...")
        
        return "\n\n".join(context_parts)
    
    def _format_results(self, results: Dict) -> List[Dict[str, Any]]:
        """Format ChromaDB results into a cleaner structure."""
        formatted = []
        
        if not results['ids'] or not results['ids'][0]:
            return formatted
        
        for i in range(len(results['ids'][0])):
            formatted.append({
                "id": results['ids'][0][i],
                "document": results['documents'][0][i] if results['documents'] else None,
                "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                "distance": results['distances'][0][i] if results.get('distances') else None
            })
        
        return formatted
    
    def delete_application_data(self, application_id: str):
        """Delete all data for an application."""
        for collection in [self.documents_collection, self.decisions_collection, 
                          self.chat_history_collection]:
            try:
                collection.delete(where={"application_id": application_id})
                logger.info(f"Deleted {application_id} data from {collection.name}")
            except Exception as e:
                logger.error(f"Error deleting from {collection.name}: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about stored embeddings."""
        return {
            "documents": self.documents_collection.count(),
            "decisions": self.decisions_collection.count(),
            "chat_history": self.chat_history_collection.count()
        }
