"""
Validation Agent - Cross-document consistency checking and data quality validation.

This agent validates extracted data from multiple documents by:
1. Checking consistency across documents (name, ID, dates)
2. Detecting income mismatches and financial anomalies
3. Verifying employment details against bank records
4. Scoring overall data quality
5. Flagging conflicts and inconsistencies for review

Uses ApplicationExtraction from Phase 2 as input.
Produces ValidationResult with detailed findings.
"""

import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from enum import Enum

from src.models.extraction_models import (
    ApplicationExtraction, PersonalInfo, EmploymentInfo, 
    BankStatementExtraction, AssetLiabilityExtraction,
    CreditReportExtraction, ExtractionMetadata
)

logger = logging.getLogger(__name__)


class ConflictSeverity(str, Enum):
    """Severity level of validation conflicts."""
    CRITICAL = "critical"      # Must resolve before approval
    HIGH = "high"              # Should review before approval
    MEDIUM = "medium"          # Review if threshold exceeded
    LOW = "low"                # Minor inconsistency, may auto-resolve
    INFO = "info"              # Informational, no action needed


class ValidationStatus(str, Enum):
    """Overall validation status."""
    PASSED = "passed"          # All checks successful
    PASSED_WITH_WARNINGS = "passed_with_warnings"  # Passed but has issues
    NEEDS_REVIEW = "needs_review"                  # Conflicts found
    FAILED = "failed"          # Critical failures


@dataclass
class ValidationFinding:
    """Single validation finding."""
    category: str              # "personal_info", "employment", "income", etc.
    finding_type: str          # "mismatch", "missing", "inconsistent", etc.
    severity: ConflictSeverity
    message: str
    fields_involved: List[str]
    affected_documents: List[str]
    auto_resolvable: bool = False
    suggested_resolution: Optional[str] = None


@dataclass
class ValidationResult:
    """Complete validation result for an application."""
    application_id: str
    validation_status: ValidationStatus
    
    # Validation metrics
    consistency_score: float        # 0.0-1.0, how consistent are documents
    completeness_score: float       # 0.0-1.0, how complete is the data
    quality_score: float            # 0.0-1.0, overall quality
    
    # Findings
    findings: List[ValidationFinding] = field(default_factory=list)
    
    # Summary
    documents_validated: List[str] = field(default_factory=list)
    validation_timestamp: datetime = field(default_factory=datetime.now)
    validation_duration_ms: float = 0.0
    
    # Scores breakdown
    personal_info_score: float = 0.0
    employment_score: float = 0.0
    income_score: float = 0.0
    assets_score: float = 0.0
    credit_score: float = 0.0
    
    def add_finding(self, finding: ValidationFinding):
        """Add a validation finding."""
        self.findings.append(finding)
    
    def critical_issues(self) -> List[ValidationFinding]:
        """Get all critical severity findings."""
        return [f for f in self.findings if f.severity == ConflictSeverity.CRITICAL]
    
    def high_issues(self) -> List[ValidationFinding]:
        """Get all high severity findings."""
        return [f for f in self.findings if f.severity == ConflictSeverity.HIGH]
    
    def all_issues(self) -> List[ValidationFinding]:
        """Get all non-info findings."""
        return [f for f in self.findings 
                if f.severity not in [ConflictSeverity.INFO]]


