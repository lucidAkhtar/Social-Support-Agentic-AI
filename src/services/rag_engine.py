"""
FAANG-Grade RAG Engine for Social Support Chatbot
==================================================
Production-ready RAG with advanced features:
- Multi-source context retrieval (4 databases)
- Vector embedding & semantic search
- Context ranking & relevance scoring
- Response caching & streaming
- Error handling & fallbacks
- Performance monitoring
- M1 8GB optimized

Author: Production Team
Date: December 31, 2025
"""
import logging
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict
import requests

logger = logging.getLogger("RAGEngine")


class ContextRanker:
    """Ranks and scores retrieved context by relevance"""
    
    @staticmethod
    def score_context(query: str, context: Dict[str, Any]) -> float:
        """
        Score context relevance using multiple signals
        Returns score 0.0-1.0
        """
        score = 0.0
        query_lower = query.lower()
        
        # Keyword matching (40%)
        keywords = {
            'income': ['monthly_income', 'income', 'salary', 'earnings'],
            'decision': ['decision', 'approved', 'declined', 'eligibility'],
            'family': ['family_size', 'dependents', 'children'],
            'assets': ['total_assets', 'assets', 'property', 'savings'],
            'debt': ['total_liabilities', 'debt', 'liabilities', 'loans'],
            'employment': ['employment_status', 'job', 'work', 'employer'],
            'credit': ['credit_score', 'credit', 'rating']
        }
        
        for category, terms in keywords.items():
            if any(term in query_lower for term in terms):
                if any(term in str(context).lower() for term in terms):
                    score += 0.4 / len(keywords)
        
        # Data completeness (30%)
        if isinstance(context, dict):
            non_empty = sum(1 for v in context.values() if v not in [None, '', 0, [], {}])
            total = len(context)
            if total > 0:
                score += 0.3 * (non_empty / total)
        
        # Recency (20%)
        if isinstance(context, dict):
            if 'timestamp' in context or 'created_at' in context:
                score += 0.2
        
        # Critical fields present (10%)
        critical_fields = ['application_id', 'decision', 'monthly_income']
        if isinstance(context, dict):
            present = sum(1 for f in critical_fields if f in context and context[f])
            score += 0.1 * (present / len(critical_fields))
        
        return min(score, 1.0)
    
    @staticmethod
    def rank_contexts(query: str, contexts: List[Dict[str, Any]]) -> List[Tuple[Dict, float]]:
        """
        Rank contexts by relevance score
        Returns [(context, score), ...] sorted by score descending
        """
        scored = [(ctx, ContextRanker.score_context(query, ctx)) for ctx in contexts]
        return sorted(scored, key=lambda x: x[1], reverse=True)


