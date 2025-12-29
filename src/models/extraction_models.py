"""
Data models for extraction agent - unified representation of extracted application data.

These models represent the structured output from document extraction and validation.
They serve as the single source of truth for application data across all processing stages.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class EmploymentType(str, Enum):
    """Employment types matching data generation configuration."""
    GOVERNMENT = "Government"
    PRIVATE = "Private"
    SELF_EMPLOYED = "Self-Employed"
    UNEMPLOYED = "Unemployed"
    STUDENT = "Student"


class DocumentType(str, Enum):
    """Types of documents in application."""
    BANK_STATEMENT = "bank_statement"
    EMIRATES_ID = "emirates_id"
    EMPLOYMENT_LETTER = "employment_letter"
    RESUME = "resume"
    ASSETS_LIABILITIES = "assets_liabilities"
    CREDIT_REPORT = "credit_report"


class ExtractionStatus(str, Enum):
    """Status of extraction for each document."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    MISSING = "missing"


class VerificationStatus(str, Enum):
    """Verification status for extracted data."""
    VERIFIED = "verified"
    CONFLICTED = "conflicted"
    INCOMPLETE = "incomplete"
    SUSPICIOUS = "suspicious"


@dataclass
class ExtractionMetadata:
    """Metadata about extraction process."""
    document_type: DocumentType
    extraction_status: ExtractionStatus
    confidence: float  # 0.0-1.0
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    extraction_method: str = ""  # e.g., "pdfplumber", "pytesseract", "openpyxl"
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time_ms: float = 0.0


@dataclass
class PersonalInfo:
    """Personal identification data."""
    full_name: Optional[str] = None
    emirates_id: Optional[str] = None
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    marital_status: Optional[str] = None
    dependents: Optional[int] = None


@dataclass
class BankAccount:
    """Bank account information."""
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    currency: str = "AED"
    balance: Optional[float] = None
    account_type: Optional[str] = None


@dataclass
class BankTransaction:
    """Single bank transaction."""
    date: date
    description: str
    amount: float
    transaction_type: str  # "credit" or "debit"
    running_balance: Optional[float] = None


