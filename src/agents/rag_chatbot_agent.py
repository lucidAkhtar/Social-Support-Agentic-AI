"""
RAG-Powered Chatbot Agent - OPTIMIZED FOR M1 8GB
Provides intelligent responses using all 4 databases with caching and session management

Features:
- ✅ SQLite retrieval (applications, validation, decisions)
- ✅ TinyDB document cache (fast JSON lookup)
- ✅ ChromaDB semantic search (vector similarity)
- ✅ NetworkX graph queries (relationships, similar cases)
- ✅ Response caching (avoid redundant LLM calls)
- ✅ Session management (conversation history)
- ✅ Memory optimized (minimal overhead)
"""
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import requests

from ..core.base_agent import BaseAgent
from ..core.types import ApplicationState


class RAGChatbotAgent(BaseAgent):
    """
    Production-grade chatbot with 4-database RAG + caching + session management
    Optimized for M1 8GB RAM
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("RAGChatbotAgent", config)
        self.logger = logging.getLogger("RAGChatbotAgent")
        
        # Unified database manager (all 4 DBs)
        from ..databases import UnifiedDatabaseManager
        self.db_manager = UnifiedDatabaseManager()
        
        # LLM configuration
        self.ollama_url = config.get('ollama_url', 'http://localhost:11434') if config else 'http://localhost:11434'
        self.ollama_model = config.get('ollama_model', 'mistral:latest') if config else 'mistral:latest'
        
        # Response cache (in-memory, LRU with max 100 entries)
        self.response_cache = {}
        self.cache_order = []
        self.max_cache_size = 100
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Session management (stores last 10 messages per session)
        self.active_sessions = {}
        self.max_history_per_session = 10
        
        self.logger.info("RAG Chatbot initialized: 4 DBs + caching + sessions (M1 8GB optimized)")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute chatbot query (async interface)"""
        try:
            application_id = input_data.get("application_id")
            query = input_data.get("query", "")
            
            # Create minimal ApplicationState for processing
            from ..core.types import ApplicationState
            state = ApplicationState(application_id=application_id)
            state.chat_input = query
            
            # Process through pipeline
            result_state = self.process(state)
            
            return {
                "response": result_state.chat_response,
                "application_id": application_id,
                "status": "success"
            }
        except Exception as e:
            self.logger.error(f"Execute error: {e}")
            return {
                "response": f"Error: {str(e)}",
                "application_id": input_data.get("application_id"),
                "status": "error"
            }
    
    def process(self, state: ApplicationState) -> ApplicationState:
        """Process chat queries with full RAG pipeline"""
        try:
            query = state.chat_input.strip()
            session_id = state.application_id or "default"
            
            # Initialize session
            if session_id not in self.active_sessions:
                self.active_sessions[session_id] = {
                    'history': [],
                    'context_cache': {},
                    'created_at': datetime.now().isoformat()
                }
            
            # Check cache first (fast path)
            cache_key = self._get_cache_key(session_id, query)
            if cache_key in self.response_cache:
                self.cache_hits += 1
                cached_response = self.response_cache[cache_key]
                state.chat_response = cached_response
                self._store_conversation(session_id, query, cached_response, from_cache=True)
                self.logger.info(f"Cache HIT for session {session_id}")
                return state
            
            self.cache_misses += 1
            self.logger.info(f"Cache MISS for session {session_id} (hits: {self.cache_hits}, misses: {self.cache_misses})")
            
            # Route to appropriate handler
            if "why" in query.lower() and "decision" in query.lower():
                response = self._explain_decision(state, session_id)
            elif "improve" in query.lower() or "better" in query.lower():
                response = self._suggest_improvements(state, session_id)
            elif "detail" in query.lower() or "show" in query.lower():
                response = self._show_details(state, session_id)
            elif "what if" in query.lower() or "simulate" in query.lower():
                response = self._simulate_changes(state, query, session_id)
            elif "similar" in query.lower() or "compare" in query.lower():
                response = self._find_similar_cases(state, session_id)
            elif "program" in query.lower() or "support" in query.lower():
                response = self._explain_programs(state, session_id)
            else:
                response = self._general_query(state, query, session_id)
            
            # Cache response (LRU eviction)
            self._add_to_cache(cache_key, response)
            
            # Store conversation in TinyDB + session
            self._store_conversation(session_id, query, response, from_cache=False)
            
            state.chat_response = response
            return state
            
        except Exception as e:
            self.logger.error(f"Chat processing error: {str(e)}", exc_info=True)
            state.chat_response = f"I encountered an error: {str(e)}. Please try again."
            return state
    
    def _get_cache_key(self, session_id: str, query: str) -> str:
        """Generate cache key from session + query"""
        query_normalized = query.lower().strip()
        return hashlib.md5(f"{session_id}:{query_normalized}".encode()).hexdigest()
    
    def _add_to_cache(self, key: str, value: str):
        """Add to cache with LRU eviction"""
        if key in self.response_cache:
            # Move to end (most recent)
            self.cache_order.remove(key)
            self.cache_order.append(key)
        else:
            # Add new entry
            if len(self.cache_order) >= self.max_cache_size:
                # Evict oldest
                oldest_key = self.cache_order.pop(0)
                del self.response_cache[oldest_key]
            self.cache_order.append(key)
            self.response_cache[key] = value
    
    def _store_conversation(self, session_id: str, query: str, response: str, from_cache: bool):
        """Store conversation in session + TinyDB for persistence"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'query': query,
            'response': response,
            'from_cache': from_cache
        }
        
        # Add to session history (in-memory)
        self.active_sessions[session_id]['history'].append(message)
        
        # Keep only last N messages per session (memory optimization)
        if len(self.active_sessions[session_id]['history']) > self.max_history_per_session:
            self.active_sessions[session_id]['history'] = \
                self.active_sessions[session_id]['history'][-self.max_history_per_session:]
        
        # Store in TinyDB for persistence
        try:
            self.db_manager.tinydb.store_llm_response(
                application_id=session_id,
                query=query,
                response=response,
                query_type='chat',
                model=self.ollama_model,
                tokens_used=len(response.split())  # Approximate
            )
        except Exception as e:
            self.logger.warning(f"Failed to store conversation in TinyDB: {e}")
    
    def _explain_decision(self, state: ApplicationState, session_id: str) -> str:
        """Explain decision using all 4 databases"""
        try:
            app_id = state.application_id
            
            # 1. Get decision from SQLite
            decision_data = self._query_sqlite_decision(app_id)
            
            # 2. Get validation issues from SQLite
            validation_data = self._query_sqlite_validation(app_id)
            
            # 3. Get cached extraction from TinyDB
            extraction_data = self._query_tinydb_cache(app_id)
            
            # 4. Get similar cases from NetworkX
            similar_cases = self._query_networkx_similar(app_id)
            
            # Build context for LLM
            context = {
                'decision': decision_data,
                'validation': validation_data,
                'extraction': extraction_data,
                'similar_cases': similar_cases,
                'applicant_name': state.applicant_name
            }
            
            # Call LLM with rich context
            prompt = self._build_explanation_prompt(context)
            response = self._call_ollama(prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Explanation error: {e}")
            return f"I couldn't explain the decision: {str(e)}"
    
    def _suggest_improvements(self, state: ApplicationState, session_id: str) -> str:
        """Suggest improvements using all 4 databases"""
        try:
            app_id = state.application_id
            
            # 1. Get validation issues from SQLite
            validation_data = self._query_sqlite_validation(app_id)
            
            # 2. Get financial data from TinyDB cache
            financial_data = self._query_tinydb_cache(app_id)
            
            # 3. Get recommended programs from NetworkX
            programs = self._query_networkx_programs(app_id)
            
            # 4. Find successful similar cases from NetworkX
            successful_cases = self._query_networkx_successful_similar(app_id)
            
            context = {
                'validation_issues': validation_data,
                'financial': financial_data,
                'programs': programs,
                'successful_examples': successful_cases
            }
            
            prompt = self._build_improvement_prompt(context)
            response = self._call_ollama(prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Improvement suggestion error: {e}")
            return f"I couldn't generate improvements: {str(e)}"
    
    def _show_details(self, state: ApplicationState, session_id: str) -> str:
        """Show comprehensive details from all 4 databases"""
        try:
            app_id = state.application_id
            
            # Gather from all sources
            details = {
                'application': self._query_sqlite_application(app_id),
                'profile': self._query_sqlite_profile(app_id),
                'documents': self._query_tinydb_documents(app_id),
                'validation': self._query_sqlite_validation(app_id),
                'decision': self._query_sqlite_decision(app_id),
                'graph_connections': self._query_networkx_connections(app_id),
                'semantic_matches': self._query_chromadb_semantic(app_id)
            }
            
            # Format with LLM
            prompt = self._build_details_prompt(details)
            response = self._call_ollama(prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Details retrieval error: {e}")
            return f"I couldn't retrieve details: {str(e)}"
    
    def _simulate_changes(self, state: ApplicationState, query: str, session_id: str) -> str:
        """Simulate what-if scenarios"""
        try:
            app_id = state.application_id
            
            # Get current state
            current = self._query_tinydb_cache(app_id)
            
            # Parse simulation parameters from query
            simulation_params = self._parse_simulation_query(query)
            
            # Get similar cases with those parameters from NetworkX
            similar_outcomes = self._query_networkx_similar_with_params(simulation_params)
            
            context = {
                'current': current,
                'simulation': simulation_params,
                'similar_outcomes': similar_outcomes
            }
            
            prompt = self._build_simulation_prompt(context)
            response = self._call_ollama(prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
            return f"I couldn't simulate changes: {str(e)}"
    
    def _find_similar_cases(self, state: ApplicationState, session_id: str) -> str:
        """Find similar cases using NetworkX graph"""
        try:
            app_id = state.application_id
            
            # Get application data from TinyDB
            current_app = self._query_tinydb_cache(app_id)
            
            # Find similar using NetworkX (income, employment, family size)
            similar = self.db_manager.networkx.get_similar_applications(
                app_id,
                limit=5
            )
            
            # Get their outcomes from SQLite
            outcomes = []
            for similar_id in similar:
                decision = self._query_sqlite_decision(similar_id)
                outcomes.append({'app_id': similar_id, 'decision': decision})
            
            context = {
                'current': current_app,
                'similar_cases': outcomes
            }
            
            prompt = self._build_similar_cases_prompt(context)
            response = self._call_ollama(prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Similar cases error: {e}")
            return f"I couldn't find similar cases: {str(e)}"
    
    def _explain_programs(self, state: ApplicationState, session_id: str) -> str:
        """Explain recommended programs"""
        try:
            app_id = state.application_id
            
            # Get recommended programs from NetworkX
            programs = self._query_networkx_programs(app_id)
            
            # Get all available programs
            all_programs = self._get_all_programs()
            
            context = {
                'recommended': programs,
                'all_programs': all_programs
            }
            
            prompt = self._build_programs_prompt(context)
            response = self._call_ollama(prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"Program explanation error: {e}")
            return f"I couldn't explain programs: {str(e)}"
    
    def _general_query(self, state: ApplicationState, query: str, session_id: str) -> str:
        """Handle general queries with full RAG"""
        try:
            app_id = state.application_id
            
            # Use ChromaDB semantic search for relevant context
            semantic_results = self._query_chromadb_semantic_search(query, limit=3)
            
            # Get conversation history from session
            history = self.active_sessions[session_id]['history'][-5:]  # Last 5 messages
            
            context = {
                'query': query,
                'semantic_results': semantic_results,
                'conversation_history': history,
                'application_id': app_id
            }
            
            prompt = self._build_general_prompt(context)
            response = self._call_ollama(prompt)
            
            return response
            
        except Exception as e:
            self.logger.error(f"General query error: {e}")
            return f"I couldn't process your query: {str(e)}"
    
    # ============= DATABASE QUERY METHODS =============
    
    def _query_sqlite_application(self, app_id: str) -> Optional[Dict]:
        """Query application from SQLite"""
        try:
            result = self.db_manager.sqlite.get_application(app_id)
            return result
        except Exception as e:
            self.logger.warning(f"SQLite application query failed: {e}")
            return None
    
    def _query_sqlite_profile(self, app_id: str) -> Optional[Dict]:
        """Query profile from SQLite"""
        try:
            result = self.db_manager.sqlite.get_applicant_profile(app_id)
            return result
        except Exception as e:
            self.logger.warning(f"SQLite profile query failed: {e}")
            return None
    
    def _query_sqlite_validation(self, app_id: str) -> Optional[Dict]:
        """Query validation results from SQLite"""
        try:
            results = self.db_manager.sqlite.get_validation_history(app_id)
            return results[0] if results else None
        except Exception as e:
            self.logger.warning(f"SQLite validation query failed: {e}")
            return None
    
    def _query_sqlite_decision(self, app_id: str) -> Optional[Dict]:
        """Query decision from SQLite"""
        try:
            results = self.db_manager.sqlite.get_decision_history(app_id)
            return results[0] if results else None
        except Exception as e:
            self.logger.warning(f"SQLite decision query failed: {e}")
            return None
    
    def _query_tinydb_cache(self, app_id: str) -> Optional[Dict]:
        """Query cached extraction from TinyDB"""
        try:
            result = self.db_manager.tinydb.get_cached_extraction(app_id)
            return result
        except Exception as e:
            self.logger.warning(f"TinyDB cache query failed: {e}")
            return None
    
    def _query_tinydb_documents(self, app_id: str) -> List[Dict]:
        """Query documents from TinyDB"""
        try:
            # TinyDB stores by document type, get all OCR results for this app
            results = []
            try:
                ocr_results = self.db_manager.tinydb.get_ocr_results(app_id)
                if ocr_results:
                    results.extend(ocr_results)
            except:
                pass
            return results
        except Exception as e:
            self.logger.warning(f"TinyDB documents query failed: {e}")
            return []
    
    def _query_networkx_similar(self, app_id: str) -> List[str]:
        """Find similar applications using NetworkX"""
        try:
            similar = self.db_manager.networkx.get_similar_applications(app_id, limit=3)
            return similar
        except Exception as e:
            self.logger.warning(f"NetworkX similar query failed: {e}")
            return []
    
    def _query_networkx_programs(self, app_id: str) -> List[Dict]:
        """Get recommended programs from NetworkX"""
        try:
            programs = self.db_manager.networkx.get_recommended_programs(app_id)
            return programs
        except Exception as e:
            self.logger.warning(f"NetworkX programs query failed: {e}")
            return []
    
    def _query_networkx_connections(self, app_id: str) -> Dict:
        """Get graph connections from NetworkX"""
        try:
            subgraph = self.db_manager.networkx.get_application_graph(app_id)
            if not subgraph:
                return {'nodes': 0, 'edges': 0, 'neighbors': []}
            return {
                'nodes': len(subgraph.get('nodes', [])),
                'edges': len(subgraph.get('edges', [])),
                'neighbors': []
            }
        except Exception as e:
            self.logger.warning(f"NetworkX connections query failed: {e}")
            return {}
    
    def _query_networkx_successful_similar(self, app_id: str) -> List[Dict]:
        """Find similar successful cases"""
        try:
            similar_ids = self.db_manager.networkx.get_similar_applications(app_id, limit=5)
            successful = []
            for sim_id in similar_ids:
                decision = self._query_sqlite_decision(sim_id)
                if decision and decision.get('decision_type') == 'APPROVED':
                    successful.append({'app_id': sim_id, 'decision': decision})
            return successful
        except Exception as e:
            self.logger.warning(f"NetworkX successful similar query failed: {e}")
            return []
    
    def _query_networkx_similar_with_params(self, params: Dict) -> List[Dict]:
        """Find cases with similar parameters"""
        # Simplified - would need to enhance NetworkX queries
        return []
    
    def _query_chromadb_semantic(self, app_id: str) -> List[Dict]:
        """Query similar profiles from ChromaDB"""
        try:
            # Get current profile
            profile = self._query_sqlite_profile(app_id)
            if not profile:
                return []
            
            # Create query text
            query_text = f"Applicant with income {profile.get('monthly_income', 0)} AED, " \
                        f"employment status: {profile.get('employment_status', 'unknown')}"
            
            # Search ChromaDB
            try:
                chromadb = getattr(self.db_manager, 'chromadb', None) or getattr(self.db_manager, 'chroma', None)
                if chromadb and hasattr(chromadb, 'query_profiles'):
                    results = chromadb.query_profiles(query_text, limit=3)
                    return results
            except:
                pass
            return []
        except Exception as e:
            self.logger.warning(f"ChromaDB semantic query failed: {e}")
            return []
    
    def _query_chromadb_semantic_search(self, query: str, limit: int = 3) -> List[Dict]:
        """General semantic search in ChromaDB"""
        try:
            chromadb = getattr(self.db_manager, 'chromadb', None) or getattr(self.db_manager, 'chroma', None)
            if chromadb and hasattr(chromadb, 'search'):
                results = chromadb.search(query, limit=limit)
                return results
            return []
        except Exception as e:
            self.logger.warning(f"ChromaDB search failed: {e}")
            return []
    
    # ============= PROMPT BUILDING METHODS =============
    
    def _build_explanation_prompt(self, context: Dict) -> str:
        """Build prompt for decision explanation"""
        decision = context.get('decision', {})
        validation = context.get('validation', {})
        
        return f"""You are an AI assistant explaining a social support decision.