class LRUCache:
    """
    Least Recently Used cache with expiration
    M1 8GB optimized - limits memory usage
    """
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if key not in self.cache:
            self.misses += 1
            return None
        
        value, timestamp = self.cache[key]
        
        # Check expiration
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            self.misses += 1
            return None
        
        # Move to end (most recent)
        self.cache.move_to_end(key)
        self.hits += 1
        return value
    
    def put(self, key: str, value: Any):
        """Put value in cache"""
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = (value, time.time())
        
        # Evict oldest if over size
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def clear(self):
        """Clear cache"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total_requests': total,
            'hit_rate_percent': round(hit_rate, 2),
            'current_size': len(self.cache),
            'max_size': self.max_size
        }


class RAGEngine:
    """
    FAANG-Grade Retrieval-Augmented Generation Engine
    ================================================
    
    Features:
    - Multi-database context retrieval with fallbacks
    - Intelligent context ranking & filtering
    - Response caching with TTL
    - Error handling & retry logic
    - Performance monitoring
    - Streaming responses (optional)
    - M1 8GB memory optimized
    """
    
    def __init__(self, db_manager, ollama_url: str = "http://localhost:11434", 
                 ollama_model: str = "mistral:latest"):
        self.db_manager = db_manager
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        
        # Response cache (1 hour TTL)
        self.response_cache = LRUCache(max_size=100, ttl_seconds=3600)
        
        # Context cache (5 minutes TTL for frequently accessed data)
        self.context_cache = LRUCache(max_size=200, ttl_seconds=300)
        
        # Performance metrics
        self.metrics = {
            'total_queries': 0,
            'cache_hits': 0,
            'llm_calls': 0,
            'avg_response_time_ms': 0,
            'errors': 0,
            'context_retrieval_times': []
        }
        
        logger.info("RAG Engine initialized: Multi-DB + Caching + Ranking (M1 optimized)")
    
    def generate_response(self, query: str, application_id: str, 
                         query_type: str = "general") -> Dict[str, Any]:
        """
        Generate RAG response with full pipeline
        
        Args:
            query: User's question
            application_id: Application ID for context
            query_type: Type of query (general, explanation, simulation)
        
        Returns:
            {
                'response': str,
                'confidence': float,
                'sources': List[str],
                'cached': bool,
                'response_time_ms': int
            }
        """
        start_time = time.time()
        self.metrics['total_queries'] += 1
        
        try:
            # Check response cache first
            cache_key = self._get_cache_key(application_id, query)
            cached_response = self.response_cache.get(cache_key)
            
            if cached_response:
                self.metrics['cache_hits'] += 1
                logger.info(f"Cache HIT for {application_id}: {query[:50]}...")
                return {
                    **cached_response,
                    'cached': True,
                    'response_time_ms': int((time.time() - start_time) * 1000)
                }
            
            # 1. Retrieve context from all sources
            context = self._retrieve_context(application_id, query)
            
            # 2. Rank and filter context
            ranked_context = self._rank_and_filter_context(query, context)
            
            # 3. Build optimized prompt
            prompt = self._build_prompt(query, ranked_context, query_type)
            
            # 4. Call LLM with retry logic
            response_text, confidence = self._call_llm_with_retry(prompt)
            
            # CRITICAL: If unprocessed application, set low confidence
            if not context.get('has_data', False):
                confidence = 0.1  # Very low confidence for unprocessed apps
                sources = ['Application Status Check']
            else:
                # 5. Extract sources
                sources = self._extract_sources(ranked_context)
            
            # Build response
            result = {
                'response': response_text,
                'confidence': confidence,
                'sources': sources,
                'cached': False,
                'response_time_ms': int((time.time() - start_time) * 1000)
            }
            
            # Cache for future requests
            self.response_cache.put(cache_key, result)
            
            # Update metrics
            self.metrics['llm_calls'] += 1
            response_time = int((time.time() - start_time) * 1000)
            self._update_avg_response_time(response_time)
            
            logger.info(f"Generated response for {application_id} in {response_time}ms")
            return result
            
        except Exception as e:
            self.metrics['errors'] += 1
            logger.error(f"RAG error for {application_id}: {e}", exc_info=True)
            return {
                'response': f"I apologize, but I encountered an error processing your request: {str(e)}. Please try again or contact support if the issue persists.",
                'confidence': 0.0,
                'sources': [],
                'cached': False,
                'response_time_ms': int((time.time() - start_time) * 1000),
                'error': str(e)
            }
    
    def _retrieve_context(self, application_id: str, query: str) -> Dict[str, Any]:
        """
        Retrieve context from all 4 databases with caching
        CRITICAL: Detects unprocessed/pending applications and returns special flag
        """
        start_time = time.time()
        
        # Check context cache
        context_cache_key = f"context:{application_id}"
        cached_context = self.context_cache.get(context_cache_key)
        if cached_context:
            logger.debug(f"Context cache HIT for {application_id}")
            return cached_context
        
        context = {
            'application': {},
            'decision': {},
            'validation': {},
            'documents': [],
            'similar_cases': [],
            'semantic_matches': [],
            'graph_data': {},
            'is_processed': False,
            'has_data': False
        }
        
        try:
            # 1. SQLite - Application data (PRIMARY SOURCE)
            try:
                app_result = self.db_manager.query_application(application_id, include_full_context=False)
                if app_result:
                    context['application'] = app_result.get('application', {})
                    context['decision'] = app_result.get('decision', {})
                    
                    # CRITICAL CHECK: Is application actually processed?
                    app_data = context['application']
                    status = app_data.get('status', 'PENDING')
                    income = app_data.get('monthly_income', 0)
                    
                    # Check if application has real data (not just defaults)
                    # Must check multiple fields to determine if actually processed
                    # FIXED: Case-insensitive check (DB saves as 'completed', not 'COMPLETED')
                    context['is_processed'] = status.upper() in ['PROCESSED', 'COMPLETED'] if status else False
                    context['has_data'] = (
                        (income is not None and income > 0) or 
                        (app_data.get('monthly_expenses') is not None and app_data.get('monthly_expenses', 0) > 0) or
                        (app_data.get('credit_score') is not None and app_data.get('credit_score', 0) > 0) or
                        (app_data.get('employment_status') not in [None, 'Unknown', ''])
                    )
                    
                    logger.info(f"Application {application_id}: status={status}, has_data={context['has_data']}, income={income}, credit_score={app_data.get('credit_score', 0)}")
                    
            except Exception as e:
                logger.warning(f"SQLite application query failed: {e}")
            
            # 2. SQLite - Validation history
            try:
                if hasattr(self.db_manager.sqlite, 'get_validation_history'):
                    validation_history = self.db_manager.sqlite.get_validation_history(application_id)
                    if validation_history:
                        context['validation'] = validation_history[0]
                else:
                    logger.debug("get_validation_history method not available")
            except Exception as e:
                logger.warning(f"SQLite validation query failed: {e}")
            
            # 3. TinyDB - Cached extraction & documents
            try:
                if hasattr(self.db_manager.tinydb, 'get_cached_extraction'):
                    extraction = self.db_manager.tinydb.get_cached_extraction(application_id)
                elif hasattr(self.db_manager.tinydb, 'get_app_context'):
                    extraction = self.db_manager.tinydb.get_app_context(application_id)
                else:
                    extraction = None
                
                if extraction:
                    context['extraction'] = extraction
            except Exception as e:
                logger.warning(f"TinyDB query failed: {e}")
            
            # 4. NetworkX - Similar cases (if available)
            try:
                if hasattr(self.db_manager, 'networkx'):
                    similar = self.db_manager.networkx.get_similar_applications(application_id, limit=3)
                    context['similar_cases'] = similar if similar else []
            except Exception as e:
                logger.warning(f"NetworkX query failed: {e}")
            
            # 5. ChromaDB - Semantic search (if available and relevant)
            try:
                if any(keyword in query.lower() for keyword in ['similar', 'like', 'compare', 'other']):
                    semantic_results = self.db_manager.semantic_search(query, limit=3)
                    context['semantic_matches'] = semantic_results if semantic_results else []
            except Exception as e:
                logger.warning(f"Semantic search failed: {e}")
            
        except Exception as e:
            logger.error(f"Context retrieval error: {e}", exc_info=True)
        
        # Cache context for 5 minutes
        self.context_cache.put(context_cache_key, context)
        
        retrieval_time = int((time.time() - start_time) * 1000)
        self.metrics['context_retrieval_times'].append(retrieval_time)
        logger.debug(f"Context retrieved in {retrieval_time}ms")
        
        return context
    
    def _rank_and_filter_context(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rank and filter context by relevance
        Reduces prompt size by removing low-relevance data
        CRITICAL: Preserves has_data and is_processed flags
        """
        ranked = {}
        
        # CRITICAL: Preserve status flags
        ranked['has_data'] = context.get('has_data', False)
        ranked['is_processed'] = context.get('is_processed', False)
        
        # Always include application (highest priority)
        if context.get('application'):
            ranked['application'] = context['application']
        
        # Always include decision if available
        if context.get('decision'):
            ranked['decision'] = context['decision']
        
        # Rank other contexts
        for key in ['validation', 'extraction', 'semantic_matches', 'similar_cases']:
            if context.get(key):
                score = ContextRanker.score_context(query, context[key])
                if score > 0.3:  # Threshold: only include if >30% relevant
                    ranked[key] = context[key]
                    logger.debug(f"Including {key} (score: {score:.2f})")
        
        return ranked
    
    def _build_prompt(self, query: str, context: Dict[str, Any], query_type: str) -> str:
        """
        Build optimized prompt for LLM
        Uses structured format for better responses
        CRITICAL: Handles unprocessed applications specially
        """
        # CRITICAL CHECK: If application not processed, return special instruction
        has_data = context.get('has_data', False)
        is_processed = context.get('is_processed', False)
        
        logger.info(f"Building prompt: has_data={has_data}, is_processed={is_processed}")
        
        if not has_data or not is_processed:
            app = context.get('application', {})
            app_id = app.get('app_id', 'Unknown')
            name = app.get('applicant_name', 'the applicant')
            status = app.get('status', 'PENDING')
            
            logger.warning(f"Application {app_id} lacks data - guiding user to upload documents")
            
            return f"""You are a UAE Social Support assistant. The user asked: "{query}"

CRITICAL INFORMATION:
Application ID: {app_id}
Applicant: {name}
Status: {status}
Data Available: NO - Application has not been processed yet

INSTRUCTIONS:
This application is in {status} status and has NO extracted data yet. The applicant needs to:
1. Upload required documents (Emirates ID, Bank Statements, Resume, Assets/Liabilities, Credit Report)
2. Wait for document processing and validation
3. Then they can ask questions about their application

Your response MUST:
- Clearly state the application is in {status} status
- Explain that documents need to be uploaded first via the /upload endpoint
- List the required documents
- DO NOT make up information about "insufficient information provided"
- DO NOT discuss income/assets/credit score as if they were provided (they weren't)
- Be helpful and guide them on next steps

Generate a clear, accurate response now:"""
        
        app = context.get('application', {})
        decision = context.get('decision', {})
        
        # Build concise application summary
        app_summary = f"""
APPLICATION DETAILS:
ID: {app.get('app_id', app.get('application_id', 'N/A'))}
Name: {app.get('applicant_name', 'N/A')}
Income: {app.get('monthly_income', 0)} AED/month
Expenses: {app.get('monthly_expenses', 0)} AED/month
Family Size: {app.get('family_size', 0)} members
Employment: {app.get('employment_status', 'N/A')}
Company: {app.get('company_name', 'N/A')}
Position: {app.get('current_position', 'N/A')}
Monthly Salary: {app.get('monthly_salary', 0)} AED
Assets: {app.get('total_assets', 0)} AED
Liabilities: {app.get('total_liabilities', 0)} AED
Credit Score: {app.get('credit_score', 0)}
Credit Rating: {app.get('credit_rating', 'N/A')}
Payment History: {app.get('payment_ratio', 0)}% on-time
Outstanding Debt: {app.get('total_outstanding', 0)} AED
Decision: {app.get('decision', app.get('eligibility', 'PENDING'))}
"""
        
        decision_summary = ""
        if decision or app.get('decision'):
            # Decision might be in app object or separate
            dec = decision if decision else {}
            decision_summary = f"""
DECISION INFORMATION:
Status: {app.get('decision', dec.get('decision_type', 'PENDING'))}
Policy Score: {app.get('policy_score', dec.get('policy_score', 0))}/100
Support Amount: {app.get('support_amount', dec.get('support_amount', 0))} AED
Duration: {app.get('duration_months', dec.get('duration_months', 0))} months
Reasoning: {app.get('reasoning', dec.get('reasoning', 'Not available'))}
"""
        
        # Add validation if relevant
        validation_summary = ""
        if context.get('validation') and 'issue' in query.lower():
            validation = context.get('validation', {})
            validation_summary = f"\nVALIDATION STATUS:\n{json.dumps(validation, indent=2)}\n"
        
        # System instruction based on query type
        if query_type == "explanation":
            system_instruction = "You are an expert social support advisor. Explain decisions clearly using specific data from the application."
        elif query_type == "simulation":
            system_instruction = "You are a social support analyst. Analyze hypothetical scenarios based on historical patterns."
        else:
            system_instruction = "You are a helpful UAE Social Support assistant. Answer questions accurately using the application data provided."
        
        prompt = f"""{system_instruction}

{app_summary}
{decision_summary}
{validation_summary}

USER QUESTION: {query}

INSTRUCTIONS:
1. Answer using SPECIFIC data from the application above
2. Reference exact numbers and facts
3. Be direct and concise (2-4 paragraphs)
4. If data is missing, acknowledge it clearly
5. Maintain a helpful, professional tone

Your response:"""
        
        return prompt
    
    def _call_llm_with_retry(self, prompt: str, max_retries: int = 2) -> Tuple[str, float]:
        """
        Call LLM with retry logic and timeout
        Returns (response_text, confidence_score)
        """
        for attempt in range(max_retries + 1):
            try:
                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json={
                        "model": self.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": 400,  # Optimized for concise responses
                            "top_p": 0.9,
                            "top_k": 40,
                            "stop": ["\n\nUSER", "\n\nINSTRUCTIONS"]
                        }
                    },
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '').strip()
                    
                    # Calculate confidence based on response quality
                    confidence = self._calculate_confidence(response_text)
                    
                    return response_text, confidence
                else:
                    logger.error(f"LLM error: {response.status_code}")
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                    
            except requests.Timeout:
                logger.error(f"LLM timeout (attempt {attempt + 1}/{max_retries + 1})")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                continue
            except requests.ConnectionError:
                logger.error("LLM connection failed - is Ollama running?")
                return "I cannot connect to the AI service. Please ensure Ollama is running with 'ollama serve'.", 0.0
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                continue
        
        return "I apologize, but I'm having trouble generating a response right now. Please try again in a moment.", 0.0
    
    def _calculate_confidence(self, response: str) -> float:
        """
        Calculate confidence score for response
        Based on response quality indicators
        """
        score = 0.5  # Base score
        
        # Length check (good responses are 50-800 chars)
        length = len(response)
        if 50 <= length <= 800:
            score += 0.2
        
        # Contains specific numbers (indicates data usage)
        if any(char.isdigit() for char in response):
            score += 0.15
        
        # Contains "AED" (using UAE currency = using real data)
        if "AED" in response:
            score += 0.1
        
        # Not an error message
        if not any(word in response.lower() for word in ['error', 'cannot', "can't", 'unable', 'sorry']):
            score += 0.05
        
        return min(score, 1.0)
    
    def _extract_sources(self, context: Dict[str, Any]) -> List[str]:
        """Extract source databases used"""
        sources = []
        if context.get('application'):
            sources.append('SQLite Database')
        if context.get('extraction'):
            sources.append('TinyDB Cache')
        if context.get('similar_cases'):
            sources.append('NetworkX Graph')
        if context.get('semantic_matches'):
            sources.append('ChromaDB Vectors')
        return sources
    
    def _get_cache_key(self, application_id: str, query: str) -> str:
        """Generate cache key"""
        query_normalized = query.lower().strip()
        return hashlib.md5(f"{application_id}:{query_normalized}".encode()).hexdigest()
    
    def _update_avg_response_time(self, response_time_ms: int):
        """Update rolling average response time"""
        current_avg = self.metrics['avg_response_time_ms']
        total_calls = self.metrics['llm_calls']
        self.metrics['avg_response_time_ms'] = int(
            (current_avg * (total_calls - 1) + response_time_ms) / total_calls
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine performance metrics"""
        cache_stats = self.response_cache.stats()
        context_cache_stats = self.context_cache.stats()
        
        avg_retrieval = 0
        if self.metrics['context_retrieval_times']:
            avg_retrieval = sum(self.metrics['context_retrieval_times']) / len(self.metrics['context_retrieval_times'])
        
        return {
            'queries': {
                'total': self.metrics['total_queries'],
                'cached': self.metrics['cache_hits'],
                'llm_calls': self.metrics['llm_calls'],
                'errors': self.metrics['errors']
            },
            'performance': {
                'avg_response_time_ms': self.metrics['avg_response_time_ms'],
                'avg_context_retrieval_ms': round(avg_retrieval, 2)
            },
            'caching': {
                'response_cache': cache_stats,
                'context_cache': context_cache_stats
            }
        }
    
    def clear_caches(self):
        """Clear all caches"""
        self.response_cache.clear()
        self.context_cache.clear()
        logger.info("All caches cleared")