@dataclass
class BankStatementExtraction:
    """Extracted data from bank statement."""
    account: BankAccount = field(default_factory=BankAccount)
    statement_period_start: Optional[date] = None
    statement_period_end: Optional[date] = None
    transactions: List[BankTransaction] = field(default_factory=list)
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    monthly_average_debit: Optional[float] = None
    monthly_average_credit: Optional[float] = None
    salary_deposits: List[BankTransaction] = field(default_factory=list)
    
    def extract_monthly_income(self) -> Optional[float]:
        """Calculate average monthly salary/income deposits."""
        if not self.salary_deposits:
            return None
        total = sum(t.amount for t in self.salary_deposits)
        months = self._count_months_in_statement()
        return total / months if months > 0 else None
    
    def _count_months_in_statement(self) -> int:
        """Count number of months covered by statement."""
        if self.statement_period_start and self.statement_period_end:
            delta = self.statement_period_end - self.statement_period_start
            return max(1, delta.days // 30)
        return 1


@dataclass
class EmploymentInfo:
    """Employment/employment history information."""
    employment_type: Optional[EmploymentType] = None
    current_employer: Optional[str] = None
    job_title: Optional[str] = None
    employment_start_date: Optional[date] = None
    employment_end_date: Optional[date] = None
    monthly_salary: Optional[float] = None
    currency: str = "AED"
    employment_status: Optional[str] = None  # "Active", "Employed", "Unemployed"
    

@dataclass
class WorkExperience:
    """Single work experience entry from resume."""
    employer: str
    job_title: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None
    current: bool = False


@dataclass
class ResumeExtraction:
    """Extracted data from resume/CV."""
    education: List[str] = field(default_factory=list)
    work_experience: List[WorkExperience] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    summary: Optional[str] = None


@dataclass
class Property:
    """Real estate property."""
    type: str  # "Apartment", "Villa", "Townhouse"
    location: Optional[str] = None
    estimated_value: Optional[float] = None
    mortgage_remaining: Optional[float] = None
    status: str = "Owned"  # "Owned", "Mortgaged"


@dataclass
class Vehicle:
    """Vehicle asset."""
    make: str
    model: str
    year: Optional[int] = None
    estimated_value: Optional[float] = None
    loan_remaining: Optional[float] = None
    status: str = "Owned"


@dataclass
class Loan:
    """Loan liability."""
    type: str  # "Mortgage", "Auto Loan", "Personal Loan"
    amount_remaining: float
    monthly_payment: float
    interest_rate: Optional[float] = None
    months_remaining: Optional[int] = None


@dataclass
class AssetLiabilityExtraction:
    """Extracted data from asset/liability sheet."""
    properties: List[Property] = field(default_factory=list)
    vehicles: List[Vehicle] = field(default_factory=list)
    savings: Optional[float] = None
    investments: Optional[float] = None
    loans: List[Loan] = field(default_factory=list)
    credit_card_debt: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    
    def calculate_net_worth(self) -> Optional[float]:
        """Calculate total net worth."""
        if self.total_assets is not None and self.total_liabilities is not None:
            return self.total_assets - self.total_liabilities
        return None
    
    def calculate_debt_to_income_ratio(self, monthly_income: float) -> Optional[float]:
        """Calculate debt-to-income ratio."""
        if monthly_income <= 0 or self.total_liabilities is None:
            return None
        monthly_obligations = sum(loan.monthly_payment for loan in self.loans)
        return monthly_obligations / monthly_income if monthly_income > 0 else None


@dataclass
class CreditAccount:
    """Single credit account from credit report."""
    account_type: str  # "Mortgage", "Auto Loan", "Credit Card"
    balance: float
    credit_limit: Optional[float] = None
    monthly_payment: float = 0.0
    payment_status: Optional[str] = None  # "Current", "Late", "Missed"
    months_in_good_standing: Optional[int] = None


@dataclass
class CreditReportExtraction:
    """Extracted data from credit report."""
    credit_score: Optional[int] = None  # UAE scale 0-1800
    score_rating: Optional[str] = None  # "Excellent", "Very Good", "Good", "Fair", "Poor"
    total_active_accounts: Optional[int] = None
    accounts: List[CreditAccount] = field(default_factory=list)
    payment_history: Dict[str, int] = field(default_factory=dict)  # {"on_time": 10, "late_30": 2, "late_60": 0, "missed": 0}
    total_outstanding_balance: Optional[float] = None
    total_credit_limit: Optional[float] = None
    enquiries_count: Optional[int] = None
    remarks: Optional[str] = None


@dataclass
class ApplicationExtraction:
    """Complete extracted data from all documents for one application."""
    application_id: str
    personal_info: PersonalInfo
    employment_info: EmploymentInfo
    bank_statement: Optional[BankStatementExtraction] = None
    resume: Optional[ResumeExtraction] = None
    assets_liabilities: Optional[AssetLiabilityExtraction] = None
    credit_report: Optional[CreditReportExtraction] = None
    
    # Extraction metadata
    extraction_metadata: Dict[DocumentType, ExtractionMetadata] = field(default_factory=dict)
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    
    # Validation results
    verification_status: VerificationStatus = VerificationStatus.INCOMPLETE
    consistency_issues: List[str] = field(default_factory=list)
    missing_documents: List[DocumentType] = field(default_factory=list)
    data_quality_score: Optional[float] = None  # 0.0-1.0
    
    def get_extraction_status(self, doc_type: DocumentType) -> Optional[ExtractionStatus]:
        """Get extraction status for specific document."""
        if doc_type in self.extraction_metadata:
            return self.extraction_metadata[doc_type].extraction_status
        return None
    
    def get_monthly_income(self) -> Optional[float]:
        """Get monthly income from bank statement if available."""
        if self.bank_statement:
            return self.bank_statement.extract_monthly_income()
        # Fallback to employment letter
        if self.employment_info and self.employment_info.monthly_salary:
            return self.employment_info.monthly_salary
        return None
    
    def is_fully_extracted(self) -> bool:
        """Check if all critical documents are successfully extracted."""
        critical_docs = [
            DocumentType.EMIRATES_ID,
            DocumentType.BANK_STATEMENT,
            DocumentType.EMPLOYMENT_LETTER,
        ]
        for doc in critical_docs:
            if self.get_extraction_status(doc) != ExtractionStatus.SUCCESS:
                return False
        return True
    
    def all_documents_present(self) -> bool:
        """Check if all expected documents were found."""
        return len(self.missing_documents) == 0


@dataclass
class ExtractionBatchResult:
    """Results from batch extraction of multiple applications."""
    total_applications: int
    successful_extractions: int
    failed_extractions: int
    partial_extractions: int
    applications: List[ApplicationExtraction] = field(default_factory=list)
    
    # Statistics
    extraction_time_ms: float = 0.0
    average_quality_score: Optional[float] = None
    document_success_rates: Dict[DocumentType, float] = field(default_factory=dict)
    
    def success_rate(self) -> float:
        """Overall success rate of batch extraction."""
        if self.total_applications == 0:
            return 0.0
        return self.successful_extractions / self.total_applications
    
    def get_failed_applications(self) -> List[str]:
        """Get list of failed application IDs."""
        return [app.application_id for app in self.applications 
                if app.verification_status == VerificationStatus.INCOMPLETE]