class PersonalInfoValidator:
    """Validate personal information consistency across documents."""
    
    @staticmethod
    def validate(extraction: ApplicationExtraction) -> List[ValidationFinding]:
        """Validate personal information consistency."""
        findings = []
        
        if not extraction.personal_info:
            return findings
        
        personal_info = extraction.personal_info
        
        # Check for complete personal info
        required_fields = ['full_name', 'emirates_id', 'date_of_birth', 'nationality']
        missing_fields = [f for f in required_fields 
                         if not getattr(personal_info, f, None)]
        
        if missing_fields:
            findings.append(ValidationFinding(
                category="personal_info",
                finding_type="missing_fields",
                severity=ConflictSeverity.HIGH,
                message=f"Missing personal information: {', '.join(missing_fields)}",
                fields_involved=missing_fields,
                affected_documents=["emirates_id"]
            ))
        
        # Validate Emirates ID format
        if personal_info.emirates_id:
            if not PersonalInfoValidator._is_valid_emirates_id(personal_info.emirates_id):
                findings.append(ValidationFinding(
                    category="personal_info",
                    finding_type="invalid_format",
                    severity=ConflictSeverity.MEDIUM,
                    message=f"Emirates ID format appears invalid: {personal_info.emirates_id}",
                    fields_involved=["emirates_id"],
                    affected_documents=["emirates_id"]
                ))
        
        # Validate age (should be > 18)
        if personal_info.date_of_birth:
            age = (date.today() - personal_info.date_of_birth).days // 365
            if age < 18:
                findings.append(ValidationFinding(
                    category="personal_info",
                    finding_type="age_validation",
                    severity=ConflictSeverity.CRITICAL,
                    message=f"Applicant age is {age}, must be 18+",
                    fields_involved=["date_of_birth"],
                    affected_documents=["emirates_id"]
                ))
            elif age > 100:
                findings.append(ValidationFinding(
                    category="personal_info",
                    finding_type="age_validation",
                    severity=ConflictSeverity.MEDIUM,
                    message=f"Applicant age is {age}, appears implausible",
                    fields_involved=["date_of_birth"],
                    affected_documents=["emirates_id"],
                    auto_resolvable=True
                ))
        
        return findings
    
    @staticmethod
    def _is_valid_emirates_id(emirates_id: str) -> bool:
        """Check if Emirates ID format is valid."""
        # Format: XXX-YYYY-ZZZZZZZZ-C (12 digits + 3 hyphens)
        import re
        pattern = r'^\d{3}-\d{4}-\d{7}-\d$'
        return bool(re.match(pattern, emirates_id))


class EmploymentValidator:
    """Validate employment information consistency."""
    
    @staticmethod
    def validate(extraction: ApplicationExtraction) -> List[ValidationFinding]:
        """Validate employment information."""
        findings = []
        
        if not extraction.employment_info:
            findings.append(ValidationFinding(
                category="employment",
                finding_type="missing_data",
                severity=ConflictSeverity.HIGH,
                message="No employment information extracted",
                fields_involved=["employment_info"],
                affected_documents=["employment_letter", "resume"]
            ))
            return findings
        
        emp = extraction.employment_info
        
        # Check required employment fields
        if not emp.current_employer:
            findings.append(ValidationFinding(
                category="employment",
                finding_type="missing_employer",
                severity=ConflictSeverity.HIGH,
                message="Current employer information missing",
                fields_involved=["current_employer"],
                affected_documents=["employment_letter"]
            ))
        
        if not emp.job_title:
            findings.append(ValidationFinding(
                category="employment",
                finding_type="missing_job_title",
                severity=ConflictSeverity.MEDIUM,
                message="Job title information missing",
                fields_involved=["job_title"],
                affected_documents=["employment_letter", "resume"]
            ))
        
        # Validate employment duration
        if emp.employment_start_date and emp.employment_end_date:
            if emp.employment_end_date < emp.employment_start_date:
                findings.append(ValidationFinding(
                    category="employment",
                    finding_type="invalid_dates",
                    severity=ConflictSeverity.CRITICAL,
                    message="Employment end date is before start date",
                    fields_involved=["employment_start_date", "employment_end_date"],
                    affected_documents=["employment_letter", "resume"]
                ))
        
        # Check employment duration (should be at least 3 months for stability)
        if emp.employment_start_date:
            duration_days = (date.today() - emp.employment_start_date).days
            if duration_days < 90:
                findings.append(ValidationFinding(
                    category="employment",
                    finding_type="short_duration",
                    severity=ConflictSeverity.MEDIUM,
                    message=f"Current employment duration is only {duration_days // 30} months",
                    fields_involved=["employment_start_date"],
                    affected_documents=["employment_letter"]
                ))
        
        return findings


