"""
ChromaDB manager for vector embeddings and semantic search.
Uses default embeddings for application summaries, resumes, and income patterns.
"""

from typing import Dict, List, Optional, Any
import chromadb


class ChromaDBManager:
    """Manages vector embeddings and similarity search using ChromaDB."""

    def __init__(self, persist_dir: str = "data/databases/chromadb"):
        """Initialize ChromaDB with persistent storage."""
        self.client = chromadb.PersistentClient(path=persist_dir)
        self._initialize_collections()

    def _initialize_collections(self):
        """Initialize 4 collections for different embedding types."""
        try:
            # Reset if schema conflicts exist
            collections_to_init = [
                ("application_summaries", "Application profile summaries for similarity search"),
                ("resumes", "Resume text embeddings for skill matching"),
                ("income_patterns", "Income and financial stability patterns"),
                ("case_decisions", "Decision rationales and outcomes for precedent lookup")
            ]
            
            for collection_name, description in collections_to_init:
                try:
                    collection = self.client.get_or_create_collection(
                        name=collection_name,
                        metadata={"description": description}
                    )
                    setattr(self, collection_name.replace("-", "_"), collection)
                except Exception as e:
                    # Try to delete and recreate if schema issue
                    try:
                        self.client.delete_collection(name=collection_name)
                        collection = self.client.get_or_create_collection(
                            name=collection_name,
                            metadata={"description": description}
                        )
                        setattr(self, collection_name.replace("-", "_"), collection)
                    except:
                        # Fallback - create empty placeholder
                        setattr(self, collection_name.replace("-", "_"), None)
        except Exception as e:
            print(f"Warning: Could not initialize collections: {e} - proceeding with limited functionality")

    def add_application_summary(self, app_id: str, summary_text: str, metadata: Dict):
        """Add application summary embedding."""
        try:
            self.application_summaries.add(
                ids=[app_id],
                documents=[summary_text],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"Error adding application summary {app_id}: {e}")

    def add_resume(self, app_id: str, resume_text: str, metadata: Dict):
        """Add resume embedding."""
        try:
            self.resumes.add(
                ids=[app_id],
                documents=[resume_text],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"Error adding resume {app_id}: {e}")

    def add_income_pattern(self, app_id: str, income_summary: str, metadata: Dict):
        """Add income pattern embedding."""
        try:
            self.income_patterns.add(
                ids=[app_id],
                documents=[income_summary],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"Error adding income pattern {app_id}: {e}")

    def add_decision_case(self, decision_id: str, decision_summary: str, metadata: Dict):
        """Add decision case embedding for precedent lookup."""
        try:
            self.case_decisions.add(
                ids=[decision_id],
                documents=[decision_summary],
                metadatas=[metadata]
            )
        except Exception as e:
            print(f"Error adding decision case {decision_id}: {e}")

    def find_similar_applications(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """Find similar applications based on profile similarity."""
        try:
            results = self.application_summaries.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return self._format_results(results)
        except Exception as e:
            print(f"Error finding similar applications: {e}")
            return []

    def find_resume_matches(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """Find resumes similar to query (for training recommendations)."""
        try:
            results = self.resumes.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return self._format_results(results)
        except Exception as e:
            print(f"Error finding resume matches: {e}")
            return []

    def find_income_anomalies(self, query_text: str, n_results: int = 5) -> List[Dict]:
        """Find income patterns similar to current applicant (for anomaly detection)."""
        try:
            results = self.income_patterns.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return self._format_results(results)
        except Exception as e:
            print(f"Error finding income anomalies: {e}")
            return []

    def find_similar_decisions(self, query_text: str, n_results: int = 3) -> List[Dict]:
        """Find similar decision cases (for precedent lookup)."""
        try:
            results = self.case_decisions.query(
                query_texts=[query_text],
                n_results=n_results
            )
            return self._format_results(results)
        except Exception as e:
            print(f"Error finding similar decisions: {e}")
            return []

    def _format_results(self, results: Dict) -> List[Dict]:
        """Format ChromaDB query results."""
        formatted = []
        if results and results["ids"] and len(results["ids"]) > 0:
            ids = results["ids"][0]
            documents = results["documents"][0] if results["documents"] else []
            distances = results["distances"][0] if results["distances"] else []
            metadatas = results["metadatas"][0] if results["metadatas"] else []

            for i, doc_id in enumerate(ids):
                formatted.append({
                    "id": doc_id,
                    "document": documents[i] if i < len(documents) else "",
                    "distance": distances[i] if i < len(distances) else 0,
                    "similarity": 1 - (distances[i] if i < len(distances) else 0),
                    "metadata": metadatas[i] if i < len(metadatas) else {}
                })
        return formatted

    def get_collection_stats(self) -> Dict:
        """Get statistics for all collections."""
        stats = {}
        for collection in [self.application_summaries, self.resumes, self.income_patterns, self.case_decisions]:
            try:
                stats[collection.name] = {
                    "count": collection.count(),
                    "metadata": collection.metadata
                }
            except Exception as e:
                stats[collection.name] = {"error": str(e)}
        return stats

    def delete_collection(self, collection_name: str):
        """Delete a collection."""
        try:
            self.client.delete_collection(name=collection_name)
        except Exception as e:
            print(f"Error deleting collection {collection_name}: {e}")

    def close(self):
        """Close ChromaDB connection."""
        # ChromaDB handles cleanup automatically
        pass