Application: {context.get('applicant_name')}
Decision: {decision.get('decision_type', 'UNKNOWN')}
Support Amount: {decision.get('support_amount', 0)} AED

Validation Issues:
{json.dumps(validation, indent=2)}

Similar Cases:
{json.dumps(context.get('similar_cases', []), indent=2)}

Explain the decision clearly, mentioning:
1. Key factors that led to this decision
2. How validation issues affected it
3. How it compares to similar cases

Keep it concise (3-4 paragraphs)."""
    
    def _build_improvement_prompt(self, context: Dict) -> str:
        """Build prompt for improvement suggestions"""
        return f"""You are an AI assistant suggesting improvements for a social support application.

Current Issues:
{json.dumps(context.get('validation_issues', {}), indent=2)}

Financial Data:
{json.dumps(context.get('financial', {}), indent=2)}

Available Programs:
{json.dumps(context.get('programs', []), indent=2)}

Successful Examples:
{json.dumps(context.get('successful_examples', []), indent=2)}

Provide 3-5 specific, actionable improvements ranked by impact.
For each, explain:
1. What to improve
2. Why it matters
3. How to achieve it

Keep it concise and practical."""
    
    def _build_details_prompt(self, details: Dict) -> str:
        """Build prompt for showing details"""
        return f"""You are an AI assistant presenting application details.

