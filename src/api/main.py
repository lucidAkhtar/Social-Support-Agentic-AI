"""
FastAPI Backend for Social Support System.
Provides REST API endpoints for all agent operations.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import asyncio
import logging
from pathlib import Path
import shutil
import uuid

from src.core.orchestrator import MasterOrchestrator
from src.core.types import ApplicationState, ProcessingStage
from src.databases import UnifiedDatabaseManager
from src.agents.extraction_agent import DataExtractionAgent
from src.agents.validation_agent import DataValidationAgent
from src.agents.eligibility_agent import EligibilityAgent
from src.agents.recommendation_agent import RecommendationAgent
from src.agents.explanation_agent import ExplanationAgent
from src.agents.rag_chatbot_agent import RAGChatbotAgent  # NEW: RAG chatbot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Social Support System API",
    description="Multi-agent system for social support eligibility assessment",
    version="1.0.0"
)

# CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator and database
orchestrator = MasterOrchestrator()
db_manager = UnifiedDatabaseManager(use_neo4j_mock=True)

# Initialize and register all agents
extraction_agent = DataExtractionAgent()
validation_agent = DataValidationAgent()
eligibility_agent = EligibilityAgent()
recommendation_agent = RecommendationAgent()
explanation_agent = ExplanationAgent()
rag_chatbot_agent = RAGChatbotAgent({
    'db_path': 'data/databases/applications.db',
    'ollama_url': 'http://localhost:11434',
    'ollama_model': 'mistral:latest'
})  # NEW: RAG-powered chatbot

orchestrator.register_agents(
    extraction_agent=extraction_agent,
    validation_agent=validation_agent,
    eligibility_agent=eligibility_agent,
    recommendation_agent=recommendation_agent,
    explanation_agent=explanation_agent,
    rag_chatbot_agent=rag_chatbot_agent  # NEW: Register RAG chatbot
)
logger.info("All agents initialized and registered with orchestrator (including RAG chatbot)")

# In-memory state storage (in production, use Redis or similar)
active_applications: Dict[str, ApplicationState] = {}


# ========== Request/Response Models ==========

class ChatQuery(BaseModel):
    application_id: str
    query: str
    query_type: Optional[str] = "explanation"


class SimulationQuery(BaseModel):
    application_id: str
    changes: Dict[str, Any]


class ApplicationResponse(BaseModel):
    application_id: str
    status: str
    current_stage: str
    message: str


class ProcessingStatusResponse(BaseModel):
    application_id: str
    current_stage: str
    progress_percentage: int
    message: str
    data: Optional[Dict[str, Any]] = None


# ========== API Endpoints ==========

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Social Support System API",
        "version": "1.0.0"
    }


@app.post("/api/applications/create", response_model=ApplicationResponse)
async def create_application(applicant_name: str = Form(...)):
    """Create a new application."""
    try:
        application_id = f"APP_{uuid.uuid4().hex[:8].upper()}"
        
        # Create in database
        success = db_manager.create_application(application_id, applicant_name)
        
        if not success:
            raise HTTPException(status_code=400, detail="Application already exists")
        
        # Create state
        state = ApplicationState(
            application_id=application_id,
            applicant_name=applicant_name.strip(),
            stage=ProcessingStage.PENDING
        )
        active_applications[application_id] = state
        
        logger.info(f"Created application {application_id} for {applicant_name}")
        
        return ApplicationResponse(
            application_id=application_id,
            status="created",
            current_stage=state.stage.value,
            message=f"Application created successfully for {applicant_name}"
        )
    
    except Exception as e:
        logger.error(f"Error creating application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{application_id}/upload")
async def upload_documents(
    application_id: str,
    documents: List[UploadFile] = File(...)
):
    """Upload documents for an application."""
    try:
        if application_id not in active_applications:
            raise HTTPException(status_code=404, detail="Application not found")
        
        state = active_applications[application_id]
        upload_dir = Path(f"data/uploads/{application_id}")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        uploaded_files = []
        
        for file in documents:
            # Save file
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Determine document type from filename
            filename_lower = file.filename.lower()
            if "emirates" in filename_lower or "id" in filename_lower:
                doc_type = "emirates_id"
            elif "resume" in filename_lower or "cv" in filename_lower:
                doc_type = "resume"
            elif "bank" in filename_lower or "statement" in filename_lower:
                doc_type = "bank_statement"
            elif "utility" in filename_lower or "bill" in filename_lower:
                doc_type = "utility_bill"
            elif "asset" in filename_lower or "liab" in filename_lower:
                doc_type = "assets_liabilities"
            else:
                doc_type = "other"
            
            # Add to state
            from src.core.types import Document
            doc = Document(
                document_id=f"DOC_{uuid.uuid4().hex[:8].upper()}",
                document_type=doc_type,
                filename=file.filename,
                file_path=str(file_path)
            )
            state.documents.append(doc)
            
            # Save to database
            db_manager.add_document(
                application_id,
                doc.document_id,
                doc_type,
                str(file_path)
            )
            
            uploaded_files.append({
                "filename": file.filename,
                "document_type": doc_type,
                "document_id": doc.document_id
            })
        
        db_manager.log_action(
            application_id, "System", "documents_uploaded",
            {"count": len(documents), "files": uploaded_files}
        )
        
        logger.info(f"Uploaded {len(documents)} documents for {application_id}")
        
        return {
            "application_id": application_id,
            "uploaded_count": len(documents),
            "documents": uploaded_files,
            "message": f"Successfully uploaded {len(documents)} document(s)"
        }
    
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{application_id}/process", response_model=ProcessingStatusResponse)
async def process_application(application_id: str):
    """Process application through all agents."""
    try:
        if application_id not in active_applications:
            raise HTTPException(status_code=404, detail="Application not found")
        
        state = active_applications[application_id]
        
        # Register application with orchestrator if not already registered
        if application_id not in orchestrator.applications:
            orchestrator.applications[application_id] = state
        
        # Process through orchestrator
        final_state = await orchestrator.process_application(application_id)
        
        # Save all results to database
        if final_state.extracted_data:
            profile_data = {
                "id_number": final_state.extracted_data.applicant_info.get("id_number"),
                "monthly_income": final_state.extracted_data.income_data.get("monthly_income", 0),
                "monthly_expenses": final_state.extracted_data.income_data.get("monthly_expenses", 0),
                "employment_status": final_state.extracted_data.employment_data.get("employment_status", "unknown"),
                "years_experience": final_state.extracted_data.employment_data.get("years_experience", 0),
                "total_assets": final_state.extracted_data.assets_liabilities.get("total_assets", 0),
                "total_liabilities": final_state.extracted_data.assets_liabilities.get("total_liabilities", 0),
                "net_worth": final_state.extracted_data.assets_liabilities.get("net_worth", 0),
                "credit_score": final_state.extracted_data.credit_data.get("credit_score", 0),
                "family_size": final_state.extracted_data.family_info.get("family_size", 1),
            }
            db_manager.save_applicant_profile(application_id, profile_data)
        
        if final_state.validation_report:
            validation_data = {
                "is_valid": final_state.validation_report.is_valid,
                "completeness_score": final_state.validation_report.data_completeness_score,
                "confidence_score": final_state.validation_report.confidence_score,
                "issues": [{"field": i.field, "severity": i.severity, "message": i.message} 
                          for i in final_state.validation_report.issues]
            }
            db_manager.save_validation_result(application_id, validation_data)
        
        if final_state.eligibility_result:
            decision_data = {
                "is_eligible": final_state.eligibility_result.is_eligible,
                "eligibility_score": final_state.eligibility_result.eligibility_score,
                "ml_prediction": final_state.eligibility_result.ml_prediction,
                "policy_rules_met": final_state.eligibility_result.policy_rules_met,
                "final_decision": final_state.recommendation.decision.value if final_state.recommendation else "DECLINED",
                "reasons": final_state.eligibility_result.reasoning
            }
            db_manager.save_eligibility_decision(application_id, decision_data)
        
        if final_state.recommendation:
            recommendation_data = {
                "decision_type": final_state.recommendation.decision.value,
                "financial_support_amount": final_state.recommendation.financial_support_amount,
                "financial_support_type": final_state.recommendation.financial_support_type,
                "programs": final_state.recommendation.economic_enablement_programs,
                "reasoning": final_state.recommendation.reasoning
            }
            db_manager.save_recommendation(application_id, recommendation_data)
        
        # Update state
        active_applications[application_id] = final_state
        db_manager.update_application_stage(application_id, final_state.stage.value)
        
        # Prepare response
        progress = 100 if final_state.stage == ProcessingStage.COMPLETED else 50
        
        return ProcessingStatusResponse(
            application_id=application_id,
            current_stage=final_state.stage.value,
            progress_percentage=progress,
            message="Application processing completed",
            data={
                "extracted_data": final_state.extracted_data is not None,
                "validation_valid": final_state.validation_report.is_valid if final_state.validation_report else False,
                "eligibility_score": final_state.eligibility_result.eligibility_score if final_state.eligibility_result else 0,
                "decision": final_state.recommendation.decision.value if final_state.recommendation else "PENDING"
            }
        )
    
    except Exception as e:
        logger.error(f"Error processing application: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{application_id}/status", response_model=ProcessingStatusResponse)
async def get_application_status(application_id: str):
    """Get current status of an application."""
    try:
        if application_id not in active_applications:
            # Try to load from database
            app_data = db_manager.sqlite.get_application(application_id)
            if not app_data:
                raise HTTPException(status_code=404, detail="Application not found")
            
            return ProcessingStatusResponse(
                application_id=application_id,
                current_stage=app_data['current_stage'],
                progress_percentage=0,
                message="Application found in database",
                data=app_data
            )
        
        state = active_applications[application_id]
        
        stage_progress = {
            ProcessingStage.PENDING: 0,
            ProcessingStage.EXTRACTING: 20,
            ProcessingStage.VALIDATING: 40,
            ProcessingStage.CHECKING_ELIGIBILITY: 60,
            ProcessingStage.GENERATING_RECOMMENDATION: 80,
            ProcessingStage.COMPLETED: 100,
            ProcessingStage.FAILED: 0
        }
        
        return ProcessingStatusResponse(
            application_id=application_id,
            current_stage=state.stage.value,
            progress_percentage=stage_progress.get(state.stage, 0),
            message=f"Application is in {state.stage.value} stage",
            data={
                "documents_count": len(state.documents),
                "has_extracted_data": state.extracted_data is not None,
                "has_validation": state.validation_report is not None,
                "has_eligibility": state.eligibility_result is not None,
                "has_recommendation": state.recommendation is not None
            }
        )
    
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/{application_id}/results")
async def get_application_results(application_id: str):
    """Get complete results for an application."""
    try:
        if application_id not in active_applications:
            raise HTTPException(status_code=404, detail="Application not found")
        
        state = active_applications[application_id]
        
        # Get complete data from database
        full_data = db_manager.get_application_full_data(application_id)
        
        return {
            "application_id": application_id,
            "current_stage": state.stage.value,
            "extracted_data": {
                "applicant_info": state.extracted_data.applicant_info,
                "income_data": state.extracted_data.income_data,
                "employment_data": state.extracted_data.employment_data,
                "assets_liabilities": state.extracted_data.assets_liabilities,
                "credit_data": state.extracted_data.credit_data,
                "family_info": state.extracted_data.family_info,
            } if state.extracted_data else None,
            "validation": {
                "is_valid": state.validation_report.is_valid,
                "completeness_score": state.validation_report.data_completeness_score,
                "confidence_score": state.validation_report.confidence_score,
                "issues": [{"field": i.field, "severity": i.severity, "message": i.message}
                          for i in state.validation_report.issues]
            } if state.validation_report else None,
            "eligibility": {
                "is_eligible": state.eligibility_result.is_eligible,
                "eligibility_score": state.eligibility_result.eligibility_score,
                "ml_prediction": state.eligibility_result.ml_prediction,
                "policy_rules_met": state.eligibility_result.policy_rules_met,
                "reasoning": state.eligibility_result.reasoning
            } if state.eligibility_result else None,
            "recommendation": {
                "decision": state.recommendation.decision.value,
                "support_amount": state.recommendation.financial_support_amount,
                "support_type": state.recommendation.financial_support_type,
                "programs": state.recommendation.economic_enablement_programs,
                "reasoning": state.recommendation.reasoning,
                "key_factors": state.recommendation.key_factors
            } if state.recommendation else None,
            "explanation": {
                "summary": state.explanation.summary,
                "detailed_reasoning": state.explanation.detailed_reasoning,
                "factors_analysis": state.explanation.factors_analysis
            } if state.explanation else None,
            "database_data": full_data
        }
    
    except Exception as e:
        logger.error(f"Error getting results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{application_id}/chat")
async def chat_with_agent(chat_query: ChatQuery):
    """Chat with the explanation agent."""
    try:
        application_id = chat_query.application_id
        
        if application_id not in active_applications:
            raise HTTPException(status_code=404, detail="Application not found")
        
        state = active_applications[application_id]
        
        # Check if chatbot is enabled (validation must be complete)
        if not state.is_chatbot_enabled():
            return {
                "application_id": application_id,
                "response": f"The chatbot will be available after processing completes. Current stage: {state.stage.value}. Please complete document upload and click 'Process Application'.",
                "chatbot_enabled": False,
                "current_stage": state.stage.value
            }
        
        # Handle chat query via orchestrator
        response = await orchestrator.handle_chat_query(
            application_id, chat_query.query, chat_query.query_type
        )
        
        # Extract response text
        response_text = response if isinstance(response, str) else response.get("response", str(response))
        
        # Save to database for RAG context
        from datetime import datetime
        db_manager.add_chat_message(
            application_id, "user", chat_query.query, datetime.now().isoformat()
        )
        db_manager.add_chat_message(
            application_id, "assistant", response_text, datetime.now().isoformat()
        )
        
        return {
            "application_id": application_id,
            "query": chat_query.query,
            "response": response_text,
            "chatbot_enabled": True
        }
    
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/applications/{application_id}/simulate")
async def simulate_changes(simulation: SimulationQuery):
    """Simulate what-if scenarios."""
    try:
        application_id = simulation.application_id
        
        if application_id not in active_applications:
            raise HTTPException(status_code=404, detail="Application not found")
        
        state = active_applications[application_id]
        
        query = f"What if: {', '.join([f'{k}={v}' for k, v in simulation.changes.items()])}"
        response = await orchestrator.handle_chat_query(state, query, "simulation")
        
        return {
            "application_id": application_id,
            "changes": simulation.changes,
            "simulation_result": response
        }
    
    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics")
async def get_statistics():
    """Get system statistics."""
    try:
        stats = db_manager.get_system_statistics()
        return {
            "total_applications": stats["total_applications"],
            "sqlite_stats": stats["sqlite"],
            "chromadb_stats": stats["chromadb"],
            "active_applications": len(active_applications)
        }
    
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