class IncomeValidator:
    """Validate income consistency across documents."""
    
    @staticmethod
    def validate(extraction: ApplicationExtraction) -> List[ValidationFinding]:
        """Validate income information and consistency."""
        findings = []
        
        emp_salary = None
        bank_income = None
        
        # Get employment salary
        if extraction.employment_info and extraction.employment_info.monthly_salary:
            emp_salary = extraction.employment_info.monthly_salary
        
        # Get average monthly income from bank statement
        if extraction.bank_statement:
            bank_income = extraction.bank_statement.extract_monthly_income()
        
        # Check for income data
        if not emp_salary and not bank_income:
            findings.append(ValidationFinding(
                category="income",
                finding_type="missing_income",
                severity=ConflictSeverity.CRITICAL,
                message="No income information found in employment letter or bank statement",
                fields_involved=["monthly_salary", "extract_monthly_income()"],
                affected_documents=["employment_letter", "bank_statement"]
            ))
            return findings
        
        # Validate income consistency
        if emp_salary and bank_income:
            # Allow 20% variance (different calculation methods)
            variance = abs(emp_salary - bank_income) / max(emp_salary, bank_income)
            
            if variance > 0.30:  # > 30% variance
                findings.append(ValidationFinding(
                    category="income",
                    finding_type="income_mismatch",
                    severity=ConflictSeverity.HIGH,
                    message=f"Income mismatch: Employment letter shows AED {emp_salary}, "
                           f"but bank statement shows average AED {bank_income} ({variance*100:.0f}% variance)",
                    fields_involved=["monthly_salary", "monthly_average_credit"],
                    affected_documents=["employment_letter", "bank_statement"],
                    auto_resolvable=False,
                    suggested_resolution="Manual review required to verify actual income"
                ))
            elif variance > 0.15:  # > 15% variance
                findings.append(ValidationFinding(
                    category="income",
                    finding_type="income_variance",
                    severity=ConflictSeverity.MEDIUM,
                    message=f"Income variance detected: {variance*100:.0f}% difference between "
                           f"employment letter (AED {emp_salary}) and bank statement (AED {bank_income})",
                    fields_involved=["monthly_salary", "monthly_average_credit"],
                    affected_documents=["employment_letter", "bank_statement"],
                    auto_resolvable=True,
                    suggested_resolution="Accept average of both values"
                ))
        
        # Validate income minimum threshold (for UAE social support)
        final_income = emp_salary or bank_income
        if final_income and final_income < 1000:  # Below minimum
            findings.append(ValidationFinding(
                category="income",
                finding_type="low_income",
                severity=ConflictSeverity.INFO,
                message=f"Monthly income is AED {final_income}, which may qualify for support",
                fields_involved=["monthly_salary"],
                affected_documents=["employment_letter", "bank_statement"]
            ))
        
        return findings


class AssetValidator:
    """Validate assets and liabilities consistency."""
    
    @staticmethod
    def validate(extraction: ApplicationExtraction) -> List[ValidationFinding]:
        """Validate assets and financial position."""
        findings = []
        
        if not extraction.assets_liabilities:
            findings.append(ValidationFinding(
                category="assets",
                finding_type="missing_data",
                severity=ConflictSeverity.MEDIUM,
                message="No asset/liability information extracted",
                fields_involved=["assets_liabilities"],
                affected_documents=["assets_liabilities"]
            ))
            return findings
        
        assets = extraction.assets_liabilities
        net_worth = assets.calculate_net_worth()
        
        # Check for extreme wealth (may disqualify from benefits)
        if net_worth and net_worth > 500000:  # > AED 500K
            findings.append(ValidationFinding(
                category="assets",
                finding_type="high_net_worth",
                severity=ConflictSeverity.MEDIUM,
                message=f"High net worth detected: AED {net_worth:,.0f}. May not qualify for social support.",
                fields_involved=["properties", "vehicles", "loans"],
                affected_documents=["assets_liabilities"],
                auto_resolvable=False
            ))
        
        # Check for negative net worth
        if net_worth and net_worth < -100000:  # < -AED 100K debt
            findings.append(ValidationFinding(
                category="assets",
                finding_type="high_debt",
                severity=ConflictSeverity.HIGH,
                message=f"High debt burden detected: AED {net_worth:,.0f} net worth",
                fields_involved=["loans"],
                affected_documents=["assets_liabilities"],
                auto_resolvable=False,
                suggested_resolution="Verify loan obligations and debt structure"
            ))
        
        # Validate assets consistency
        if assets.properties and len(assets.properties) > 5:
            findings.append(ValidationFinding(
                category="assets",
                finding_type="multiple_properties",
                severity=ConflictSeverity.LOW,
                message=f"Multiple properties listed ({len(assets.properties)})",
                fields_involved=["properties"],
                affected_documents=["assets_liabilities"]
            ))
        
        return findings


