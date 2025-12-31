"""
Production-Grade Logging, Auditing & Governance System
FAANG Standards: Structured logging, audit trails, compliance, M1 8GB optimized
"""
import logging
import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager
import threading
from functools import wraps
import time
import traceback
import sys


class StructuredLogger:
    """
    Structured logging with JSON output
    Optimized for M1 8GB: File rotation, memory-efficient
    """
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        self.logger.handlers = []
        
        # File handler - JSON structured logs (for automated parsing)
        json_handler = logging.FileHandler(
            self.log_dir / f"{name}_structured.jsonl",
            encoding='utf-8'
        )
        json_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(json_handler)
        
        # Console handler - human-readable (for debugging)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(console_handler)
        
        # Error file handler (separate file for errors)
        error_handler = logging.FileHandler(
            self.log_dir / f"{name}_errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n%(exc_info)s\n'
        ))
        self.logger.addHandler(error_handler)
    
    def info(self, message: str, **kwargs):
        """Log info with structured data"""
        self.logger.info(message, extra={'structured_data': kwargs})
    
    def error(self, message: str, **kwargs):
        """Log error with structured data"""
        self.logger.error(message, extra={'structured_data': kwargs})
    
    def warning(self, message: str, **kwargs):
        """Log warning with structured data"""
        self.logger.warning(message, extra={'structured_data': kwargs})
    
    def debug(self, message: str, **kwargs):
        """Log debug with structured data"""
        self.logger.debug(message, extra={'structured_data': kwargs})


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for structured logging"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add structured data if present
        if hasattr(record, 'structured_data'):
            log_data['data'] = record.structured_data
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


class AuditLogger:
    """
    Compliance-grade audit logging
    Tracks all sensitive operations for governance
    """
    
    def __init__(self, db_path: str = "data/governance.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._init_schema()
    
    @contextmanager
    def get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                timeout=30.0,
                check_same_thread=False
            )
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        
        yield self._local.conn
    
    def _init_schema(self):
        """Initialize audit tables"""
        with self.get_connection() as conn:
            # Audit trail table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT NOT NULL,
                    user_id TEXT,
                    application_id TEXT,
                    action TEXT NOT NULL,
                    resource TEXT,
                    resource_id TEXT,
                    details TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    status TEXT,
                    error_message TEXT
                )
            """)
            
            # API access log
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    method TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    application_id TEXT,
                    status_code INTEGER,
                    response_time_ms INTEGER,
                    ip_address TEXT,
                    user_agent TEXT,
                    request_body TEXT,
                    response_body TEXT
                )
            """)
            
            # Data access log (PII tracking)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    access_type TEXT NOT NULL,
                    fields_accessed TEXT,
                    purpose TEXT,
                    ip_address TEXT
                )
            """)
            
            # Performance metrics
            conn.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    metric_unit TEXT,
                    tags TEXT
                )
            """)
            
            # Indexes for fast queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_audit_app_id ON audit_log(application_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_timestamp ON api_access_log(timestamp DESC)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_api_endpoint ON api_access_log(endpoint)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_data_access ON data_access_log(resource_type, resource_id)")
            
            conn.commit()
    
    def log_audit_event(
        self,
        event_type: str,
        action: str,
        application_id: Optional[str] = None,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None
    ):
        """Log an audit event"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO audit_log (
                    event_type, action, application_id, user_id,
                    resource, resource_id, details, ip_address,
                    user_agent, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_type,
                action,
                application_id,
                user_id,
                resource,
                resource_id,
                json.dumps(details) if details else None,
                ip_address,
                user_agent,
                status,
                error_message
            ))
            conn.commit()
    
    def log_api_access(
        self,
        method: str,
        endpoint: str,
        application_id: Optional[str],
        status_code: int,
        response_time_ms: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_body: Optional[str] = None,
        response_body: Optional[str] = None
    ):
        """Log API access"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO api_access_log (
                    method, endpoint, application_id, status_code,
                    response_time_ms, ip_address, user_agent,
                    request_body, response_body
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                method,
                endpoint,
                application_id,
                status_code,
                response_time_ms,
                ip_address,
                user_agent,
                request_body[:1000] if request_body else None,  # Truncate large bodies
                response_body[:1000] if response_body else None
            ))
            conn.commit()
    
    def log_data_access(
        self,
        resource_type: str,
        resource_id: str,
        access_type: str,  # READ, WRITE, DELETE
        user_id: Optional[str] = None,
        fields_accessed: Optional[List[str]] = None,
        purpose: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log data access (for PII compliance)"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO data_access_log (
                    user_id, resource_type, resource_id, access_type,
                    fields_accessed, purpose, ip_address
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                resource_type,
                resource_id,
                access_type,
                json.dumps(fields_accessed) if fields_accessed else None,
                purpose,
                ip_address
            ))
            conn.commit()
    
    def log_metric(
        self,
        metric_name: str,
        metric_value: float,
        metric_unit: str = "",
        tags: Optional[Dict] = None
    ):
        """Log performance metric"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO performance_metrics (
                    metric_name, metric_value, metric_unit, tags
                ) VALUES (?, ?, ?, ?)
            """, (
                metric_name,
                metric_value,
                metric_unit,
                json.dumps(tags) if tags else None
            ))
            conn.commit()
    
    def get_audit_trail(
        self,
        application_id: Optional[str] = None,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Retrieve audit trail with filters"""
        with self.get_connection() as conn:
            query = "SELECT * FROM audit_log WHERE 1=1"
            params = []
            
            if application_id:
                query += " AND application_id = ?"
                params.append(application_id)
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]


def audit_endpoint(event_type: str):
    """
    Decorator to automatically audit API endpoints
    Usage: @audit_endpoint("application_access")
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            audit_logger = get_audit_logger()
            
            # Extract request context
            from fastapi import Request
            request = kwargs.get('request') or (args[0] if args and isinstance(args[0], Request) else None)
            
            application_id = kwargs.get('application_id') or kwargs.get('id')
            
            try:
                result = await func(*args, **kwargs)
                
                # Log successful access
                response_time_ms = int((time.time() - start_time) * 1000)
                
                audit_logger.log_audit_event(
                    event_type=event_type,
                    action=func.__name__,
                    application_id=application_id,
                    status="success",
                    ip_address=request.client.host if request else None,
                    user_agent=request.headers.get('user-agent') if request else None
                )
                
                audit_logger.log_metric(
                    f"endpoint.{func.__name__}.response_time",
                    response_time_ms,
                    "ms"
                )
                
                return result
                
            except Exception as e:
                # Log failed access
                audit_logger.log_audit_event(
                    event_type=event_type,
                    action=func.__name__,
                    application_id=application_id,
                    status="error",
                    error_message=str(e),
                    ip_address=request.client.host if request else None,
                    user_agent=request.headers.get('user-agent') if request else None
                )
                raise
        
        return wrapper
    return decorator


# Singleton instances
_audit_logger = None
_structured_logger = None

def get_audit_logger() -> AuditLogger:
    """Get singleton audit logger"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger

def get_structured_logger(name: str) -> StructuredLogger:
    """Get structured logger for a component"""
    return StructuredLogger(name)
