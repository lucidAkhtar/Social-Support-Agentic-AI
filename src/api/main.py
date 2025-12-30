"""
FastAPI service for social support application processing
Endpoints for application submission, processing, decision retrieval, and recommendations
Integrates LangGraph orchestration + Langfuse observability
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import json
from pathlib import Path
import asyncio

# Import orchestration and observability
try:
    from src.orchestration.langgraph_orchestrator import LangGraphOrchestrator, ApplicationProcessingState
    LANGGRAPH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: LangGraph orchestration not available: {e}")
    LANGGRAPH_AVAILABLE = False
    LangGraphOrchestrator = None
    ApplicationProcessingState = None

try:
    from src.observability.langfuse_tracker import ObservabilityIntegration, LangfuseTracker
    LANGFUSE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Langfuse observability not available: {e}")
    LANGFUSE_AVAILABLE = False
    ObservabilityIntegration = None
    LangfuseTracker = None

try:
    from src.database.database_manager import DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError as e:
    DATABASE_AVAILABLE = False
    DatabaseManager = None


# Pydantic models for API contracts
class ApplicantInfo(BaseModel):
    """Applicant personal information"""
    full_name: str = Field(..., description="Full name of applicant")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    date_of_birth: str = Field(..., description="Date of birth (YYYY-MM-DD)")
    nationality: str = Field(..., description="Nationality/Emirates ID")
    marital_status: str = Field(..., description="Single, Married, Divorced, Widowed")
    address: str = Field(..., description="Current residential address")


class IncomeInfo(BaseModel):
    """Income information"""
    total_monthly: float = Field(..., description="Total monthly income")
    employment_type: str = Field(..., description="Employed, Self-employed, Unemployed")
    employer: Optional[str] = Field(None, description="Employer name")
    years_employed: Optional[float] = Field(None, description="Years in current employment")


class FamilyMember(BaseModel):
    """Family member information"""
    name: str
    relationship: str
    age: int
    employment_status: Optional[str] = None


class AssetInfo(BaseModel):
    """Asset information"""
    real_estate: Optional[float] = Field(0, description="Real estate value")
    vehicles: Optional[float] = Field(0, description="Vehicle value")
    savings: Optional[float] = Field(0, description="Savings/bank balance")
    investments: Optional[float] = Field(0, description="Investment portfolio value")
    
    def total(self) -> float:
        return (self.real_estate or 0) + (self.vehicles or 0) + (self.savings or 0) + (self.investments or 0)


class LiabilityInfo(BaseModel):
    """Liability information"""
    mortgage: Optional[float] = Field(0, description="Mortgage balance")
    car_loan: Optional[float] = Field(0, description="Car loan balance")
    credit_debt: Optional[float] = Field(0, description="Credit card debt")
    other_debt: Optional[float] = Field(0, description="Other debt")
    
    def total(self) -> float:
        return (self.mortgage or 0) + (self.car_loan or 0) + (self.credit_debt or 0) + (self.other_debt or 0)


class ApplicationSubmission(BaseModel):
    """Complete application submission"""
    applicant_info: ApplicantInfo = Field(..., description="Applicant personal info")
    income: IncomeInfo = Field(..., description="Income information")
    family_members: List[FamilyMember] = Field(default_factory=list, description="Dependents")
    assets: AssetInfo = Field(default_factory=AssetInfo, description="Assets owned")
    liabilities: LiabilityInfo = Field(default_factory=LiabilityInfo, description="Debts/liabilities")
    documents: Dict[str, str] = Field(default_factory=dict, description="Document references (PDF paths)")
    notes: Optional[str] = Field(None, description="Additional notes")


class ApplicationResponse(BaseModel):
    """Response for submitted application"""
    application_id: str = Field(..., description="Unique application ID")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    submitted_at: str = Field(..., description="Submission timestamp")


class DecisionResult(BaseModel):
    """Decision and recommendations"""
    application_id: str
    decision: str
    confidence: float
    reasoning: List[str]
    recommendations: List[Dict[str, Any]]
    processing_time: float
    processed_at: str


class ProcessingStatus(BaseModel):
    """Processing status information"""
    application_id: str
    status: str
    current_stage: str
    progress_percentage: float
    processing_times: Dict[str, float]
    error_count: int
    last_updated: str


# Initialize FastAPI app
app = FastAPI(
    title="Social Support Application API",
    description="AI-powered application processing for government social support programs",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
orchestrator: Optional[LangGraphOrchestrator] = None
tracker: Optional[LangfuseTracker] = None
db: Optional[DatabaseManager] = None

# Store processing state
applications_in_process: Dict[str, ApplicationProcessingState] = {}
processing_results: Dict[str, Dict[str, Any]] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize orchestrator, database, and observability on startup"""
    global orchestrator, tracker, db
    
    try:
        # Initialize database
        db = DatabaseManager()
        print("✓ DatabaseManager initialized")
        
        # Initialize LangGraph orchestrator
        orchestrator = LangGraphOrchestrator(database_manager=db)
        print("✓ LangGraphOrchestrator initialized")
        
        # Initialize Langfuse tracker
        tracker = ObservabilityIntegration.initialize()
        print("✓ Langfuse tracker initialized")
        
    except Exception as e:
        print(f"⚠ Startup error: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        if tracker:
            tracker.flush()
        if db:
            db.close()
        print("✓ Cleanup completed")
    except Exception as e:
        print(f"⚠ Shutdown error: {e}")


# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "orchestrator": orchestrator is not None,
            "database": db is not None,
            "tracker": tracker is not None
        }
    }


