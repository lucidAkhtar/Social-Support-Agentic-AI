"""
TinyDB Manager - Lightweight NoSQL JSON Database (MongoDB Replacement)
Stores unstructured data: raw documents, OCR results, LLM responses, caches

Benefits over MongoDB for 8GB RAM:
- 10 MB memory footprint vs 800 MB
- No separate server process
- Fast JSON-based storage
- Perfect for demos and development
"""

from tinydb import TinyDB, Query, where
from tinydb.storages import JSONStorage
from tinydb.middlewares import CachingMiddleware
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class TinyDBManager:
    """
    Lightweight NoSQL database for unstructured data.
    Replaces MongoDB with minimal memory footprint.
    """
    
    def __init__(self, db_path: str = "data/databases/tinydb"):
        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize separate databases for different data types
        self.raw_documents = TinyDB(
            self.db_path / 'raw_documents.json',
            storage=CachingMiddleware(JSONStorage)
        )
        self.ocr_results = TinyDB(
            self.db_path / 'ocr_results.json',
            storage=CachingMiddleware(JSONStorage)
        )
        self.llm_responses = TinyDB(
            self.db_path / 'llm_responses.json',
            storage=CachingMiddleware(JSONStorage)
        )
        self.extraction_cache = TinyDB(
            self.db_path / 'extraction_cache.json',
            storage=CachingMiddleware(JSONStorage)
        )
        self.validation_cache = TinyDB(
            self.db_path / 'validation_cache.json',
            storage=CachingMiddleware(JSONStorage)
        )
        self.user_sessions = TinyDB(
            self.db_path / 'user_sessions.json',
            storage=CachingMiddleware(JSONStorage)
        )
        self.system_metrics = TinyDB(
            self.db_path / 'system_metrics.json',
            storage=CachingMiddleware(JSONStorage)
        )
        self.error_logs = TinyDB(
            self.db_path / 'error_logs.json',
            storage=CachingMiddleware(JSONStorage)
        )
        
        logger.info(f"TinyDB initialized at {self.db_path}")
    
    # ========== Raw Documents ==========
    
    def store_raw_document(self, application_id: str, document_type: str, 
                          document_data: Dict[str, Any]) -> int:
        """Store raw document data (images, PDFs, Excel as base64 or metadata)"""
        doc = {
            'application_id': application_id,
            'document_type': document_type,
            'uploaded_at': datetime.now().isoformat(),
            **document_data
        }
        doc_id = self.raw_documents.insert(doc)
        logger.info(f"Stored raw document: {document_type} for {application_id}")
        return doc_id
    
    def get_raw_documents(self, application_id: str) -> List[Dict[str, Any]]:
        """Retrieve all raw documents for an application"""
        Document = Query()
        return self.raw_documents.search(Document.application_id == application_id)
    
    def get_raw_document_by_type(self, application_id: str, 
                                 document_type: str) -> Optional[Dict[str, Any]]:
        """Get specific document type"""
        Document = Query()
        results = self.raw_documents.search(
            (Document.application_id == application_id) & 
            (Document.document_type == document_type)
        )
        return results[0] if results else None
    
    # ========== OCR Results ==========
    
    def store_ocr_result(self, application_id: str, document_id: str,
                        ocr_text: str, confidence: float, 
                        metadata: Dict[str, Any] = None) -> int:
        """Store OCR extraction results"""
        doc = {
            'application_id': application_id,
            'document_id': document_id,
            'ocr_text': ocr_text,
            'confidence': confidence,
            'extracted_at': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        doc_id = self.ocr_results.insert(doc)
        logger.info(f"Stored OCR result for {document_id}")
        return doc_id
    
    def get_ocr_results(self, application_id: str) -> List[Dict[str, Any]]:
        """Get all OCR results for an application"""
        OCR = Query()
        return self.ocr_results.search(OCR.application_id == application_id)
    
    # ========== LLM Responses ==========
    
    def store_llm_response(self, application_id: str, query: str, 
                          response: str, query_type: str,
                          model: str, tokens_used: int = 0) -> int:
        """Store LLM chat responses for history"""
        doc = {
            'application_id': application_id,
            'query': query,
            'response': response,
            'query_type': query_type,
            'model': model,
            'tokens_used': tokens_used,
            'timestamp': datetime.now().isoformat()
        }
        doc_id = self.llm_responses.insert(doc)
        logger.info(f"Stored LLM response for {application_id}")
        return doc_id
    
    def get_llm_history(self, application_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get LLM conversation history"""
        LLM = Query()
        results = self.llm_responses.search(LLM.application_id == application_id)
        # Sort by timestamp descending
        return sorted(results, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
    
    # ========== Extraction Cache ==========
    
    def cache_extraction(self, application_id: str, extracted_data: Dict[str, Any]) -> None:
        """Cache extraction results to avoid reprocessing"""
        Cache = Query()
        self.extraction_cache.upsert(
            {
                'application_id': application_id,
                'extracted_data': extracted_data,
                'cached_at': datetime.now().isoformat()
            },
            Cache.application_id == application_id
        )
        logger.info(f"Cached extraction for {application_id}")
    
    def get_cached_extraction(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached extraction"""
        Cache = Query()
        results = self.extraction_cache.search(Cache.application_id == application_id)
        return results[0] if results else None
    
    # ========== Validation Cache ==========
    
    def cache_validation(self, application_id: str, validation_result: Dict[str, Any]) -> None:
        """Cache validation results"""
        Cache = Query()
        self.validation_cache.upsert(
            {
                'application_id': application_id,
                'validation_result': validation_result,
                'cached_at': datetime.now().isoformat()
            },
            Cache.application_id == application_id
        )
        logger.info(f"Cached validation for {application_id}")
    
    def get_cached_validation(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached validation"""
        Cache = Query()
        results = self.validation_cache.search(Cache.application_id == application_id)
        return results[0] if results else None
    
    # ========== User Sessions ==========
    
    def create_session(self, session_id: str, user_data: Dict[str, Any]) -> int:
        """Create user session"""
        doc = {
            'session_id': session_id,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            **user_data
        }
        doc_id = self.user_sessions.insert(doc)
        logger.info(f"Created session {session_id}")
        return doc_id
    
    def update_session_activity(self, session_id: str) -> None:
        """Update last activity timestamp"""
        Session = Query()
        self.user_sessions.update(
            {'last_activity': datetime.now().isoformat()},
            Session.session_id == session_id
        )
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        Session = Query()
        results = self.user_sessions.search(Session.session_id == session_id)
        return results[0] if results else None
    
    # ========== System Metrics ==========
    
    def log_metric(self, metric_type: str, metric_name: str, 
                  value: float, metadata: Dict[str, Any] = None) -> int:
        """Log system performance metrics"""
        doc = {
            'metric_type': metric_type,
            'metric_name': metric_name,
            'value': value,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        doc_id = self.system_metrics.insert(doc)
        return doc_id
    
    def get_metrics(self, metric_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve system metrics"""
        if metric_type:
            Metric = Query()
            results = self.system_metrics.search(Metric.metric_type == metric_type)
        else:
            results = self.system_metrics.all()
        
        # Sort by timestamp descending
        return sorted(results, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
    
    # ========== Error Logs ==========
    
    def log_error(self, level: str, error_type: str, message: str, 
                 stack_trace: str = None, metadata: Dict[str, Any] = None) -> int:
        """Log application errors"""
        doc = {
            'level': level,
            'error_type': error_type,
            'message': message,
            'stack_trace': stack_trace,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat()
        }
        doc_id = self.error_logs.insert(doc)
        return doc_id
    
    def get_error_logs(self, level: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve error logs"""
        if level:
            Error = Query()
            results = self.error_logs.search(Error.level == level)
        else:
            results = self.error_logs.all()
        
        # Sort by timestamp descending
        return sorted(results, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
    
    # ========== Utility Methods ==========
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        return {
            'raw_documents': len(self.raw_documents),
            'ocr_results': len(self.ocr_results),
            'llm_responses': len(self.llm_responses),
            'extraction_cache': len(self.extraction_cache),
            'validation_cache': len(self.validation_cache),
            'user_sessions': len(self.user_sessions),
            'system_metrics': len(self.system_metrics),
            'error_logs': len(self.error_logs),
            'total_documents': sum([
                len(self.raw_documents),
                len(self.ocr_results),
                len(self.llm_responses),
                len(self.extraction_cache),
                len(self.validation_cache),
                len(self.user_sessions),
                len(self.system_metrics),
                len(self.error_logs)
            ])
        }
    
    def close_all(self):
        """Close all database connections"""
        self.raw_documents.close()
        self.ocr_results.close()
        self.llm_responses.close()
        self.extraction_cache.close()
        self.validation_cache.close()
        self.user_sessions.close()
        self.system_metrics.close()
        self.error_logs.close()
        logger.info("All TinyDB connections closed")
