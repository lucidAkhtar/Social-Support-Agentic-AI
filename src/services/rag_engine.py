"""
RAG Engine for Social Support Chatbot
==================================================
Production-ready RAG with advanced features:
- Multi-source context retrieval (4 databases)
- Vector embedding & semantic search
- Context ranking & relevance scoring
- Response caching & streaming
- Error handling & fallbacks
- Performance monitoring

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
        
        # Response cache (10 minutes TTL)
        self.response_cache = LRUCache(max_size=100, ttl_seconds=600)
        
        # Context cache (10 minutes TTL for frequently accessed data)
        self.context_cache = LRUCache(max_size=200, ttl_seconds=600)
        
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
                logger.info(f"[{application_id}] DEBUG - app_result from query_application: {app_result}")
                if app_result:
                    # app_result structure depends on source (cache vs database)
                    # From database: {'application': {...}, 'decision': {...}}
                    # From cache: {'context': {...}, 'decision': {...}} or flat {...}
                    
                    if 'application' in app_result:
                        # Database structure
                        context['application'] = app_result['application']
                        context['decision'] = app_result.get('decision', {}) if isinstance(app_result.get('decision'), dict) else {}
                    elif 'context' in app_result:
                        # TinyDB cache structure with separate context and decision
                        context['application'] = app_result['context']
                        context['decision'] = app_result.get('decision', {}) if isinstance(app_result.get('decision'), dict) else {}
                    else:
                        # Flat structure - application fields at root
                        context['application'] = app_result
                        # Decision might be string ("approved") or dict - check both
                        decision_field = app_result.get('decision')
                        if isinstance(decision_field, dict):
                            context['decision'] = decision_field
                        else:
                            # Decision is string or missing - initialize empty dict
                            context['decision'] = {}
                    
                    logger.info(f"[{application_id}] DEBUG - context['decision'] type: {type(context['decision'])}, keys: {list(context['decision'].keys()) if isinstance(context['decision'], dict) else 'N/A'}")
                    logger.info(f"[{application_id}] DEBUG - context['application']: {context['application']}")
                    
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
            
            # 4. NetworkX - Graph relationships (always query for graph context)
            try:
                if hasattr(self.db_manager, 'networkx'):
                    # Get similar applications (income/status similarity)
                    similar = self.db_manager.networkx.get_similar_applications(application_id, limit=3)
                    context['similar_cases'] = similar if similar else []
                    
                    # Get decision path (graph traversal)
                    try:
                        if hasattr(self.db_manager.networkx, 'trace_decision_path'):
                            path = self.db_manager.networkx.trace_decision_path(application_id)
                            context['decision_path'] = path if path else []
                    except Exception:
                        pass
                    
                    logger.info(f"NetworkX graph queried - found {len(similar)} similar cases")
            except Exception as e:
                logger.warning(f"NetworkX query failed: {e}")
            
            # 5. Fetch programs from SQLite decision conditions (JSON array)
            try:
                decision = context.get('decision', {})
                logger.info(f"[{application_id}] DEBUG - Fetching programs from decision: {decision}")
                conditions = decision.get('conditions') if decision else None
                logger.info(f"[{application_id}] DEBUG - Conditions field: {conditions}")
                
                if conditions:
                    # Parse conditions JSON to get program list
                    if isinstance(conditions, str):
                        try:
                            programs_list = json.loads(conditions)
                            if programs_list and isinstance(programs_list, list):
                                context['connected_programs'] = programs_list
                                logger.info(f"[{application_id}] Fetched {len(programs_list)} programs from decision conditions: {programs_list}")
                        except json.JSONDecodeError as json_err:
                            logger.warning(f"[{application_id}] Failed to parse decision conditions as JSON: {conditions}, Error: {json_err}")
                    elif isinstance(conditions, list):
                        context['connected_programs'] = conditions
                        logger.info(f"[{application_id}] Fetched {len(conditions)} programs from decision conditions (already list): {conditions}")
                else:
                    logger.warning(f"[{application_id}] No conditions field found in decision. Decision keys: {list(decision.keys()) if decision else 'None'}")
            except Exception as e:
                logger.warning(f"[{application_id}] Failed to fetch programs from decision conditions: {e}", exc_info=True)
            
            # 6. ChromaDB - Semantic search (if available and relevant)
            try:
                # Expanded keywords to trigger semantic search
                semantic_keywords = ['similar', 'like', 'compare', 'other', 'show', 'find', 
                                    'who', 'cases', 'examples', 'same', 'related', 'match']
                logger.info(f"[{application_id}] Checking if query '{query}' triggers semantic search...")
                if any(keyword in query.lower() for keyword in semantic_keywords):
                    logger.info(f"[{application_id}] ChromaDB semantic search TRIGGERED for query: {query}")
                    semantic_results = self.db_manager.semantic_search(query, limit=3)
                    context['semantic_matches'] = semantic_results if semantic_results else []
                    logger.info(f"[{application_id}] ChromaDB returned {len(semantic_results) if semantic_results else 0} results")
                else:
                    logger.info(f"[{application_id}] No semantic keywords found in query")
            except Exception as e:
                logger.warning(f"Semantic search failed: {e}", exc_info=True)
            
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
        
        # Always include connected programs (no filtering)
        if context.get('connected_programs'):
            ranked['connected_programs'] = context['connected_programs']
            logger.info(f"Including {len(context['connected_programs'])} connected programs from NetworkX")
        
        # CRITICAL: Always include similar cases and semantic matches (no filtering)
        if context.get('similar_cases'):
            ranked['similar_cases'] = context['similar_cases']
            logger.info(f"Including {len(context['similar_cases'])} similar_cases from NetworkX")
        
        if context.get('semantic_matches'):
            ranked['semantic_matches'] = context['semantic_matches']
            logger.info(f"Including {len(context['semantic_matches'])} semantic_matches from ChromaDB")
        
        # Rank other contexts (validation, extraction, etc.)
        for key in ['validation', 'extraction']:
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
Monthly Income: {app.get('monthly_income', 0)} AED
Monthly Expenses: {app.get('monthly_expenses', 0)} AED
Family Size: {app.get('family_size', 0)} members
Employment: {app.get('employment_status', 'N/A')}
Company: {app.get('company_name', 'N/A')}
Position: {app.get('current_position', 'N/A')}
Total Assets: {app.get('total_assets', 0)} AED
Total Liabilities: {app.get('total_liabilities', 0)} AED
Credit Score: {app.get('credit_score', 0)}
Credit Rating: {app.get('credit_rating', 'N/A')}
Payment History: {app.get('payment_ratio', 0)}% on-time
Outstanding Debt: {app.get('total_outstanding', 0)} AED
Status: {app.get('status', 'PENDING')}
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
        
        # Add recommended programs (always include if available, let Mistral decide)
        programs_summary = ""
        connected_programs = context.get('connected_programs', [])
        
        if connected_programs:
            programs_summary = f"\nRECOMMENDED PROGRAMS:\n"
            for program in connected_programs:
                if isinstance(program, dict):
                    prog_name = program.get('name', 'N/A')
                    prog_category = program.get('category', 'N/A')
                    prog_desc = program.get('description', 'N/A')
                    programs_summary += f"• {prog_name} ({prog_category}): {prog_desc}\n"
                else:
                    programs_summary += f"• {program}\n"
        
        # Add validation if relevant
        validation_summary = ""
        if context.get('validation') and 'issue' in query.lower():
            validation = context.get('validation', {})
            validation_summary = f"\nVALIDATION STATUS:\n{json.dumps(validation, indent=2)}\n"
        
        # CRITICAL: Only add similar cases if query explicitly asks for them
        similar_cases_summary = ""
        semantic_matches = context.get('semantic_matches', [])
        similar_cases = context.get('similar_cases', [])
        
        # Keywords that indicate user wants similar cases
        comparison_keywords = ['similar', 'compare', 'other', 'like', 'same', 'examples', 'cases', 'who else']
        wants_similar = any(keyword in query.lower() for keyword in comparison_keywords)
        
        app_id_log = app.get('app_id') or app.get('application_id') or 'UNKNOWN'
        
        if wants_similar and (semantic_matches or similar_cases):
            logger.info(f"[{app_id_log}] Including similar cases (query asked for comparison)")
            similar_cases_summary = "\nSIMILAR APPLICATIONS:\n"
            
            # Add NetworkX similar cases with app IDs
            if similar_cases:
                similar_cases_summary += f"NetworkX Graph Analysis (income ±2000 AED, same employment):\n"
                for sc_id in similar_cases[:5]:
                    similar_cases_summary += f"• Application {sc_id}\n"
            
            # Add ChromaDB semantic matches
            if semantic_matches:
                similar_cases_summary += f"\nChromaDB Semantic Search:\n"
                for match in semantic_matches[:3]:
                    metadata = match.get('metadata', {})
                    app_id = metadata.get('app_id', 'N/A')
                    distance = match.get('distance', 0)
                    similarity = round((1 - distance) * 100, 1)
                    
                    # Extract available metadata fields
                    name = metadata.get('applicant_name', '')
                    income = metadata.get('monthly_income', '')
                    employment = metadata.get('employment_status', '')
                    eligibility = metadata.get('eligibility', '')
                    
                    # Build bullet point
                    similar_cases_summary += f"• "
                    if name:
                        similar_cases_summary += f"{name} ({app_id})"
                    else:
                        similar_cases_summary += f"Application {app_id}"
                    
                    details = []
                    if income:
                        details.append(f"Income={income} AED")
                    if employment:
                        details.append(f"Employment={employment}")
                    if eligibility:
                        details.append(f"Status={eligibility}")
                    
                    if details:
                        similar_cases_summary += f" - {', '.join(details)}"
                    
                    similar_cases_summary += f" ({similarity}% similar)\n"
        
        # Add extracted features for explanation queries (first response)
        extracted_features = ""
        if query_type == "explanation":
            extracted_features = f"\nEXTRACTED FEATURES (From Document Analysis):\n"
            features = [
                ("Applicant Name", app.get('applicant_name', 'N/A')),
                ("Monthly Income", f"{app.get('monthly_income', 0)} AED"),
                ("Employment Status", app.get('employment_status', 'N/A')),
                ("Company", app.get('company_name', 'N/A')),
                ("Position", app.get('current_position', 'N/A')),
                ("Credit Score", app.get('credit_score', 0)),
                ("Total Assets", f"{app.get('total_assets', 0)} AED"),
                ("Total Liabilities", f"{app.get('total_liabilities', 0)} AED"),
                ("Family Size", app.get('family_size', 0)),
                ("Credit Rating", app.get('credit_rating', 'N/A'))
            ]
            for feature_name, feature_value in features:
                extracted_features += f"• {feature_name}: {feature_value}\n"
        
        # Get applicant name for personalization
        applicant_name = app.get('applicant_name', 'Applicant')
        
        # System instruction based on query type - STRICT FACTUAL CONSTRAINTS
        if query_type == "explanation":
            system_instruction = f"""You are a UAE Social Support case officer providing factual information about {applicant_name}'s application.