@app.post("/applications/submit", response_model=ApplicationResponse, tags=["Applications"])
async def submit_application(application: ApplicationSubmission, 
                            background_tasks: BackgroundTasks):
    """
    Submit a social support application.
    
    The application will be processed asynchronously through:
    1. Data Extraction
    2. Data Validation  
    3. ML Eligibility Scoring
    4. Decision Making
    5. Economic Enablement Recommendations
    
    Returns: Application ID for tracking
    """
    
    if not orchestrator or not tracker:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    # Generate unique application ID
    app_id = f"APP_{uuid.uuid4().hex[:8].upper()}"
    
    # Start observability trace
    trace_id = f"trace_{app_id}"
    tracker.start_trace(trace_id, app_id, {
        "applicant_name": application.applicant_info.full_name,
        "submission_time": datetime.now().isoformat()
    })
    
    # Convert Pydantic models to dicts for processing
    app_data = {
        "applicant_info": application.applicant_info.dict(),
        "income": application.income.dict(),
        "family_members": [m.dict() for m in application.family_members],
        "assets": application.assets.dict(),
        "liabilities": application.liabilities.dict(),
        "documents": application.documents,
        "notes": application.notes
    }
    
    # Add background task for processing
    background_tasks.add_task(
        process_application_background,
        app_id,
        app_data,
        trace_id
    )
    
    return ApplicationResponse(
        application_id=app_id,
        status="submitted",
        message=f"Application {app_id} submitted successfully. Processing started.",
        submitted_at=datetime.now().isoformat()
    )


@app.get("/applications/{application_id}/status", 
         response_model=ProcessingStatus, 
         tags=["Applications"])
async def get_application_status(application_id: str):
    """Get processing status of an application"""
    
    if application_id not in applications_in_process and application_id not in processing_results:
        raise HTTPException(status_code=404, detail=f"Application {application_id} not found")
    
    # Check if still processing
    if application_id in applications_in_process:
        state = applications_in_process[application_id]
        total_stages = 6
        completed = len(state["processing_log"])
        
        return ProcessingStatus(
            application_id=application_id,
            status="processing",
            current_stage=state["stage"],
            progress_percentage=(completed / total_stages) * 100,
            processing_times=state["processing_times"],
            error_count=len(state["errors"]),
            last_updated=datetime.now().isoformat()
        )
    
    # Otherwise check completed results
    result = processing_results.get(application_id, {})
    
    return ProcessingStatus(
        application_id=application_id,
        status=result.get("status", "unknown"),
        current_stage="complete",
        progress_percentage=100.0,
        processing_times=result.get("processing_times", {}),
        error_count=len(result.get("errors", [])),
        last_updated=result.get("completed_at", datetime.now().isoformat())
    )


@app.get("/applications/{application_id}/decision", 
         response_model=DecisionResult,
         tags=["Applications"])
async def get_application_decision(application_id: str):
    """Get decision and recommendations for an application"""
    
    if application_id not in processing_results:
        raise HTTPException(
            status_code=404,
            detail=f"Decision for application {application_id} not ready or not found"
        )
    
    result = processing_results[application_id]
    decision = result.get("decision_results", {})
    recommendations = result.get("recommendations", {})
    
    return DecisionResult(
        application_id=application_id,
        decision=decision.get("decision", "pending"),
        confidence=result.get("confidence_scores", {}).get("decision", 0),
        reasoning=result.get("observations", []),
        recommendations=recommendations.get("programs", []),
        processing_time=result.get("processing_times", {}).get("total", 0),
        processed_at=result.get("completed_at", datetime.now().isoformat())
    )


@app.get("/applications/{application_id}/details", tags=["Applications"])
async def get_application_details(application_id: str):
    """Get complete application processing details"""
    
    if application_id not in processing_results:
        raise HTTPException(status_code=404, detail="Application not found")
    
    result = processing_results[application_id]
    
    return {
        "application_id": application_id,
        "status": result.get("status"),
        "decision": {
            "decision": result.get("decision_results", {}).get("decision"),
            "confidence": result.get("confidence_scores", {}).get("decision", 0)
        },
        "ml_scoring": {
            "eligibility_score": result.get("ml_prediction", {}).get("eligibility_score"),
            "confidence": result.get("confidence_scores", {}).get("ml_scoring", 0),
            "feature_importance": result.get("ml_prediction", {}).get("feature_importance", {})
        },
        "validation": {
            "quality_score": result.get("confidence_scores", {}).get("validation", 0),
            "issues_found": len(result.get("validation_results", {}).get("validation_errors", [])),
            "errors": result.get("validation_results", {}).get("validation_errors", [])
        },
        "recommendations": result.get("recommendations", {}).get("programs", []),
        "processing_timeline": {
            "stages": result.get("processing_log", []),
            "total_time": result.get("processing_times", {}).get("total", 0),
            "by_stage": {
                stage: duration 
                for stage, duration in result.get("processing_times", {}).items()
            }
        },
        "reasoning": {
            "thoughts": result.get("thoughts", []),
            "observations": result.get("observations", []),
            "actions": result.get("actions_taken", [])
        }
    }


