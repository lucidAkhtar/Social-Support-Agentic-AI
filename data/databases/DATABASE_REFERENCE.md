# Database Directory Reference

## Active Databases

### 1. **applications.db** (SQLite)
- **Size:** ~184 KB
- **Location:** `data/databases/applications.db`
- **Purpose:** Primary relational database for application data
- **Schema:**
  - `applications` table: 40 application records (demographics, income, family)
  - `decisions` table: 40 decision records (APPROVED/CONDITIONAL/DECLINED)
- **Used By:**
  - `src/databases/prod_sqlite_manager.py` - SQLiteManager
  - `src/api/main.py` - Statistics endpoint, application CRUD
  - `scripts/comprehensive_data_regeneration.py` - Data population
- **Status:** ACTIVE - Core production database

---

### 2. **chromadb/** (ChromaDB - Vector Database)
- **Size:** ~15 MB
- **Location:** `data/databases/chromadb/`
- **Purpose:** Document embeddings for semantic search (828 documents)
- **Collections:**
  - `resumes`: 73 documents (resume PDFs chunked + embedded)
  - `application_summaries`: 188 documents (employment letters, Emirates ID OCR)
  - `income_patterns`: 567 documents (bank statements, credit reports, assets/liabilities)
  - `case_decisions`: 0 documents (reserved for future use)
- **Used By:**
  - `src/databases/chroma_manager.py` - ChromaDBManager
  - `src/api/main.py` - RAG chatbot, semantic search endpoint
  - `scripts/ingest_documents_to_chromadb.py` - Document ingestion pipeline
- **Status:** ACTIVE - Production vector DB (updated Jan 1, 2026)

---

### 3. **cache.json** (TinyDB)
- **Size:** ~0 KB (empty)
- **Location:** `data/databases/cache.json`
- **Purpose:** Fast key-value cache for sessions and RAG queries
- **Tables:**
  - `sessions`: User session state
  - `rag_cache`: Cached RAG query results (TTL: 30 min)
  - `app_context`: Application context cache (TTL: 10 min)
  - `conversation_state`: Multi-turn chat tracking
- **Used By:**
  - `src/databases/tinydb_manager.py` - TinyDBManager
  - `src/api/main.py` - Session management, cache stats
  - RAG Chatbot Agent - Query caching
- **Status:**  ACTIVE - Runtime cache (empty when no active sessions)

---

### 4. **application_graph.graphml** (NetworkX)
- **Location:** `application_graph.graphml` (root - ACTIVE)
- **Purpose:** Graph database for application relationships
- **Nodes:** 120 (40 Applications + 40 Persons + 40 Decisions)
- **Edges:** 141 (APPLIED_BY, HAS_DECISION, SIMILAR_TO relationships)
- **Use Case:** Application Similarity Graph (find similar approved cases)
- **Used By:**
  - `src/databases/networkx_manager.py` - NetworkXManager
  - `src/api/main.py` - Loads from root: `Path("application_graph.graphml")`
  - `scripts/comprehensive_data_regeneration.py` - Graph building
- **Status:** ACTIVE - Uses root file (40 KB)


---

### 5. **governance.db** (Governance & Audit)
- **Size:** 256 KB (+ 32 KB -shm, 28 KB -wal)
- **Location:** `data/governance.db` (not in databases folder!)
- **Purpose:** Compliance and audit logging for GDPR/regulatory requirements
- **Schema:**
  - `audit_log`: Tracks all sensitive operations (access, modifications, decisions)
  - `gdpr_requests`: Data subject access requests
  - `consent_records`: User consent tracking
- **Used By:**
  - `src/services/governance.py` - AuditLogger, GovernanceService
  - Phase 8 governance tests
- **Status:** ACTIVE - Compliance requirement (keep)
- **Files:**
  - `governance.db` - Main database
  - `governance.db-shm` - SQLite shared memory (temporary)
  - `governance.db-wal` - Write-ahead log (temporary)

---