CRITICAL RULES:
1. ONLY use data from the APPLICATION DETAILS and DECISION INFORMATION sections below
2. DO NOT suggest contacting HR, financial advisors, or external parties
3. DO NOT make generic recommendations - use ONLY the specific programs listed in RECOMMENDED PROGRAMS
4. DO NOT mention "insufficient information" - use the data provided
5. If a field shows 0 or N/A, acknowledge it briefly and move on
6. Keep responses concise (2-3 paragraphs maximum)"""
        elif query_type == "simulation":
            system_instruction = f"""You are a social support analyst for {applicant_name}. Analyze using ONLY the factual data provided below. No generic advice."""
        else:
            system_instruction = f"""You are a UAE Social Support assistant for {applicant_name}.

STRICT RULES:
1. Answer using ONLY the factual data in the sections below
2. DO NOT suggest external consultations (HR, advisors, etc.)
3. For program questions: Use ONLY programs listed in RECOMMENDED PROGRAMS section
4. For comparison questions: Use ONLY data in SIMILAR APPLICATIONS section
5. Be direct and factual - no generic advice
6. Keep answers brief (2-3 paragraphs)"""
        
        prompt = f"""{system_instruction}

{app_summary}
{decision_summary}
{extracted_features}
{programs_summary}
{validation_summary}
{similar_cases_summary}