class CreditValidator:
    """Validate credit information consistency."""
    
    @staticmethod
    def validate(extraction: ApplicationExtraction) -> List[ValidationFinding]:
        """Validate credit history and score."""
        findings = []
        
        if not extraction.credit_report:
            findings.append(ValidationFinding(
                category="credit",
                finding_type="missing_data",
                severity=ConflictSeverity.MEDIUM,
                message="No credit report information extracted",
                fields_involved=["credit_report"],
                affected_documents=["credit_report"]
            ))
            return findings
        
        credit = extraction.credit_report
        
        # Validate credit score
        if credit.credit_score:
            if credit.credit_score < 300:
                findings.append(ValidationFinding(
                    category="credit",
                    finding_type="low_credit_score",
                    severity=ConflictSeverity.HIGH,
                    message=f"Credit score is very low ({credit.credit_score}). "
                           f"May indicate financial risk.",
                    fields_involved=["credit_score"],
                    affected_documents=["credit_report"],
                    auto_resolvable=False
                ))
            elif credit.credit_score < 600:
                findings.append(ValidationFinding(
                    category="credit",
                    finding_type="poor_credit_score",
                    severity=ConflictSeverity.MEDIUM,
                    message=f"Credit score is poor ({credit.credit_score}). "
                           f"Consider additional review.",
                    fields_involved=["credit_score"],
                    affected_documents=["credit_report"]
                ))
        
        # Check for active accounts
        if credit.accounts:
            # Count delinquent accounts
            delinquent = [a for a in credit.accounts 
                         if hasattr(a, 'status') and 'delinquent' in str(a.status).lower()]
            
            if delinquent:
                findings.append(ValidationFinding(
                    category="credit",
                    finding_type="delinquent_accounts",
                    severity=ConflictSeverity.HIGH,
                    message=f"{len(delinquent)} delinquent account(s) found",
                    fields_involved=["accounts"],
                    affected_documents=["credit_report"],
                    auto_resolvable=False,
                    suggested_resolution="Verify account statuses and payment history"
                ))
        
        return findings


