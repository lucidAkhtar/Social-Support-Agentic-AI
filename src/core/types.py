"""
Core data types for the Social Support Application System
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class ProcessingStage(Enum):
    """Application processing stages"""
    PENDING = "pending"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    CHECKING_ELIGIBILITY = "checking_eligibility"
    GENERATING_RECOMMENDATION = "generating_recommendation"
    COMPLETED = "completed"
    FAILED = "failed"


class DecisionType(Enum):
    """Decision outcomes"""
    APPROVED = "approved"
    SOFT_DECLINED = "soft_declined"
    DECLINED = "declined"
    PENDING_REVIEW = "pending_review"


@dataclass
class Document:
    """Uploaded document metadata"""
    document_id: str
    document_type: str  # emirates_id, bank_statement, resume, assets_liabilities, credit_report
    filename: str
    file_path: str
    uploaded_at: datetime = field(default_factory=datetime.now)
    processed: bool = False


@dataclass
class ExtractedData:
    """Data extracted from all documents"""
    applicant_info: Dict[str, Any] = field(default_factory=dict)  # Name, ID, contact
    income_data: Dict[str, Any] = field(default_factory=dict)  # From bank statements
    employment_data: Dict[str, Any] = field(default_factory=dict)  # From resume
    assets_liabilities: Dict[str, Any] = field(default_factory=dict)  # From Excel
    credit_data: Dict[str, Any] = field(default_factory=dict)  # From credit report
    family_info: Dict[str, Any] = field(default_factory=dict)  # Family size, dependents
    raw_ocr_text: Dict[str, str] = field(default_factory=dict)  # Document type -> raw text
    extraction_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ValidationIssue:
    """A single validation issue found"""
    severity: str  # critical, warning, info
    category: str  # inconsistency, missing_data, format_error
    field: str
    message: str
    documents_affected: List[str]
    suggested_resolution: Optional[str] = None


@dataclass
class ValidationReport:
    """Validation results"""
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    cross_document_checks: Dict[str, Any] = field(default_factory=dict)
    data_completeness_score: float = 0.0
    confidence_score: float = 0.0
    validation_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EligibilityResult:
    """Eligibility determination output"""
    is_eligible: bool
    eligibility_score: float  # 0.0 to 1.0
    ml_prediction: Dict[str, Any] = field(default_factory=dict)  # Model output
    policy_rules_met: Dict[str, bool] = field(default_factory=dict)  # Rule checks
    income_assessment: Dict[str, Any] = field(default_factory=dict)
    wealth_assessment: Dict[str, Any] = field(default_factory=dict)
    employment_assessment: Dict[str, Any] = field(default_factory=dict)
    demographic_factors: Dict[str, Any] = field(default_factory=dict)
    reasoning: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Recommendation:
    """Final recommendation output"""
    decision: DecisionType
    financial_support_amount: Optional[float] = None
    financial_support_type: Optional[str] = None
    economic_enablement_programs: List[Dict[str, Any]] = field(default_factory=list)
    # Programs like upskilling, job matching, career counseling
    confidence_level: float = 0.0
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Explanation:
    """Natural language explanation of the decision"""
    summary: str  # Brief explanation
    detailed_reasoning: str  # Full breakdown
    factors_analysis: Dict[str, Any] = field(default_factory=dict)
    what_if_scenarios: List[Dict[str, Any]] = field(default_factory=list)
    human_review_notes: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ApplicationState:
    """Complete application state through the pipeline"""
    application_id: str
    applicant_name: Optional[str] = None  # Name provided during application creation
    stage: ProcessingStage = ProcessingStage.PENDING
    
    # Documents
    documents: List[Document] = field(default_factory=list)
    
    # Agent outputs
    extracted_data: Optional[ExtractedData] = None
    validation_report: Optional[ValidationReport] = None
    eligibility_result: Optional[EligibilityResult] = None
    recommendation: Optional[Recommendation] = None
    explanation: Optional[Explanation] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    errors: List[str] = field(default_factory=list)
    
    # Chatbot interaction history
    chat_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def update_stage(self, new_stage: ProcessingStage):
        """Update processing stage"""
        self.stage = new_stage
        self.updated_at = datetime.now()
    
    def add_error(self, error: str):
        """Add an error"""
        self.errors.append(error)
        self.stage = ProcessingStage.FAILED
        self.updated_at = datetime.now()
    
    def is_chatbot_enabled(self) -> bool:
        """Determine if chatbot should be enabled"""
        # Chatbot only enabled after validation is complete
        return self.stage in [
            ProcessingStage.CHECKING_ELIGIBILITY,
            ProcessingStage.GENERATING_RECOMMENDATION,
            ProcessingStage.COMPLETED
        ]


@dataclass
class AgentMessage:
    """Message passed between agents"""
    sender: str
    recipient: str
    message_type: str  # request, response, error, status_update
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    correlation_id: Optional[str] = None