USER QUESTION: {query}

RESPONSE REQUIREMENTS:
1. Use ONLY the data provided above - no external suggestions
2. Be specific - reference actual numbers and program names
3. If asked about programs: List ONLY programs from RECOMMENDED PROGRAMS section
4. If asked for comparisons: Use ONLY data from SIMILAR APPLICATIONS section
5. DO NOT suggest: contacting HR, financial advisors, or any external parties
6. DO NOT provide: generic advice, hypothetical scenarios, or information not in the data above
7. Length: 2-3 paragraphs maximum

Your factual response:"""
        
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
                            "num_predict": 600,  # Increased to prevent truncation
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
                    
                    # Remove signature placeholder if present
                    response_text = self._clean_signature(response_text)
                    
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
    
    def _clean_signature(self, response: str) -> str:
        """
        Remove signature placeholders from LLM responses
        Cleans up unprofessional placeholder text
        """
        import re
        
        # Remove common signature placeholders
        placeholders = [
            r'\[Your Name\]',
            r'\[Your Position\]',
            r'\[Your Title\]',
            r'Best regards,\s*\[Your Name\]\s*\[Your Position\]',
            r'Sincerely,\s*\[Your Name\]\s*\[Your Position\]',
        ]
        
        for pattern in placeholders:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Clean up extra whitespace and newlines
        response = re.sub(r'\n{3,}', '\n\n', response)  # Max 2 newlines
        response = response.strip()
        
        return response
    
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