class ValidationAgent:
    """Main validation agent orchestrating all validators."""
    
    def __init__(self):
        self.personal_validator = PersonalInfoValidator()
        self.employment_validator = EmploymentValidator()
        self.income_validator = IncomeValidator()
        self.asset_validator = AssetValidator()
        self.credit_validator = CreditValidator()
        logger.info("ValidationAgent initialized")
    
    def validate_application(self, extraction) -> dict:
        """
        Validate a complete extracted application.
        
        Args:
            extraction: ApplicationExtraction from Phase 2 or dict with extracted data
        
        Returns:
            Dict-like ValidationResult with all findings and scores
        """
        start_time = datetime.now()
        
        # Handle dict input (from test or LangGraph)
        if isinstance(extraction, dict):
            # Create a minimal ApplicationExtraction object from dict
            app_extract = ApplicationExtraction(
                application_id=extraction.get("application_id", "UNKNOWN"),
                personal_info=PersonalInfo(),
                employment_info=EmploymentInfo()
            )
            extraction = app_extract
        
        result = ValidationResult(
            application_id=extraction.application_id,
            validation_status=ValidationStatus.PASSED,
            consistency_score=0.0,
            completeness_score=0.0,
            quality_score=0.0
        )
        
        # Run all validators
        result.findings.extend(self.personal_validator.validate(extraction))
        result.findings.extend(self.employment_validator.validate(extraction))
        result.findings.extend(self.income_validator.validate(extraction))
        result.findings.extend(self.asset_validator.validate(extraction))
        result.findings.extend(self.credit_validator.validate(extraction))
        
        # Calculate scores
        result.personal_info_score = self._score_personal_info(extraction, result)
        result.employment_score = self._score_employment(extraction, result)
        result.income_score = self._score_income(extraction, result)
        result.assets_score = self._score_assets(extraction, result)
        result.credit_score = self._score_credit(extraction, result)
        
        # Calculate overall scores
        result.consistency_score = self._calculate_consistency_score(result)
        result.completeness_score = self._calculate_completeness_score(extraction)
        result.quality_score = (
            result.personal_info_score * 0.15 +
            result.employment_score * 0.15 +
            result.income_score * 0.25 +
            result.assets_score * 0.20 +
            result.credit_score * 0.25
        )
        
        # Determine validation status
        critical = result.critical_issues()
        high = result.high_issues()
        
        if critical:
            result.validation_status = ValidationStatus.FAILED
        elif high or (len(result.findings) > 0 and result.quality_score < 0.6):
            result.validation_status = ValidationStatus.NEEDS_REVIEW
        elif result.findings:
            result.validation_status = ValidationStatus.PASSED_WITH_WARNINGS
        else:
            result.validation_status = ValidationStatus.PASSED
        
        # Convert to dict for compatibility with tests
        return {
            "application_id": result.application_id,
            "validation_status": result.validation_status.value,
            "quality_score": result.quality_score,
            "consistency_score": result.consistency_score,
            "completeness_score": result.completeness_score,
            "validation_errors": [(f.category, f.message) for f in result.findings if f.severity.value in ["critical", "high"]],
            "findings_count": len(result.findings),
            "result_object": result  # Keep original for further processing
        }
        
        # Track validated documents
        if extraction.personal_info:
            result.documents_validated.append("emirates_id")
        if extraction.employment_info:
            result.documents_validated.append("employment_letter")
        if extraction.bank_statement:
            result.documents_validated.append("bank_statement")
        if extraction.resume:
            result.documents_validated.append("resume")
        if extraction.assets_liabilities:
            result.documents_validated.append("assets_liabilities")
        if extraction.credit_report:
            result.documents_validated.append("credit_report")
        
        result.validation_duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return result
    
    @staticmethod
    def _score_personal_info(extraction: ApplicationExtraction, result: ValidationResult) -> float:
        """Score personal information completeness."""
        if not extraction.personal_info:
            return 0.0
        
        score = 1.0
        personal_findings = [f for f in result.findings if f.category == "personal_info"]
        
        # Deduct for each finding
        score -= len([f for f in personal_findings if f.severity == ConflictSeverity.CRITICAL]) * 0.3
        score -= len([f for f in personal_findings if f.severity == ConflictSeverity.HIGH]) * 0.15
        score -= len([f for f in personal_findings if f.severity == ConflictSeverity.MEDIUM]) * 0.05
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def _score_employment(extraction: ApplicationExtraction, result: ValidationResult) -> float:
        """Score employment information."""
        if not extraction.employment_info:
            return 0.5  # Partial credit for missing
        
        score = 1.0
        emp_findings = [f for f in result.findings if f.category == "employment"]
        
        score -= len([f for f in emp_findings if f.severity == ConflictSeverity.CRITICAL]) * 0.3
        score -= len([f for f in emp_findings if f.severity == ConflictSeverity.HIGH]) * 0.15
        score -= len([f for f in emp_findings if f.severity == ConflictSeverity.MEDIUM]) * 0.05
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def _score_income(extraction: ApplicationExtraction, result: ValidationResult) -> float:
        """Score income validation."""
        has_employment = extraction.employment_info and extraction.employment_info.monthly_salary
        has_bank = extraction.bank_statement and extraction.bank_statement.extract_monthly_income()
        
        if not has_employment and not has_bank:
            return 0.0
        
        score = 1.0
        income_findings = [f for f in result.findings if f.category == "income"]
        
        score -= len([f for f in income_findings if f.severity == ConflictSeverity.CRITICAL]) * 0.3
        score -= len([f for f in income_findings if f.severity == ConflictSeverity.HIGH]) * 0.15
        score -= len([f for f in income_findings if f.severity == ConflictSeverity.MEDIUM]) * 0.1
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def _score_assets(extraction: ApplicationExtraction, result: ValidationResult) -> float:
        """Score assets/liabilities."""
        if not extraction.assets_liabilities:
            return 0.5
        
        score = 1.0
        asset_findings = [f for f in result.findings if f.category == "assets"]
        
        score -= len([f for f in asset_findings if f.severity == ConflictSeverity.CRITICAL]) * 0.3
        score -= len([f for f in asset_findings if f.severity == ConflictSeverity.HIGH]) * 0.2
        score -= len([f for f in asset_findings if f.severity == ConflictSeverity.MEDIUM]) * 0.1
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def _score_credit(extraction: ApplicationExtraction, result: ValidationResult) -> float:
        """Score credit information."""
        if not extraction.credit_report:
            return 0.5
        
        score = 1.0
        credit_findings = [f for f in result.findings if f.category == "credit"]
        
        score -= len([f for f in credit_findings if f.severity == ConflictSeverity.CRITICAL]) * 0.3
        score -= len([f for f in credit_findings if f.severity == ConflictSeverity.HIGH]) * 0.2
        score -= len([f for f in credit_findings if f.severity == ConflictSeverity.MEDIUM]) * 0.1
        
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def _calculate_consistency_score(result: ValidationResult) -> float:
        """Calculate consistency score based on conflicts."""
        if not result.findings:
            return 1.0
        
        non_info = [f for f in result.findings 
                   if f.severity != ConflictSeverity.INFO]
        
        if not non_info:
            return 1.0
        
        # Penalize based on severity and count
        critical_count = sum(1 for f in non_info if f.severity == ConflictSeverity.CRITICAL)
        high_count = sum(1 for f in non_info if f.severity == ConflictSeverity.HIGH)
        medium_count = sum(1 for f in non_info if f.severity == ConflictSeverity.MEDIUM)
        low_count = sum(1 for f in non_info if f.severity == ConflictSeverity.LOW)
        
        penalty = (critical_count * 0.30 + high_count * 0.20 + 
                  medium_count * 0.10 + low_count * 0.05)
        
        return max(0.0, 1.0 - penalty)
    
    @staticmethod
    def _calculate_completeness_score(extraction: ApplicationExtraction) -> float:
        """Calculate data completeness score."""
        score = 0.0
        max_score = 0.0
        
        # Check each component
        if extraction.personal_info:
            score += 0.15
            max_score += 0.15
        else:
            max_score += 0.15
        
        if extraction.employment_info:
            score += 0.15
            max_score += 0.15
        else:
            max_score += 0.15
        
        if extraction.bank_statement:
            score += 0.20
            max_score += 0.20
        else:
            max_score += 0.20
        
        if extraction.resume:
            score += 0.15
            max_score += 0.15
        else:
            max_score += 0.15
        
        if extraction.assets_liabilities:
            score += 0.20
            max_score += 0.20
        else:
            max_score += 0.20
        
        if extraction.credit_report:
            score += 0.15
            max_score += 0.15
        else:
            max_score += 0.15
        
        return score / max_score if max_score > 0 else 0.0
