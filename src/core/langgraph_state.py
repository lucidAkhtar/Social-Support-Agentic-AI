"""
LangGraph State Schema - Type-safe state management for multi-agent workflow

This module defines the TypedDict state schema that flows through the LangGraph
workflow. Each agent reads from and writes to this shared state.

State Management:
    - Immutable updates (new dict returned on each modification)
    - Type-checked at runtime
    - Supports partial updates (agents only update relevant fields)
    
State Flow:
    Input → Extract → Validate → Eligibility → Recommend → Explain → Output
"""

from typing import TypedDict, List, Optional, Dict, Any
from datetime import datetime
from ..core.types import (
    ExtractedData,
    ValidationReport,
    EligibilityResult,
    Recommendation,
    ProcessingStage
)


class ApplicationGraphState(TypedDict, total=False):
    """
    LangGraph state that flows through the entire agent workflow.
    
    Using TypedDict with total=False allows partial updates - agents
    only need to update fields they're responsible for.
    
    State Progression:
        1. Input: application_id, documents, applicant_name
        2. After Extraction: extracted_data
        3. After Validation: validation_report
        4. After Eligibility: eligibility_result
        5. After Recommendation: recommendation
        6. After Explanation: explanation
        7. Throughout: stage, errors, metadata
    
    Attributes:
        # Application Identity
        application_id: Unique application identifier
        applicant_name: Name of the applicant
        
        # Input Data
        documents: List of uploaded document objects
        
        # Processing Stage
        stage: Current processing stage (pending, extracting, validating, etc.)
        
        # Agent Outputs (populated sequentially)
        extracted_data: Structured data from documents (Extraction Agent)
        validation_report: Consistency check results (Validation Agent)
        eligibility_result: ML-based decision (Eligibility Agent)
        recommendation: Support amount + programs (Recommendation Agent)
        explanation: Natural language justification (Explanation Agent)
        
        # Chat Support
        chat_history: List of chat interactions (RAG Chatbot Agent)
        
        # Error Handling
        errors: List of error messages encountered
        
        # Metadata
        created_at: Timestamp of application creation
        updated_at: Last update timestamp
        processing_start_time: When processing started
        processing_end_time: When processing completed
        
        # LangGraph Control
        next_agent: Which agent to route to next (used for conditional routing)
    """
    
    # Identity
    application_id: str
    applicant_name: str
    
    # Input
    documents: List[Dict[str, Any]]  # Serialized document objects
    
    # Current Stage
    stage: str  # ProcessingStage enum value
    
    # Agent Outputs
    extracted_data: Optional[ExtractedData]
    validation_report: Optional[ValidationReport]
    eligibility_result: Optional[EligibilityResult]
    recommendation: Optional[Recommendation]
    explanation: Optional[str]
    
    # Chat Support
    chat_history: List[Dict[str, Any]]
    
    # Error Handling
    errors: List[str]
    
    # Metadata
    created_at: str  # ISO format datetime
    updated_at: str  # ISO format datetime
    processing_start_time: Optional[str]
    processing_end_time: Optional[str]
    timestamps: Dict[str, str]  # Dictionary of timestamp events
    
    # LangGraph Control Flow
    next_agent: Optional[str]  # For conditional routing
    

def create_initial_state(
    application_id: str,
    applicant_name: str,
    documents: List[Dict[str, Any]]
) -> ApplicationGraphState:
    """
    Create initial state for a new application.
    
    Args:
        application_id: Unique identifier
        applicant_name: Applicant's full name
        documents: List of serialized document objects
        
    Returns:
        ApplicationGraphState with initial values set
    """
    now = datetime.now().isoformat()
    
    return ApplicationGraphState(
        application_id=application_id,
        applicant_name=applicant_name,
        documents=documents,
        stage=ProcessingStage.PENDING.value,
        extracted_data=None,
        validation_report=None,
        eligibility_result=None,
        recommendation=None,
        explanation=None,
        chat_history=[],
        errors=[],
        created_at=now,
        updated_at=now,
        processing_start_time=None,
        processing_end_time=None,
        timestamps={},
        next_agent=None
    )
