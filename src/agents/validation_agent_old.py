"""
Data Validation Agent
Performs cross-document checks and conflict detection
"""
import logging
from typing import Dict, Any, List
from datetime import datetime

from ..core.base_agent import BaseAgent
from ..core.types import ExtractedData, ValidationReport, ValidationIssue


class DataValidationAgent(BaseAgent):
    """
    Validates extracted data for consistency and completeness
    Performs cross-document checks and identifies conflicts
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("DataValidationAgent", config)
        self.logger = logging.getLogger("DataValidationAgent")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted data
        
        Input:
            - application_id
            - extracted_data: ExtractedData object
        
        Output:
            - validation_report: ValidationReport object
        """
        start_time = datetime.now()
        application_id = input_data["application_id"]
        extracted_data = input_data["extracted_data"]
        
        self.logger.info(f"[{application_id}] Starting validation")
        
        issues = []
        cross_checks = {}
        
        # 1. Check data completeness
        completeness_issues = self._check_completeness(extracted_data)
        issues.extend(completeness_issues)
        
        # 2. Cross-document validation: Name consistency
        name_check = self._validate_name_consistency(extracted_data)
        cross_checks["name_consistency"] = name_check
        if not name_check["is_consistent"]:
            issues.append(ValidationIssue(
                severity="warning",
                category="inconsistency",
                field="full_name",
                message=f"Name inconsistency detected: {name_check['details']}",
                documents_affected=name_check["affected_documents"],
                suggested_resolution="Verify applicant identity with original documents"
            ))
        
        # 3. Income validation
        income_check = self._validate_income_data(extracted_data)
        cross_checks["income_validation"] = income_check
        if not income_check["is_valid"]:
            issues.append(ValidationIssue(
                severity="warning",
                category="inconsistency",
                field="income",
                message=income_check["message"],
                documents_affected=["bank_statement", "resume"],
                suggested_resolution=income_check["suggestion"]
            ))
        
        # 4. Debt-to-Income ratio check
        dti_check = self._validate_debt_to_income(extracted_data)
        cross_checks["debt_to_income"] = dti_check
        
        # 5. Address consistency
        address_check = self._validate_address_consistency(extracted_data)
        cross_checks["address_consistency"] = address_check
        if not address_check["is_consistent"]:
            issues.append(ValidationIssue(
                severity="info",
                category="inconsistency",
                field="address",
                message=address_check["message"],
                documents_affected=address_check["affected_documents"]
            ))
        
        # 6. Employment status validation
        employment_check = self._validate_employment_status(extracted_data)
        cross_checks["employment_status"] = employment_check
        
        # Calculate scores
        data_completeness_score = self._calculate_completeness_score(extracted_data)
        confidence_score = self._calculate_confidence_score(issues, cross_checks)
        
        # Determine if validation passed
        critical_issues = [i for i in issues if i.severity == "critical"]
        is_valid = len(critical_issues) == 0 and data_completeness_score >= 0.7
        
        validation_report = ValidationReport(
            is_valid=is_valid,
            issues=issues,
            cross_document_checks=cross_checks,
            data_completeness_score=data_completeness_score,
            confidence_score=confidence_score
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"[{application_id}] Validation completed - Issues: {len(issues)}, Valid: {is_valid}")
        
        return {
            "validation_report": validation_report,
            "validation_time": duration
        }
    
    def _check_completeness(self, data: ExtractedData) -> List[ValidationIssue]:
        """Check if all required fields are present"""
        issues = []
        
        # Check applicant info
        required_applicant_fields = ["full_name", "id_number", "nationality"]
        for field in required_applicant_fields:
            if field not in data.applicant_info or not data.applicant_info[field]:
                issues.append(ValidationIssue(
                    severity="critical",
                    category="missing_data",
                    field=f"applicant_info.{field}",
                    message=f"Required field '{field}' is missing",
                    documents_affected=["emirates_id"]
                ))
        
        # Check income data
        if not data.income_data.get("monthly_income"):
            issues.append(ValidationIssue(
                severity="critical",
                category="missing_data",
                field="income_data.monthly_income",
                message="Monthly income information is missing",
                documents_affected=["bank_statement"]
            ))
        
        return issues
    
    def _validate_name_consistency(self, data: ExtractedData) -> Dict[str, Any]:
        """Check if name is consistent across documents"""
        names = []
        affected_docs = []
        
        if data.applicant_info.get("full_name"):
            names.append(data.applicant_info["full_name"])
            affected_docs.append("emirates_id")
        
        if data.income_data.get("account_holder"):
            names.append(data.income_data["account_holder"])
            affected_docs.append("bank_statement")
        
        # Simple consistency check (could be more sophisticated)
        is_consistent = len(set(names)) <= 1 if names else True
        
        return {
            "is_consistent": is_consistent,
            "names_found": names,
            "affected_documents": affected_docs,
            "details": f"Found {len(set(names))} different name variations" if not is_consistent else "Names match"
        }
    
    def _validate_income_data(self, data: ExtractedData) -> Dict[str, Any]:
        """Validate income information"""
        monthly_income = data.income_data.get("monthly_income", 0)
        monthly_expenses = data.income_data.get("monthly_expenses", 0)
        
        if monthly_income == 0:
            return {
                "is_valid": False,
                "message": "No income data found",
                "suggestion": "Verify bank statement and employment records"
            }
        
        if monthly_expenses > monthly_income * 1.5:
            return {
                "is_valid": False,
                "message": f"Expenses ({monthly_expenses}) significantly exceed income ({monthly_income})",
                "suggestion": "Review expense calculations or verify income sources"
            }
        
        return {
            "is_valid": True,
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "net_monthly": monthly_income - monthly_expenses
        }
    
    def _validate_debt_to_income(self, data: ExtractedData) -> Dict[str, Any]:
        """Calculate and validate debt-to-income ratio"""
        monthly_income = data.income_data.get("monthly_income", 0)
        total_liabilities = data.assets_liabilities.get("total_liabilities", 0)
        
        if monthly_income == 0:
            return {"dti_ratio": None, "is_healthy": False}
        
        # Assume monthly debt payment is ~5% of total liabilities
        monthly_debt_payment = total_liabilities * 0.05
        dti_ratio = (monthly_debt_payment / monthly_income) * 100
        
        return {
            "dti_ratio": round(dti_ratio, 2),
            "monthly_debt_payment": monthly_debt_payment,
            "monthly_income": monthly_income,
            "is_healthy": dti_ratio < 43  # Standard threshold
        }
    
    def _validate_address_consistency(self, data: ExtractedData) -> Dict[str, Any]:
        """Check address consistency"""
        addresses = []
        affected_docs = []
        
        if data.applicant_info.get("address"):
            addresses.append(data.applicant_info["address"])
            affected_docs.append("emirates_id")
        
        # Could check credit report address too
        
        is_consistent = len(set(addresses)) <= 1
        
        return {
            "is_consistent": is_consistent,
            "addresses_found": addresses,
            "affected_documents": affected_docs,
            "message": "Addresses match" if is_consistent else "Address variations detected"
        }
    
    def _validate_employment_status(self, data: ExtractedData) -> Dict[str, Any]:
        """Validate employment status"""
        employment_status = data.employment_data.get("employment_status", "unknown")
        has_income = data.income_data.get("monthly_income", 0) > 0
        
        is_consistent = (employment_status == "employed" and has_income) or \
                       (employment_status == "unemployed" and not has_income)
        
        return {
            "employment_status": employment_status,
            "has_regular_income": has_income,
            "is_consistent": is_consistent
        }
    
    def _calculate_completeness_score(self, data: ExtractedData) -> float:
        """Calculate data completeness score (0.0 to 1.0)"""
        total_fields = 0
        filled_fields = 0
        
        # Count applicant info fields
        for key, value in data.applicant_info.items():
            total_fields += 1
            if value and value != "Not found":
                filled_fields += 1
        
        # Count income fields
        for key, value in data.income_data.items():
            total_fields += 1
            if value and value != 0:
                filled_fields += 1
        
        # Count employment fields
        for key, value in data.employment_data.items():
            total_fields += 1
            if value:
                filled_fields += 1
        
        return filled_fields / total_fields if total_fields > 0 else 0.0
    
    def _calculate_confidence_score(self, issues: List[ValidationIssue], 
                                    cross_checks: Dict[str, Any]) -> float:
        """Calculate overall confidence score"""
        base_score = 1.0
        
        # Deduct for issues
        for issue in issues:
            if issue.severity == "critical":
                base_score -= 0.3
            elif issue.severity == "warning":
                base_score -= 0.1
            elif issue.severity == "info":
                base_score -= 0.05
        
        # Boost for passing cross-checks
        if cross_checks.get("name_consistency", {}).get("is_consistent"):
            base_score += 0.05
        if cross_checks.get("address_consistency", {}).get("is_consistent"):
            base_score += 0.05
        
        return max(0.0, min(1.0, base_score))