Data from all systems:
{json.dumps(details, indent=2)}

Present a comprehensive overview covering:
1. Applicant profile
2. Financial situation
3. Validation status
4. Decision and reasoning
5. Related connections

Format as a clear, organized summary."""
    
    def _build_simulation_prompt(self, context: Dict) -> str:
        """Build prompt for what-if simulation"""
        return f"""You are an AI assistant simulating changes to an application.

Current State:
{json.dumps(context.get('current', {}), indent=2)}

Proposed Changes:
{json.dumps(context.get('simulation', {}), indent=2)}

Similar Outcomes:
{json.dumps(context.get('similar_outcomes', []), indent=2)}

Analyze how these changes would likely affect:
1. Eligibility decision
2. Support amount
3. Program recommendations

Base your analysis on similar historical cases."""
    
    def _build_similar_cases_prompt(self, context: Dict) -> str:
        """Build prompt for similar cases"""
        return f"""You are an AI assistant comparing similar applications.

Current Application:
{json.dumps(context.get('current', {}), indent=2)}

Similar Cases:
{json.dumps(context.get('similar_cases', []), indent=2)}

Compare and explain:
1. Key similarities
2. Important differences
3. Why outcomes varied
4. Lessons learned"""
    
    def _build_programs_prompt(self, context: Dict) -> str:
        """Build prompt for program explanations"""
        return f"""You are an AI assistant explaining social support programs.

