"""
Master Orchestrator Agent
Coordinates all sub-agents in the correct sequence
"""
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.base_agent import BaseAgent
from ..core.types import ApplicationState, ProcessingStage, AgentMessage


class MasterOrchestrator(BaseAgent):
    """
    Master Orchestrator coordinates the entire application processing pipeline
    
    Flow:
    1. Upload Documents
    2. Data Extraction Agent (OCR, Resume, Excel)
    3. Data Validation Agent (Cross-doc checks, conflicts)
    4. Eligibility Agent (ML + Rules)
    5. Recommendation Agent (LLM reasoning)
    6. Explanation Agent (Natural language justification)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("MasterOrchestrator", config)
        self.logger = logging.getLogger("MasterOrchestrator")
        
        # Agents will be injected
        self.extraction_agent = None
        self.validation_agent = None
        self.eligibility_agent = None
        self.recommendation_agent = None
        self.explanation_agent = None
        self.rag_chatbot_agent = None  # NEW: RAG-powered chatbot
        
        # State management
        self.applications: Dict[str, ApplicationState] = {}
        
    def register_agents(self, 
                       extraction_agent,
                       validation_agent,
                       eligibility_agent,
                       recommendation_agent,
                       explanation_agent,
                       rag_chatbot_agent=None):  # NEW: Optional RAG chatbot
        """Register all sub-agents"""
        self.extraction_agent = extraction_agent
        self.validation_agent = validation_agent
        self.eligibility_agent = eligibility_agent
        self.recommendation_agent = recommendation_agent
        self.explanation_agent = explanation_agent
        self.rag_chatbot_agent = rag_chatbot_agent
        self.logger.info("All agents registered")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestration - not used directly, use process_application instead"""
        pass
    
    async def process_application(self, application_id: str) -> ApplicationState:
        """
        Process a complete application through the pipeline
        
        Args:
            application_id: Application ID to process
            
        Returns:
            Final ApplicationState with all results
        """
        start_time = datetime.now()
        
        if application_id not in self.applications:
            raise ValueError(f"Application {application_id} not found")
        
        app_state = self.applications[application_id]
        self.logger.info(f"Starting processing for application {application_id}")
        
        try:
            # Stage 1: Data Extraction
            app_state = await self._run_extraction(app_state)
            
            # Stage 2: Data Validation
            app_state = await self._run_validation(app_state)
            
            # Stage 3: Eligibility Check
            app_state = await self._run_eligibility(app_state)
            
            # Stage 4: Recommendation Generation
            app_state = await self._run_recommendation(app_state)
            
            # Stage 5: Explanation Generation
            app_state = await self._run_explanation(app_state)
            
            # Complete
            app_state.update_stage(ProcessingStage.COMPLETED)
            
            duration = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"Application {application_id} completed in {duration:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Error processing application {application_id}: {str(e)}")
            app_state.add_error(str(e))
        
        return app_state
    
    async def _run_extraction(self, app_state: ApplicationState) -> ApplicationState:
        """Run Data Extraction Agent"""
        self.logger.info(f"[{app_state.application_id}] Running Data Extraction")
        app_state.update_stage(ProcessingStage.EXTRACTING)
        
        # DEBUG: Log documents being passed to extraction
        self.logger.info(f"[{app_state.application_id}] DEBUG - Documents to extract: {len(app_state.documents)}")
        for doc in app_state.documents:
            self.logger.info(f"[{app_state.application_id}] DEBUG - Doc type: {doc.document_type}, path: {doc.file_path}")
        
        input_data = {
            "application_id": app_state.application_id,
            "documents": [doc.__dict__ for doc in app_state.documents]
        }
        
        result = await self.extraction_agent.execute(input_data)
        app_state.extracted_data = result["extracted_data"]
        
        # DEBUG: Log what was extracted
        self.logger.info(f"[{app_state.application_id}] DEBUG - Extracted credit_score: {app_state.extracted_data.credit_data.get('credit_score')}")
        self.logger.info(f"[{app_state.application_id}] DEBUG - Extracted company_name: {app_state.extracted_data.employment_data.get('company_name')}")
        
        self.logger.info(f"[{app_state.application_id}] Extraction complete")
        return app_state
    
    async def _run_validation(self, app_state: ApplicationState) -> ApplicationState:
        """Run Data Validation Agent"""
        self.logger.info(f"[{app_state.application_id}] Running Data Validation")
        app_state.update_stage(ProcessingStage.VALIDATING)
        
        input_data = {
            "application_id": app_state.application_id,
            "extracted_data": app_state.extracted_data,
            "applicant_name": getattr(app_state, 'applicant_name', None)  # Pass applicant name for identity verification
        }
        
        result = await self.validation_agent.execute(input_data)
        app_state.validation_report = result["validation_report"]
        
        # Check if validation passed
        if not app_state.validation_report.is_valid:
            critical_issues = [i for i in app_state.validation_report.issues if i.severity == "critical"]
            if critical_issues:
                # Log critical issues
                for issue in critical_issues:
                    self.logger.error(f"[{app_state.application_id}] CRITICAL: {issue.message}")
                raise ValueError(f"Critical validation issues found: {len(critical_issues)} issues")
        
        self.logger.info(f"[{app_state.application_id}] Validation complete")
        return app_state
        return app_state
    
    async def _run_eligibility(self, app_state: ApplicationState) -> ApplicationState:
        """Run Eligibility Agent (ML + Rules)"""
        self.logger.info(f"[{app_state.application_id}] Running Eligibility Check")
        app_state.update_stage(ProcessingStage.CHECKING_ELIGIBILITY)
        
        input_data = {
            "application_id": app_state.application_id,
            "extracted_data": app_state.extracted_data,
            "validation_report": app_state.validation_report
        }
        
        result = await self.eligibility_agent.execute(input_data)
        app_state.eligibility_result = result["eligibility_result"]
        
        self.logger.info(f"[{app_state.application_id}] Eligibility check complete - Score: {app_state.eligibility_result.eligibility_score:.2f}")
        return app_state
    
    async def _run_recommendation(self, app_state: ApplicationState) -> ApplicationState:
        """Run Recommendation Agent (LLM)"""
        self.logger.info(f"[{app_state.application_id}] Generating Recommendations")
        app_state.update_stage(ProcessingStage.GENERATING_RECOMMENDATION)
        
        input_data = {
            "application_id": app_state.application_id,
            "extracted_data": app_state.extracted_data,
            "eligibility_result": app_state.eligibility_result
        }
        
        result = await self.recommendation_agent.execute(input_data)
        app_state.recommendation = result["recommendation"]
        
        self.logger.info(f"[{app_state.application_id}] Recommendation generated: {app_state.recommendation.decision.value}")
        return app_state
    
    async def _run_explanation(self, app_state: ApplicationState) -> ApplicationState:
        """Run Explanation Agent"""
        self.logger.info(f"[{app_state.application_id}] Generating Explanation")
        
        input_data = {
            "application_id": app_state.application_id,
            "extracted_data": app_state.extracted_data,
            "eligibility_result": app_state.eligibility_result,
            "recommendation": app_state.recommendation
        }
        
        result = await self.explanation_agent.execute(input_data)
        app_state.explanation = result["explanation"]
        
        self.logger.info(f"[{app_state.application_id}] Explanation generated")
        return app_state
    
    def create_application(self, application_id: str) -> ApplicationState:
        """Create a new application"""
        app_state = ApplicationState(application_id=application_id)
        self.applications[application_id] = app_state
        self.logger.info(f"Created application {application_id}")
        return app_state
    
    def get_application(self, application_id: str) -> Optional[ApplicationState]:
        """Get application by ID"""
        return self.applications.get(application_id)
    
    def add_document(self, application_id: str, document) -> ApplicationState:
        """Add a document to an application"""
        if application_id not in self.applications:
            raise ValueError(f"Application {application_id} not found")
        
        app_state = self.applications[application_id]
        app_state.documents.append(document)
        self.logger.info(f"Added document {document.document_type} to application {application_id}")
        return app_state
    
    async def handle_chat_query(self, application_id: str, query: str, query_type: str) -> Dict[str, Any]:
        """
        Handle chatbot queries using RAG-powered chatbot agent
        
        CRITICAL FIX: Allow chatbot at ANY stage - RAG engine handles status appropriately
        
        Query types:
        - explanation: Why was this decision made?
        - improvement: How can I improve?
        - details: Show all details
        - simulation: What if X changes?
        - general: Any other question
        """
        app_state = self.get_application(application_id)
        
        if not app_state:
            return {"error": "Application not found"}
        
        # REMOVED CHECK - Allow chatbot at any stage
        # The RAG engine will detect unprocessed apps and guide users appropriately
        
        self.logger.info(f"[{application_id}] RAG Chat query: {query_type} (stage: {app_state.stage.value})")
        
        # Use RAG chatbot if available, fallback to explanation agent
        if self.rag_chatbot_agent:
            chat_input = {
                "application_id": application_id,
                "query": query,
                "query_type": query_type,
                "app_state": app_state
            }
            
            result = await self.rag_chatbot_agent.execute(chat_input)
        else:
            # Fallback to old explanation agent
            chat_input = {
                "application_id": application_id,
                "query": query,
                "query_type": query_type,
                "extracted_data": app_state.extracted_data,
                "validation_report": app_state.validation_report,
                "eligibility_result": app_state.eligibility_result,
                "recommendation": app_state.recommendation,
                "current_explanation": app_state.explanation
            }
            
            result = await self.explanation_agent.handle_chat_query(chat_input)
        
        # Add to chat history
        app_state.chat_history.append({
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "query_type": query_type,
            "response": result
        })
        
        return result
    
    def get_status(self, application_id: str) -> Dict[str, Any]:
        """Get current status of an application"""
        app_state = self.get_application(application_id)
        
        if not app_state:
            return {"error": "Application not found"}
        
        return {
            "application_id": application_id,
            "stage": app_state.stage.value,
            "documents_count": len(app_state.documents),
            "has_extracted_data": app_state.extracted_data is not None,
            "has_validation": app_state.validation_report is not None,
            "has_eligibility": app_state.eligibility_result is not None,
            "has_recommendation": app_state.recommendation is not None,
            "has_explanation": app_state.explanation is not None,
            "chatbot_enabled": app_state.is_chatbot_enabled(),
            "errors": app_state.errors,
            "created_at": app_state.created_at.isoformat(),
            "updated_at": app_state.updated_at.isoformat()
        }