@app.get("/statistics", tags=["Analytics"])
async def get_statistics():
    """Get system statistics and metrics"""
    
    total_applications = len(processing_results) + len(applications_in_process)
    completed = len(processing_results)
    in_process = len(applications_in_process)
    
    # Calculate averages
    processing_times = []
    confidence_scores = []
    
    for result in processing_results.values():
        processing_times.append(result.get("processing_times", {}).get("total", 0))
        avg_confidence = (sum(result.get("confidence_scores", {}).values()) / 
                         len(result.get("confidence_scores", {}))) if result.get("confidence_scores") else 0
        confidence_scores.append(avg_confidence)
    
    approvals = sum(
        1 for r in processing_results.values() 
        if r.get("decision_results", {}).get("decision") == "approve"
    )
    
    return {
        "timestamp": datetime.now().isoformat(),
        "applications": {
            "total": total_applications,
            "completed": completed,
            "in_process": in_process,
            "approvals": approvals,
            "approval_rate": approvals / completed if completed > 0 else 0
        },
        "performance": {
            "average_processing_time": sum(processing_times) / len(processing_times) if processing_times else 0,
            "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        },
        "observability": {
            "traces_recorded": tracker.traces.__len__() if tracker else 0,
            "export_path": str(tracker.local_export_path) if tracker else ""
        }
    }


@app.post("/export-observability", tags=["Analytics"])
async def export_observability():
    """Export all observability data to JSON"""
    
    if not tracker:
        raise HTTPException(status_code=503, detail="Observability not initialized")
    
    export_file = tracker.export_all_traces()
    
    return {
        "message": "Observability data exported successfully",
        "file": export_file,
        "traces_exported": len(tracker.traces)
    }


# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def process_application_background(app_id: str, 
                                        app_data: Dict[str, Any],
                                        trace_id: str):
    """
    Background task to process application through LangGraph workflow.
    Integrates with Langfuse for observability.
    """
    
    global tracker
    
    if not orchestrator or not tracker:
        return
    
    try:
        # Mark as in process
        print(f"Starting processing for {app_id}...")
        
        # Process through orchestrator
        result = orchestrator.process_application(app_id, app_data)
        
        # Log to observability
        if tracker:
            tracker.log_extraction(
                app_id,
                extracted_fields=len(result.get("extraction_results", {}).get("fields", {})),
                confidence=result.get("confidence_scores", {}).get("extraction", 0),
                duration=result.get("processing_times", {}).get("extraction", 0)
            )
            
            tracker.log_validation(
                app_id,
                quality_score=result.get("confidence_scores", {}).get("validation", 0),
                issues_found=len(result.get("validation_results", {}).get("validation_errors", [])),
                duration=result.get("processing_times", {}).get("validation", 0)
            )
            
            tracker.log_ml_scoring(
                app_id,
                eligibility_score=result.get("ml_prediction", {}).get("eligibility_score", 0),
                model_confidence=result.get("confidence_scores", {}).get("ml_scoring", 0),
                duration=result.get("processing_times", {}).get("ml_scoring", 0)
            )
            
            tracker.log_decision(
                app_id,
                decision=result.get("decision_results", {}).get("decision", "pending"),
                confidence=result.get("confidence_scores", {}).get("decision", 0),
                duration=result.get("processing_times", {}).get("decision", 0)
            )
            
            tracker.log_recommendations(
                app_id,
                recommendation_count=len(result.get("recommendations", {}).get("programs", [])),
                duration=result.get("processing_times", {}).get("recommendations", 0)
            )
            
            # End trace
            tracker.end_trace()
        
        # Store results
        processing_results[app_id] = {
            **result,
            "completed_at": datetime.now().isoformat()
        }
        
        # Remove from in-process
        if app_id in applications_in_process:
            del applications_in_process[app_id]
        
        print(f"✓ Processing completed for {app_id}")
        
    except Exception as e:
        print(f"✗ Error processing {app_id}: {e}")
        
        # Log error
        if tracker:
            tracker.log_error(app_id, "processing", str(e))
            tracker.end_trace()
        
        # Mark as failed
        if app_id in applications_in_process:
            applications_in_process[app_id]["status"] = "failed"
            applications_in_process[app_id]["errors"].append(str(e))


# ============================================================================
# ADDITIONAL UTILITIES
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """API documentation and information"""
    return {
        "name": "Social Support Application API",
        "version": "1.0.0",
        "description": "AI-powered application processing for government social support programs",
        "endpoints": {
            "submission": "/applications/submit",
            "status": "/applications/{application_id}/status",
            "decision": "/applications/{application_id}/decision",
            "details": "/applications/{application_id}/details",
            "statistics": "/statistics",
            "health": "/health"
        },
        "documentation": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