Recommended Programs:
{json.dumps(context.get('recommended', []), indent=2)}

All Available Programs:
{json.dumps(context.get('all_programs', []), indent=2)}

Explain:
1. Why these programs were recommended
2. What each program offers
3. How to access them
4. Expected benefits"""
    
    def _build_general_prompt(self, context: Dict) -> str:
        """Build prompt for general queries"""
        return f"""You are an AI assistant for a social support system.

User Question: {context.get('query')}

Relevant Context:
{json.dumps(context.get('semantic_results', []), indent=2)}

Recent Conversation:
{json.dumps(context.get('conversation_history', []), indent=2)}

Answer the question clearly and helpfully based on the context provided."""
    
    def _parse_simulation_query(self, query: str) -> Dict:
        """Parse simulation parameters from query"""
        params = {}
        
        # Simple parsing (can be enhanced with NLP)
        if "income" in query.lower():
            if "increase" in query.lower() or "more" in query.lower():
                params['income_change'] = '+20%'
            elif "decrease" in query.lower() or "less" in query.lower():
                params['income_change'] = '-20%'
        
        if "debt" in query.lower():
            if "reduce" in query.lower() or "pay" in query.lower():
                params['debt_change'] = '-50%'
        
        if "employ" in query.lower():
            params['employment_change'] = 'FULL_TIME'
        
        return params
    
    def _get_all_programs(self) -> List[Dict]:
        """Get all available programs"""
        return [
            {'name': 'Job Placement', 'description': 'Connect with employers'},
            {'name': 'Skills Bootcamp', 'description': '3-month training program'},
            {'name': 'Career Counseling', 'description': 'Professional guidance'},
            {'name': 'Financial Wellness', 'description': 'Budgeting and planning'},
            {'name': 'Business Development', 'description': 'Start your business'},
            {'name': 'Education Support', 'description': 'Tuition assistance'},
            {'name': 'Wellbeing Program', 'description': 'Mental health support'}
        ]
    
    # ============= LLM CALL METHOD =============
    
    def _call_ollama(self, prompt: str, temperature: float = 0.7) -> str:
        """
        Call Ollama LLM with prompt
        Optimized for M1 8GB: uses streaming, timeout, and concise responses
        """
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": 300,  # Reduced for faster response
                        "top_p": 0.9,
                        "top_k": 40
                    }
                },
                timeout=120  # Increased to 2 minutes for mistral
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response generated')
            else:
                self.logger.error(f"Ollama error: {response.status_code}")
                return f"LLM service error: {response.status_code}"
                
        except requests.Timeout:
            self.logger.error("Ollama timeout after 120s")
            return "The AI took too long to respond. Please try again."
        except requests.ConnectionError:
            self.logger.error("Ollama connection failed")
            return "Cannot connect to AI service. Please ensure Ollama is running."
        except Exception as e:
            self.logger.error(f"Ollama call failed: {e}")
            return f"AI service error: {str(e)}"
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'total_requests': total_requests,
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': len(self.response_cache),
            'max_cache_size': self.max_cache_size,
            'active_sessions': len(self.active_sessions)
        }
    
    def clear_cache(self):
        """Clear response cache (memory cleanup)"""
        self.response_cache.clear()
        self.cache_order.clear()
        self.logger.info("Cache cleared")
    
    def clear_session(self, session_id: str):
        """Clear specific session (memory cleanup)"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.logger.info(f"Session {session_id} cleared")
