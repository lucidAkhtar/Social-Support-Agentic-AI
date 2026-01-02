"""
Production-Grade SQLite Database Manager
FAANG Standards: Connection pooling, prepared statements, transactions, indexes
Purpose: Internal knowledge warehouse for chatbot queries
"""
import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager
import threading


class SQLiteManager:
    """
    SQLite database manager for application data, decisions, and analytics.
    
    Schema Design:
    1. applications: Core application data with eligibility scores
    2. decisions: Decision history with reasoning
    3. documents: Document metadata and extraction status
    4. conversations: Chat history for context-aware responses
    5. analytics: Pre-computed aggregations for fast queries
    
    Indexing Strategy:
    - Primary keys: app_id, decision_id, document_id
    - Secondary indexes: status, decision, submission_date
    - Full-text search: FTS5 virtual table for document content
    """
    
    def __init__(self, db_path: str = "data/databases/applications.db"):
        """Initialize database with connection pool"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Thread-local storage for connections
        self._local = threading.local()
        
        # Initialize schema
        self._init_schema()
        self._create_indexes()
        self._create_fts_tables()
    
    @contextmanager
    def get_connection(self):
        """Get thread-local database connection with WAL mode"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA synchronous=NORMAL")
            self._local.conn.execute("PRAGMA cache_size=10000")
            self._local.conn.execute("PRAGMA temp_store=MEMORY")
        
        try:
            yield self._local.conn
        except Exception as e:
            self._local.conn.rollback()
            raise
    
    def _init_schema(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            conn.executescript("""
                -- Applications table
                CREATE TABLE IF NOT EXISTS applications (
                    app_id TEXT PRIMARY KEY,
                    applicant_name TEXT NOT NULL,
                    emirates_id TEXT UNIQUE NOT NULL,
                    submission_date TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    monthly_income REAL NOT NULL,
                    monthly_expenses REAL NOT NULL,
                    family_size INTEGER NOT NULL,
                    employment_status TEXT NOT NULL,
                    total_assets REAL NOT NULL,
                    total_liabilities REAL NOT NULL,
                    net_worth REAL GENERATED ALWAYS AS (total_assets - total_liabilities) STORED,
                    credit_score INTEGER NOT NULL,
                    policy_score REAL,
                    ml_prediction TEXT,
                    ml_confidence REAL,
                    eligibility TEXT,
                    support_amount REAL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                
                -- Decisions table
                CREATE TABLE IF NOT EXISTS decisions (
                    decision_id TEXT PRIMARY KEY,
                    app_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    decision_date TEXT NOT NULL,
                    decided_by TEXT NOT NULL DEFAULT 'SYSTEM',
                    policy_score REAL NOT NULL,
                    ml_score REAL,
                    priority TEXT NOT NULL,
                    reasoning TEXT,
                    support_type TEXT,
                    support_amount REAL,
                    duration_months INTEGER,
                    conditions TEXT,
                    FOREIGN KEY (app_id) REFERENCES applications(app_id)
                );
                
                -- Documents table
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    app_id TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    upload_date TEXT NOT NULL,
                    extraction_status TEXT DEFAULT 'PENDING',
                    extraction_confidence REAL,
                    extracted_text TEXT,
                    metadata TEXT,
                    FOREIGN KEY (app_id) REFERENCES applications(app_id)
                );
                
                -- Conversations table (for chatbot context)
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    app_id TEXT,
                    user_query TEXT NOT NULL,
                    bot_response TEXT NOT NULL,
                    intent TEXT,
                    entities TEXT,
                    rag_context TEXT,
                    timestamp TEXT NOT NULL DEFAULT (datetime('now')),
                    response_time_ms INTEGER,
                    FOREIGN KEY (app_id) REFERENCES applications(app_id)
                );
                
                -- Analytics table (pre-computed stats)
                CREATE TABLE IF NOT EXISTS analytics (
                    metric_name TEXT PRIMARY KEY,
                    metric_value REAL NOT NULL,
                    metric_details TEXT,
                    computed_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
            """)
            conn.commit()
    
    def _create_indexes(self):
        """Create indexes for fast lookups"""
        with self.get_connection() as conn:
            conn.executescript("""
                -- Application indexes
                CREATE INDEX IF NOT EXISTS idx_app_status ON applications(status);
                CREATE INDEX IF NOT EXISTS idx_app_submission ON applications(submission_date);
                CREATE INDEX IF NOT EXISTS idx_app_eligibility ON applications(eligibility);
                CREATE INDEX IF NOT EXISTS idx_app_policy_score ON applications(policy_score);
                
                -- Decision indexes
                CREATE INDEX IF NOT EXISTS idx_decision_app ON decisions(app_id);
                CREATE INDEX IF NOT EXISTS idx_decision_date ON decisions(decision_date);
                CREATE INDEX IF NOT EXISTS idx_decision_priority ON decisions(priority);
                CREATE INDEX IF NOT EXISTS idx_decision_type ON decisions(decision);
                
                -- Document indexes
                CREATE INDEX IF NOT EXISTS idx_doc_app ON documents(app_id);
                CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(document_type);
                CREATE INDEX IF NOT EXISTS idx_doc_status ON documents(extraction_status);
                
                -- Conversation indexes
                CREATE INDEX IF NOT EXISTS idx_conv_session ON conversations(session_id);
                CREATE INDEX IF NOT EXISTS idx_conv_app ON conversations(app_id);
                CREATE INDEX IF NOT EXISTS idx_conv_time ON conversations(timestamp);
            """)
            conn.commit()
    
    def _create_fts_tables(self):
        """Create full-text search virtual tables"""
        with self.get_connection() as conn:
            try:
                conn.executescript("""
                    -- FTS5 virtual table for document search
                    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                        app_id, document_type, extracted_text,
                        content='documents',
                        content_rowid='rowid'
                    );
                    
                    -- Triggers to keep FTS in sync
                    CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                        INSERT INTO documents_fts(rowid, app_id, document_type, extracted_text)
                        VALUES (new.rowid, new.app_id, new.document_type, new.extracted_text);
                    END;
                    
                    CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                        UPDATE documents_fts SET extracted_text = new.extracted_text
                        WHERE rowid = new.rowid;
                    END;
                    
                    CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                        DELETE FROM documents_fts WHERE rowid = old.rowid;
                    END;
                """)
                conn.commit()
            except sqlite3.OperationalError:
                pass  # FTS5 might not be available
    
    # ============================================================================
    # CHATBOT QUERY METHODS - These power the conversational interface
    # ============================================================================
    
    def get_application(self, app_id: str) -> Optional[Dict]:
        """
        Get complete application data with all related information.
        Production-grade method with comprehensive error handling.
        
        Returns:
            Dict with application, decision, and metadata or None if not found
        
        Raises:
            sqlite3.Error: Database errors are logged and re-raised
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        a.app_id,
                        a.applicant_name,
                        a.emirates_id,
                        a.submission_date,
                        a.status,
                        a.monthly_income,
                        a.monthly_expenses,
                        a.family_size,
                        a.employment_status,
                        a.total_assets,
                        a.total_liabilities,
                        a.credit_score,
                        a.net_worth,
                        a.company_name,
                        a.current_position,
                        a.join_date,
                        a.credit_rating,
                        a.credit_accounts,
                        a.payment_ratio,
                        a.total_outstanding,
                        a.work_experience_years,
                        a.education_level,
                        d.decision,
                        d.policy_score,
                        d.ml_score,
                        d.priority,
                        d.support_amount,
                        d.support_type,
                        d.duration_months,
                        d.decision_date,
                        d.reasoning,
                        d.conditions
                    FROM applications a
                    LEFT JOIN decisions d ON a.app_id = d.app_id
                    WHERE a.app_id = ?
                """, (app_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                result = dict(row)
                return result
                
        except sqlite3.Error as e:
            print(f"Database error retrieving application {app_id}: {e}")
            raise
    
    def get_application_status(self, app_id: str) -> Optional[Dict]:
        """
        Get full application status for chatbot response.
        Alias for get_application for backward compatibility.
        """
        return self.get_application(app_id)
    
    def search_similar_cases(self, income: float, family_size: int, limit: int = 5) -> List[Dict]:
        """
        Find similar cases for precedent-based responses.
        
        Usage in chatbot:
        User: "Show me similar cases to income 5000 AED with family of 4"
        Chatbot: Calls this → Returns similar cases → Explains patterns
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    app_id,
                    applicant_name,
                    monthly_income,
                    family_size,
                    policy_score,
                    eligibility,
                    support_amount,
                    ABS(monthly_income - ?) + ABS(family_size - ?) * 500 as similarity_score
                FROM applications
                WHERE status = 'PROCESSED'
                ORDER BY similarity_score ASC
                LIMIT ?
            """, (income, family_size, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_eligibility_stats(self) -> Dict:
        """
        Get system-wide statistics for context.
        
        Usage in chatbot:
        User: "What are the average approval rates?"
        Chatbot: Calls this → Returns stats → Provides insights
        """
        with self.get_connection() as conn:
            # Join with decisions table to get accurate decision counts
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_applications,
                    SUM(CASE WHEN d.decision = 'APPROVED' THEN 1 ELSE 0 END) as approved,
                    SUM(CASE WHEN d.decision = 'DECLINED' THEN 1 ELSE 0 END) as declined,
                    SUM(CASE WHEN d.decision = 'CONDITIONAL' THEN 1 ELSE 0 END) as conditional,
                    AVG(d.policy_score) as avg_policy_score,
                    AVG(d.support_amount) as avg_support_amount,
                    AVG(a.monthly_income) as avg_income,
                    AVG(a.family_size) as avg_family_size
                FROM applications a
                LEFT JOIN decisions d ON a.app_id = d.app_id
                WHERE a.status IN ('COMPLETED', 'PROCESSED')
            """)
            
            return dict(cursor.fetchone())
    
    def full_text_search(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Full-text search across applications.
        
        Searches applicant names, employment status, and other text fields.
        """
        with self.get_connection() as conn:
            # Search applications using LIKE (FTS for documents is for uploaded files)
            cursor = conn.execute("""
                SELECT 
                    a.app_id,
                    a.applicant_name,
                    a.employment_status,
                    a.monthly_income,
                    a.family_size,
                    a.credit_score,
                    d.decision as eligibility,
                    d.policy_score,
                    d.support_amount
                FROM applications a
                LEFT JOIN decisions d ON a.app_id = d.app_id
                WHERE 
                    a.applicant_name LIKE ? OR
                    a.employment_status LIKE ? OR
                    d.decision LIKE ? OR
                    CAST(a.monthly_income AS TEXT) LIKE ? OR
                    CAST(a.family_size AS TEXT) LIKE ?
                ORDER BY a.submission_date DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_decision_by_app_id(self, app_id: str) -> Optional[Dict]:
        """
        Get decision for a specific application.
        
        Returns the most recent decision for the application.
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    d.*,
                    a.applicant_name,
                    a.monthly_income,
                    a.family_size,
                    a.policy_score
                FROM decisions d
                JOIN applications a ON d.app_id = a.app_id
                WHERE d.app_id = ?
                ORDER BY d.decision_date DESC
                LIMIT 1
            """, (app_id,))
            
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def get_decision_history(self, limit: int = 20) -> List[Dict]:
        """
        Get recent decision history for pattern analysis.
        
        Usage in chatbot:
        User: "What were the recent decisions?"
        Chatbot: Calls this → Returns history → Explains trends
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    d.*,
                    a.applicant_name,
                    a.monthly_income,
                    a.family_size,
                    a.policy_score
                FROM decisions d
                JOIN applications a ON d.app_id = a.app_id
                ORDER BY d.decision_date DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def store_conversation(self, session_id: str, user_query: str, bot_response: str,
                          app_id: Optional[str] = None, intent: Optional[str] = None,
                          entities: Optional[Dict] = None, rag_context: Optional[str] = None,
                          response_time_ms: Optional[int] = None):
        """
        Store conversation for context and analytics.
        
        Usage: Every chatbot interaction is logged for:
        1. Context retrieval in multi-turn conversations
        2. Analytics on common queries
        3. Training data for fine-tuning
        """
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO conversations (
                    session_id, app_id, user_query, bot_response,
                    intent, entities, rag_context, response_time_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_id, app_id, user_query, bot_response,
                intent,
                json.dumps(entities) if entities else None,
                rag_context,
                response_time_ms
            ))
            conn.commit()
    
    def get_conversation_context(self, session_id: str, last_n: int = 5) -> List[Dict]:
        """
        Get conversation history for context-aware responses.
        
        Usage in chatbot:
        User: "What about the income?" (referring to previous query)
        Chatbot: Retrieves last 5 messages → Understands context → Responds appropriately
        """
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT *
                FROM conversations
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (session_id, last_n))
            
            return [dict(row) for row in cursor.fetchall()][::-1]  # Reverse to chronological
    
    # ============================================================================
    # DATA INGESTION METHODS
    # ============================================================================
    
    def insert_application(self, app_data: Dict):
        """Insert or update application data"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO applications (
                    app_id, applicant_name, emirates_id, submission_date, status,
                    monthly_income, monthly_expenses, family_size, employment_status,
                    total_assets, total_liabilities, credit_score, policy_score,
                    ml_prediction, ml_confidence, eligibility, support_amount,
                    company_name, current_position, join_date, credit_rating,
                    credit_accounts, payment_ratio, total_outstanding,
                    work_experience_years, education_level
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                app_data['app_id'], app_data['applicant_name'], app_data['emirates_id'],
                app_data['submission_date'], app_data['status'],
                app_data['monthly_income'], app_data['monthly_expenses'], app_data['family_size'],
                app_data['employment_status'], app_data['total_assets'], app_data['total_liabilities'],
                app_data['credit_score'], app_data.get('policy_score'), app_data.get('ml_prediction'),
                app_data.get('ml_confidence'), app_data.get('eligibility'), app_data.get('support_amount'),
                app_data.get('company_name'), app_data.get('current_position'), app_data.get('join_date'),
                app_data.get('credit_rating'), app_data.get('credit_accounts'), app_data.get('payment_ratio'),
                app_data.get('total_outstanding'), app_data.get('work_experience_years'), app_data.get('education_level')
            ))
            conn.commit()
    
    def insert_decision(self, decision_data: Dict):
        """Insert decision record"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO decisions (
                    decision_id, app_id, decision, decision_date, decided_by,
                    policy_score, ml_score, priority, reasoning,
                    support_type, support_amount, duration_months, conditions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                decision_data['decision_id'], decision_data['app_id'], decision_data['decision'],
                decision_data['decision_date'], decision_data.get('decided_by', 'SYSTEM'),
                decision_data['policy_score'], decision_data.get('ml_score'),
                decision_data['priority'], decision_data.get('reasoning'),
                decision_data.get('support_type'), decision_data.get('support_amount'),
                decision_data.get('duration_months'), decision_data.get('conditions')
            ))
            conn.commit()
    
    def insert_document(self, doc_data: Dict):
        """Insert document metadata"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents (
                    document_id, app_id, document_type, file_name, file_path,
                    upload_date, extraction_status, extraction_confidence,
                    extracted_text, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_data['document_id'], doc_data['app_id'], doc_data['document_type'],
                doc_data['file_name'], doc_data['file_path'], doc_data['upload_date'],
                doc_data.get('extraction_status', 'PENDING'),
                doc_data.get('extraction_confidence'),
                doc_data.get('extracted_text'),
                json.dumps(doc_data.get('metadata')) if doc_data.get('metadata') else None
            ))
            conn.commit()
    
    def update_analytics(self, metric_name: str, metric_value: float, metric_details: Optional[Dict] = None):
        """Update analytics metric"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO analytics (metric_name, metric_value, metric_details)
                VALUES (?, ?, ?)
            """, (
                metric_name, metric_value,
                json.dumps(metric_details) if metric_details else None
            ))
            conn.commit()
    
    def close(self):
        """Close all connections"""
        if hasattr(self._local, 'conn'):
            self._local.conn.close()