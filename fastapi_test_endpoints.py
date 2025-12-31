"""
FastAPI Test Endpoints for Database Testing
FAANG Production Standards: Comprehensive testing endpoints for SQLite, TinyDB, ChromaDB, NetworkX
Purpose: Allow developers to test each database independently with appropriate inputs
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
import json

from src.databases.prod_sqlite_manager import SQLiteManager
from src.databases.tinydb_manager import TinyDBManager
from src.databases.chroma_manager import ChromaDBManager
from src.databases.networkx_manager import NetworkXManager

app = FastAPI(
    title="Database Testing API",
    description="Test endpoints for SQLite, TinyDB, ChromaDB, and NetworkX",
    version="1.0.0"
)

# Initialize database managers
sqlite_db = SQLiteManager("data/databases/applications.db")
tinydb_cache = TinyDBManager("data/databases/cache.json")
chroma_db = ChromaDBManager("data/databases/chromadb_rag")
networkx_db = NetworkXManager()

# Load NetworkX graph from file
try:
    import networkx as nx
    from pathlib import Path
    graph_path = Path("application_graph.graphml")
    if graph_path.exists():
        networkx_db.graph = nx.read_graphml(str(graph_path))
        print(f"✅ NetworkX loaded: {networkx_db.graph.number_of_nodes()} nodes, {networkx_db.graph.number_of_edges()} edges")
    else:
        print("⚠️  application_graph.graphml not found")
except Exception as e:
    print(f"⚠️  NetworkX load failed: {e}")

# ============================================================================
# PYDANTIC MODELS - Input validation
# ============================================================================

class ApplicationInput(BaseModel):
    """Input for SQLite application insertion"""
    app_id: str = Field(..., example="APP-000001")
    applicant_name: str = Field(..., example="Ahmed Hassan")
    emirates_id: str = Field(..., example="784-1990-1234567-1")
    submission_date: str = Field(..., example="2024-12-01")
    status: str = Field(default="PENDING", example="PENDING")
    monthly_income: float = Field(..., example=5200.0, ge=0)
    monthly_expenses: float = Field(..., example=3800.0, ge=0)
    family_size: int = Field(..., example=4, ge=1)
    employment_status: str = Field(..., example="Government Employee")
    total_assets: float = Field(..., example=85000.0, ge=0)
    total_liabilities: float = Field(..., example=42000.0, ge=0)
    credit_score: int = Field(..., example=680, ge=300, le=850)
    policy_score: Optional[float] = Field(None, example=72.5)
    eligibility: Optional[str] = Field(None, example="APPROVED")
    support_amount: Optional[float] = Field(None, example=5000.0)


class SessionInput(BaseModel):
    """Input for TinyDB session management"""
    session_id: str = Field(..., example="user_12345")
    data: Dict[str, Any] = Field(..., example={"user_id": "user_12345", "language": "en", "current_app_id": "APP-000001"})


class RAGQueryInput(BaseModel):
    """Input for ChromaDB semantic search"""
    query: str = Field(..., example="low income large family unemployed")
    n_results: int = Field(default=5, example=5, ge=1, le=20)


class GraphQueryInput(BaseModel):
    """Input for NetworkX graph queries"""
    node_type: Optional[str] = Field(None, example="Application")
    attribute_filter: Optional[Dict[str, Any]] = Field(None, example={"eligibility": "APPROVED"})


# ============================================================================
# SQLITE TEST ENDPOINTS
# ============================================================================

@app.post("/test/sqlite/insert-application", tags=["SQLite Tests"])
async def test_sqlite_insert(app: ApplicationInput):
    """
    Test SQLite insertion with full application data.
    
    This endpoint tests:
    - Connection pooling
    - Prepared statements
    - Generated columns (net_worth)
    - Index usage
    """
    try:
        sqlite_db.insert_application(app.dict())
        
        # Verify insertion
        result = sqlite_db.get_application_status(app.app_id)
        
        return {
            "status": "success",
            "message": f"Application {app.app_id} inserted successfully",
            "data": result,
            "net_worth_calculated": result['net_worth'] if result else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQLite insertion failed: {str(e)}")


@app.get("/test/sqlite/get-application/{app_id}", tags=["SQLite Tests"])
async def test_sqlite_get(app_id: str):
    """
    Test SQLite retrieval with JOIN query.
    
    **TEST DATA (Copy for Swagger UI):**
    ```
    APP-000001  (Ahmed Hassan, Policy Score: 72.5, APPROVED)
    APP-000010  (Layla Mohammed, Policy Score: 45.0, CONDITIONAL)
    APP-000037  (Youssef Ibrahim, Policy Score: 25.0, DECLINED)
    ```
    
    This endpoint tests:
    - Indexed lookups
    - JOIN operations (applications + decisions)
    - Connection reuse
    """
    try:
        result = sqlite_db.get_application_status(app_id)
        
        if not result:
            raise HTTPException(status_code=404, detail=f"Application {app_id} not found")
        
        return {
            "status": "success",
            "data": result
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQLite retrieval failed: {str(e)}")


@app.get("/test/sqlite/search-similar", tags=["SQLite Tests"])
async def test_sqlite_similarity(
    income: float = Query(..., example=5000.0, description="Monthly income in AED (e.g., 5000.0 for middle class, 2500.0 for low income, 12000.0 for high income)"),
    family_size: int = Query(..., example=4, description="Family size (e.g., 1 for single, 4 for family, 7 for large family)"),
    limit: int = Query(5, ge=1, le=20)
):
    """
    Test SQLite similarity search with distance metric.
    
    **TEST DATA (Copy for Swagger UI):**
    ```
    income=5000.0, family_size=4  (Find middle-class families)
    income=2500.0, family_size=6  (Find low-income large families)
    income=12000.0, family_size=2 (Find high-income small families)
    ```
    
    This endpoint tests:
    - Computed similarity score
    - ORDER BY with expressions
    - Index effectiveness on financial columns
    """
    try:
        results = sqlite_db.search_similar_cases(income, family_size, limit)
        
        return {
            "status": "success",
            "query": {"income": income, "family_size": family_size},
            "results_count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQLite similarity search failed: {str(e)}")


@app.get("/test/sqlite/full-text-search", tags=["SQLite Tests"])
async def test_sqlite_fts(
    query: str = Query(..., example="unemployed", description="Search text (e.g., 'unemployed', 'government employee', 'high debt')"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Test SQLite FTS5 full-text search.
    
    **TEST DATA (Copy for Swagger UI):**
    ```
    query="unemployed"           (Find unemployed applicants)
    query="government employee"  (Find government workers)
    query="large family"         (Find families with 5+ members)
    query="APPROVED"            (Find approved applications)
    ```
    
    This endpoint tests:
    - FTS5 MATCH operator
    - Snippet highlighting
    - Ranking algorithm
    - Fallback to LIKE if FTS5 unavailable
    """
    try:
        results = sqlite_db.full_text_search(query, limit)
        
        return {
            "status": "success",
            "query": query,
            "results_count": len(results),
            "data": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQLite FTS search failed: {str(e)}")


@app.get("/test/sqlite/statistics", tags=["SQLite Tests"])
async def test_sqlite_stats():
    """
    Test SQLite aggregation queries.
    
    This endpoint tests:
    - Aggregate functions (COUNT, AVG, SUM)
    - CASE WHEN expressions
    - Performance on large datasets
    """
    try:
        stats = sqlite_db.get_eligibility_stats()
        
        return {
            "status": "success",
            "data": stats,
            "approval_rate": (stats.get('approved', 0) / max(stats.get('total_applications', 1), 1)) * 100
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SQLite statistics failed: {str(e)}")


# ============================================================================
# TINYDB TEST ENDPOINTS
# ============================================================================

@app.post("/test/tinydb/create-session", tags=["TinyDB Tests"])
async def test_tinydb_session(session: SessionInput):
    """
    Test TinyDB session creation with TTL.
    
    **TEST DATA (Copy for Swagger UI - Request Body):**
    ```json
    {
      "session_id": "user_12345",
      "data": {
        "user_id": "user_12345",
        "language": "en",
        "current_app_id": "APP-000001"
      }
    }
    ```
    
    This endpoint tests:
    - Document insertion with upsert
    - TTL expiration logic
    - Thread-safe operations
    """
    try:
        tinydb_cache.store_session(session.session_id, session.data)
        
        # Verify storage
        retrieved = tinydb_cache.get_session(session.session_id)
        
        return {
            "status": "success",
            "message": f"Session {session.session_id} created",
            "data": retrieved
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TinyDB session creation failed: {str(e)}")


@app.get("/test/tinydb/get-session/{session_id}", tags=["TinyDB Tests"])
async def test_tinydb_get_session(session_id: str):
    """
    Test TinyDB session retrieval with expiration check.
    
    **TEST DATA (Copy for Swagger UI):**
    ```
    session_id: user_12345  (Create session first using POST /test/tinydb/create-session)
    ```
    
    This endpoint tests:
    - Query API
    - TTL validation
    - Automatic cleanup
    """
    try:
        session = tinydb_cache.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail=f"Session {session_id} not found or expired")
        
        return {
            "status": "success",
            "data": session
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TinyDB session retrieval failed: {str(e)}")


@app.post("/test/tinydb/cache-rag-results", tags=["TinyDB Tests"])
async def test_tinydb_rag_cache(rag_query: RAGQueryInput):
    """
    Test TinyDB RAG result caching.
    
    This endpoint tests:
    - Hash-based key generation
    - Cache hit/miss logic
    - Hit counter incrementation
    """
    try:
        # Simulate RAG results
        mock_results = [
            {"app_id": "APP-000001", "score": 0.95, "text": "Low income large family"},
            {"app_id": "APP-000012", "score": 0.87, "text": "Unemployed with dependents"}
        ]
        
        # Cache results
        tinydb_cache.cache_rag_results(rag_query.query, mock_results)
        
        # Retrieve from cache
        cached = tinydb_cache.get_cached_rag_results(rag_query.query)
        
        return {
            "status": "success",
            "message": "RAG results cached",
            "cached_data": cached
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TinyDB RAG caching failed: {str(e)}")


@app.get("/test/tinydb/cache-stats", tags=["TinyDB Tests"])
async def test_tinydb_stats():
    """
    Test TinyDB cache statistics.
    
    This endpoint tests:
    - Table aggregation
    - File size calculation
    - Hit rate computation
    """
    try:
        stats = tinydb_cache.get_cache_stats()
        
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TinyDB stats failed: {str(e)}")


@app.post("/test/tinydb/cleanup", tags=["TinyDB Tests"])
async def test_tinydb_cleanup():
    """
    Test TinyDB expired entry cleanup.
    
    This endpoint tests:
    - Expiration detection
    - Batch deletion
    - Performance on large cache
    """
    try:
        tinydb_cache.cleanup_expired()
        
        stats = tinydb_cache.get_cache_stats()
        
        return {
            "status": "success",
            "message": "Cleanup completed",
            "remaining_entries": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"TinyDB cleanup failed: {str(e)}")


# ============================================================================
# CHROMADB TEST ENDPOINTS
# ============================================================================

@app.post("/test/chromadb/index-documents", tags=["ChromaDB Tests"])
async def test_chromadb_index():
    """
    Test ChromaDB document indexing.
    
    This endpoint tests:
    - Embedding generation
    - Collection creation
    - Batch insertion
    - Vector storage
    
    Note: This may take 30-60 seconds for 240 documents
    """
    try:
        # Load documents from disk
        from pathlib import Path
        import json
        
        docs_dir = Path("data/processed/documents")
        documents = []
        
        for app_dir in sorted(docs_dir.glob("APP-*")):
            for doc_file in app_dir.glob("*.json"):
                with open(doc_file) as f:
                    doc = json.load(f)
                    documents.append({
                        "id": f"{app_dir.name}_{doc_file.stem}",
                        "text": json.dumps(doc),
                        "metadata": {
                            "app_id": app_dir.name,
                            "document_type": doc_file.stem
                        }
                    })
        
        # Index documents
        chroma_db.add_documents(documents)
        
        return {
            "status": "success",
            "message": f"Indexed {len(documents)} documents into ChromaDB",
            "collection": chroma_db.collection_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChromaDB indexing failed: {str(e)}")


@app.post("/test/chromadb/semantic-search", tags=["ChromaDB Tests"])
async def test_chromadb_search(rag_query: RAGQueryInput):
    """
    Test ChromaDB semantic search.
    
    **TEST DATA (Copy for Swagger UI - Request Body):**
    ```json
    {
      "query": "low income large family unemployed",
      "n_results": 5
    }
    ```
    
    **More Test Queries:**
    ```json
    {"query": "government employee stable income", "n_results": 5}
    {"query": "high debt credit issues", "n_results": 5}
    {"query": "self employed business owner", "n_results": 5}
    ```
    
    This endpoint tests:
    - Query embedding generation
    - Cosine similarity search
    - Result ranking
    - Metadata filtering
    """
    try:
        results = chroma_db.query(rag_query.query, n_results=rag_query.n_results)
        
        return {
            "status": "success",
            "query": rag_query.query,
            "results_count": len(results.get('ids', [[]])[0]),
            "data": {
                "ids": results.get('ids', [[]])[0],
                "distances": results.get('distances', [[]])[0],
                "metadatas": results.get('metadatas', [[]])[0]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChromaDB search failed: {str(e)}")


@app.get("/test/chromadb/collection-info", tags=["ChromaDB Tests"])
async def test_chromadb_info():
    """
    Test ChromaDB collection metadata.
    
    This endpoint tests:
    - Collection count across all 4 collections
    - Peek function
    - Metadata retrieval
    """
    try:
        # ChromaDBManager has 4 collections, not single collection
        collections_info = {}
        
        for collection_name in ['application_summaries', 'resumes', 'income_patterns', 'case_decisions']:
            collection = getattr(chroma_db, collection_name, None)
            if collection:
                count = collection.count()
                peek = collection.peek(limit=2) if count > 0 else {'ids': [], 'metadatas': []}
                collections_info[collection_name] = {
                    "document_count": count,
                    "sample_ids": peek.get('ids', [])[:2]
                }
            else:
                collections_info[collection_name] = {"status": "not_initialized"}
        
        total_docs = sum(c.get('document_count', 0) for c in collections_info.values() if isinstance(c, dict))
        
        return {
            "status": "success",
            "total_documents": total_docs,
            "collections": collections_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ChromaDB info retrieval failed: {str(e)}")


# ============================================================================
# NETWORKX TEST ENDPOINTS
# ============================================================================

@app.post("/test/networkx/load-graph", tags=["NetworkX Tests"])
async def test_networkx_load():
    """
    Test NetworkX graph loading from application_graph.graphml.
    
    This endpoint tests:
    - GraphML import
    - Node/edge parsing
    - Attribute preservation
    """
    try:
        from pathlib import Path
        graph_path = Path("application_graph.graphml")
        
        if not graph_path.exists():
            raise HTTPException(status_code=404, detail="Graph file not found. Run build_networkx_graph.py first")
        
        networkx_db.load_graph(str(graph_path))
        
        return {
            "status": "success",
            "message": "Graph loaded successfully",
            "nodes": networkx_db.graph.number_of_nodes(),
            "edges": networkx_db.graph.number_of_edges()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NetworkX load failed: {str(e)}")


@app.post("/test/networkx/query-nodes", tags=["NetworkX Tests"])
async def test_networkx_query(query: GraphQueryInput):
    """
    Test NetworkX node querying.
    
    **TEST DATA (Copy for Swagger UI - Request Body):**
    
    Find all Application nodes:
    ```json
    {
      "node_type": "Application",
      "attribute_filter": null
    }
    ```
    
    Find APPROVED applications:
    ```json
    {
      "node_type": "Application",
      "attribute_filter": {"eligibility": "APPROVED"}
    }
    ```
    
    Find Person nodes:
    ```json
    {
      "node_type": "Person",
      "attribute_filter": null
    }
    ```
    
    This endpoint tests:
    - Node filtering by type
    - Attribute matching
    - Graph traversal
    """
    try:
        if networkx_db.graph.number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail="Graph not loaded. Use /test/networkx/load-graph first")
        
        nodes = []
        for node, attrs in networkx_db.graph.nodes(data=True):
            # Filter by node type
            if query.node_type and attrs.get('node_type') != query.node_type:
                continue
            
            # Filter by attributes
            if query.attribute_filter:
                match = all(attrs.get(k) == v for k, v in query.attribute_filter.items())
                if not match:
                    continue
            
            nodes.append({"node_id": node, "attributes": attrs})
        
        return {
            "status": "success",
            "query": {
                "node_type": query.node_type,
                "filters": query.attribute_filter
            },
            "results_count": len(nodes),
            "data": nodes[:20]  # Limit to 20 for response size
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NetworkX query failed: {str(e)}")


@app.get("/test/networkx/get-neighbors/{node_id}", tags=["NetworkX Tests"])
async def test_networkx_neighbors(node_id: str):
    """
    Test NetworkX neighbor retrieval.
    
    **TEST DATA (Copy for Swagger UI):**
    ```
    node_id: APP-000001  (Get all connected nodes for application APP-000001)
    node_id: Person_Ahmed_Hassan  (Get all applications/documents for this person)
    node_id: Decision_APP-000001  (Get decision details)
    ```
    
    This endpoint tests:
    - Graph traversal
    - Edge following
    - Neighbor attribute access
    """
    try:
        if networkx_db.graph.number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail="Graph not loaded")
        
        if node_id not in networkx_db.graph:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found in graph")
        
        neighbors = []
        for neighbor in networkx_db.graph.neighbors(node_id):
            edge_data = networkx_db.graph.get_edge_data(node_id, neighbor)
            neighbors.append({
                "node_id": neighbor,
                "attributes": networkx_db.graph.nodes[neighbor],
                "edge_type": edge_data.get('edge_type', 'unknown')
            })
        
        return {
            "status": "success",
            "node_id": node_id,
            "neighbors_count": len(neighbors),
            "data": neighbors
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NetworkX neighbors query failed: {str(e)}")


@app.get("/test/networkx/graph-stats", tags=["NetworkX Tests"])
async def test_networkx_stats():
    """
    Test NetworkX graph statistics.
    
    This endpoint tests:
    - Node/edge counting
    - Degree distribution
    - Connected components
    """
    try:
        if networkx_db.graph.number_of_nodes() == 0:
            raise HTTPException(status_code=400, detail="Graph not loaded")
        
        import networkx as nx
        
        # Compute statistics
        stats = {
            "nodes": networkx_db.graph.number_of_nodes(),
            "edges": networkx_db.graph.number_of_edges(),
            "density": nx.density(networkx_db.graph),
            "is_connected": nx.is_weakly_connected(networkx_db.graph) if networkx_db.graph.is_directed() else nx.is_connected(networkx_db.graph)
        }
        
        # Node type distribution
        node_types = {}
        for node, attrs in networkx_db.graph.nodes(data=True):
            node_type = attrs.get('node_type', 'unknown')
            node_types[node_type] = node_types.get(node_type, 0) + 1
        
        stats['node_type_distribution'] = node_types
        
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NetworkX stats failed: {str(e)}")


# ============================================================================
# INTEGRATION TEST ENDPOINT
# ============================================================================

@app.get("/test/integration/verify-all", tags=["Integration Tests"])
async def test_integration():
    """
    Test integration across all databases.
    
    This endpoint verifies:
    1. SQLite has 40 applications
    2. TinyDB cache is operational
    3. ChromaDB has 240 documents indexed
    4. NetworkX graph is loaded
    """
    try:
        results = {}
        
        # Test SQLite
        try:
            sqlite_stats = sqlite_db.get_eligibility_stats()
            results['sqlite'] = {
                "status": "operational",
                "applications": sqlite_stats.get('total_applications', 0)
            }
        except Exception as e:
            results['sqlite'] = {"status": "error", "message": str(e)}
        
        # Test TinyDB
        try:
            cache_stats = tinydb_cache.get_cache_stats()
            results['tinydb'] = {
                "status": "operational",
                "cache_entries": cache_stats.get('rag_cache_entries', 0) + cache_stats.get('sessions', 0)
            }
        except Exception as e:
            results['tinydb'] = {"status": "error", "message": str(e)}
        
        # Test ChromaDB
        try:
            total_docs = 0
            for collection_name in ['application_summaries', 'resumes', 'income_patterns', 'case_decisions']:
                collection = getattr(chroma_db, collection_name, None)
                if collection:
                    total_docs += collection.count()
            
            results['chromadb'] = {
                "status": "operational",
                "documents": total_docs
            }
        except Exception as e:
            results['chromadb'] = {"status": "error", "message": str(e)}
        
        # Test NetworkX
        try:
            results['networkx'] = {
                "status": "operational" if networkx_db.graph.number_of_nodes() > 0 else "not_loaded",
                "nodes": networkx_db.graph.number_of_nodes(),
                "edges": networkx_db.graph.number_of_edges()
            }
        except Exception as e:
            results['networkx'] = {"status": "error", "message": str(e)}
        
        all_operational = all(r.get('status') == 'operational' for r in results.values())
        
        return {
            "status": "success" if all_operational else "partial_failure",
            "timestamp": datetime.now().isoformat(),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Integration test failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
