"""
Data Validation Agent - LangGraph Node 2

LANGGRAPH INTEGRATION:
    - Called by: langgraph_orchestrator._validate_node()
    - Position: Second node in LangGraph StateGraph workflow
    - Input State: application_id, extracted_data, applicant_name
    - Updates State: validation_report, stage=VALIDATING
    - Next Node: eligibility_node (if valid) OR END (if critical errors)
    - Conditional Routing: _should_continue_after_validation()

PURPOSE:
    Production-grade data validation with:
    - Comprehensive validation with precise rules
    - Intelligent cross-checks and fuzzy name matching
    - Completeness scoring and confidence calculation
    - Critical error detection for early termination

ARCHITECTURE PATTERN:
    Pure domain logic agent wrapped by LangGraph node function.
    Validation results determine workflow routing via conditional edges.
"""
import logging
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime
from difflib import SequenceMatcher

from ..core.base_agent import BaseAgent
from ..core.types import ExtractedData, ValidationReport, ValidationIssue


class DataValidationAgent(BaseAgent):
    """
    High-quality data validation with:
    - Precise field validation
    - Intelligent name matching (fuzzy logic)
    - Financial data verification
    - Cross-document consistency checks
    - Completeness scoring
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("DataValidationAgent", config)
        self.logger = logging.getLogger("DataValidationAgent")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate extracted data comprehensively"""
        start_time = datetime.now()
        application_id = input_data.get("application_id", "unknown")
        extracted_data = input_data.get("extracted_data")
        
        # Check if extracted_data is None
        if extracted_data is None:
            self.logger.warning(f"[{application_id}] Extracted data is None, skipping validation")
            return {
                "validation_report": ValidationReport(
                    is_valid=False,
                    completeness_score=0.0,
                    confidence_score=0.0,
                    issues=["No extracted data available for validation"],
                    cross_document_checks={}
                ),
                "validation_time": 0.0
            }
        
        applicant_name_from_application = input_data.get("applicant_name")  # Name from application creation
        
        self.logger.info(f"[{application_id}] Starting comprehensive validation")
        
        issues = []
        cross_checks = {}
        
        # CRITICAL: Validate applicant name matches documents
        if applicant_name_from_application:
            name_verification_issues, name_verification = self._verify_applicant_identity(
                applicant_name_from_application, extracted_data
            )
            issues.extend(name_verification_issues)
            cross_checks["applicant_identity_verification"] = name_verification
        
        # 1. Validate applicant identity
        identity_issues, identity_check = self._validate_identity(extracted_data)
        issues.extend(identity_issues)
        cross_checks["identity"] = identity_check
        
        # 2. Validate financial data
        financial_issues, financial_check = self._validate_financial_data(extracted_data)
        issues.extend(financial_issues)
        cross_checks["financial"] = financial_check
        
        # 3. Validate employment data
        employment_issues, employment_check = self._validate_employment(extracted_data)
        issues.extend(employment_issues)
        cross_checks["employment"] = employment_check
        
        # 4. Cross-document name consistency (fuzzy matching)
        name_issues, name_check = self._validate_name_consistency_fuzzy(extracted_data)
        issues.extend(name_issues)
        cross_checks["name_consistency"] = name_check
        
        # 5. Debt-to-income validation
        dti_issues, dti_check = self._validate_debt_to_income(extracted_data)
        issues.extend(dti_issues)
        cross_checks["debt_to_income"] = dti_check
        
        # 6. Data integrity checks
        integrity_issues = self._check_data_integrity(extracted_data)
        issues.extend(integrity_issues)
        
        # Calculate scores
        completeness_score = self._calculate_completeness_score(extracted_data)
        confidence_score = self._calculate_confidence_score(issues, completeness_score)
        
        # Determine validation result
        critical_issues = [i for i in issues if i.severity == "critical"]
        is_valid = len(critical_issues) == 0 and completeness_score >= 0.60
        
        validation_report = ValidationReport(
            is_valid=is_valid,
            issues=issues,
            cross_document_checks=cross_checks,
            data_completeness_score=completeness_score,
            confidence_score=confidence_score
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(
            f"[{application_id}] Validation complete - "
            f"Valid: {is_valid}, Issues: {len(issues)} "
            f"(Critical: {len(critical_issues)}), "
            f"Completeness: {completeness_score:.2%}"
        )
        
        return {
            "validation_report": validation_report,
            "validation_time": duration
        }
    
    # ========== Identity Validation ==========
    
    def _verify_applicant_identity(self, application_name: str, 
                                   data: ExtractedData) -> Tuple[List[ValidationIssue], Dict]:
        """CRITICAL: Verify the person who applied is the same as in documents"""
        issues = []
        check_result = {"identity_verified": False, "details": {}}
        
        # Get name from documents
        document_names = []
        
        if data.applicant_info.get("full_name"):
            document_names.append(("emirates_id", data.applicant_info["full_name"]))
        
        if data.income_data.get("account_holder"):
            document_names.append(("bank_statement", data.income_data["account_holder"]))
        
        if data.employment_data.get("full_name"):
            document_names.append(("resume", data.employment_data["full_name"]))
        
        if not document_names:
            issues.append(ValidationIssue(
                severity="critical",
                category="missing_data",
                field="applicant_identity",
                message="No name found in any uploaded documents",
                documents_affected=["all"],
                suggested_resolution="Ensure documents are readable and contain applicant information"
            ))
            return issues, check_result
        
        # Check if application name matches ANY document
        match_found = False
        similarity_scores = {}
        
        for doc_type, doc_name in document_names:
            similarity = self._name_similarity(application_name, doc_name)
            similarity_scores[doc_type] = {
                "name_in_document": doc_name,
                "similarity": similarity
            }
            
            if similarity >= 0.75:  # 75% match threshold
                match_found = True
        
        check_result["details"] = {
            "application_name": application_name,
            "document_names": dict(document_names),
            "similarity_scores": similarity_scores,
            "identity_verified": match_found
        }
        
        if not match_found:
            # CRITICAL SECURITY ISSUE
            best_match = max(similarity_scores.items(), key=lambda x: x[1]["similarity"])
            best_doc, best_score_data = best_match
            
            issues.append(ValidationIssue(
                severity="critical",
                category="identity_mismatch",
                field="applicant_identity",
                message=f"IDENTITY MISMATCH: Application name '{application_name}' does not match documents. Best match: '{best_score_data['name_in_document']}' from {best_doc} (similarity: {best_score_data['similarity']:.0%})",
                documents_affected=[doc for doc, _ in document_names],
                suggested_resolution="VERIFY APPLICANT IDENTITY - Documents may belong to a different person. This requires manual review and re-submission with correct documents."
            ))
        else:
            check_result["identity_verified"] = True
            self.logger.info(f"Identity verified: {application_name} matches documents")
        
        return issues, check_result
    
    def _validate_identity(self, data: ExtractedData) -> Tuple[List[ValidationIssue], Dict]:
        """Validate applicant identity fields"""
        issues = []
        check_result = {"passed": True, "details": {}}
        
        # Full name
        name = data.applicant_info.get("full_name")
        if not name or name == "Not found":
            issues.append(ValidationIssue(
                severity="critical",
                category="missing_data",
                field="applicant_info.full_name",
                message="Applicant full name is required",
                documents_affected=["emirates_id"],
                suggested_resolution="Verify Emirates ID is readable and uploaded correctly"
            ))
            check_result["passed"] = False
        else:
            check_result["details"]["name"] = name
        
        # ID Number
        id_number = data.applicant_info.get("id_number")
        if not id_number or id_number == "Not found":
            issues.append(ValidationIssue(
                severity="critical",
                category="missing_data",
                field="applicant_info.id_number",
                message="Emirates ID number is required",
                documents_affected=["emirates_id"],
                suggested_resolution="Ensure ID number is clearly visible in uploaded image"
            ))
            check_result["passed"] = False
        else:
            # Validate ID format
            if not self._is_valid_emirates_id(id_number):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="format_error",
                    field="applicant_info.id_number",
                    message=f"ID number format may be incorrect: {id_number}",
                    documents_affected=["emirates_id"],
                    suggested_resolution="Verify ID number follows UAE format (15 digits or 784-YYYY-XXXXXXX-X)"
                ))
            check_result["details"]["id_number"] = id_number
        
        # Date of birth
        dob = data.applicant_info.get("date_of_birth")
        if not dob or dob == "Not found":
            issues.append(ValidationIssue(
                severity="warning",
                category="missing_data",
                field="applicant_info.date_of_birth",
                message="Date of birth not extracted",
                documents_affected=["emirates_id"]
            ))
        else:
            # Validate age (18-100 years old)
            age = self._calculate_age(dob)
            if age and (age < 18 or age > 100):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="inconsistency",
                    field="applicant_info.date_of_birth",
                    message=f"Unusual age detected: {age} years",
                    documents_affected=["emirates_id"],
                    suggested_resolution="Verify date of birth is correct"
                ))
            check_result["details"]["age"] = age
        
        # Nationality
        nationality = data.applicant_info.get("nationality")
        if nationality and "UAE" in nationality.upper():
            check_result["details"]["is_uae_national"] = True
        
        return issues, check_result
    
    def _is_valid_emirates_id(self, id_number: str) -> bool:
        """Validate Emirates ID format"""
        # Remove spaces and dashes
        cleaned = id_number.replace("-", "").replace(" ", "")
        
        # Should be 15 digits
        if len(cleaned) == 15 and cleaned.isdigit():
            return True
        
        # Or 784-YYYY-XXXXXXX-X format
        pattern = r'784-\d{4}-\d{7}-\d'
        if re.match(pattern, id_number):
            return True
        
        return False
    
    def _calculate_age(self, dob_str: str) -> int:
        """Calculate age from date of birth string"""
        try:
            # Try different date formats
            for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"]:
                try:
                    dob = datetime.strptime(dob_str, fmt)
                    today = datetime.now()
                    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                    return age
                except ValueError:
                    continue
        except:
            pass
        return None
    
    # ========== Financial Data Validation ==========
    
    def _validate_financial_data(self, data: ExtractedData) -> Tuple[List[ValidationIssue], Dict]:
        """Validate financial data for consistency"""
        issues = []
        check_result = {"passed": True, "details": {}}
        
        # Monthly income
        income = data.income_data.get("monthly_income", 0)
        if income <= 0:
            issues.append(ValidationIssue(
                severity="critical",
                category="missing_data",
                field="income_data.monthly_income",
                message="Monthly income must be provided",
                documents_affected=["bank_statement"],
                suggested_resolution="Verify bank statement shows income transactions"
            ))
            check_result["passed"] = False
        elif income < 1000:
            issues.append(ValidationIssue(
                severity="warning",
                category="inconsistency",
                field="income_data.monthly_income",
                message=f"Unusually low monthly income: AED {income:.2f}",
                documents_affected=["bank_statement"],
                suggested_resolution="Verify income calculation is correct"
            ))
        elif income > 100000:
            issues.append(ValidationIssue(
                severity="info",
                category="inconsistency",
                field="income_data.monthly_income",
                message=f"High monthly income: AED {income:.2f}",
                documents_affected=["bank_statement"]
            ))
        
        check_result["details"]["monthly_income"] = income
        
        # Monthly expenses
        expenses = data.income_data.get("monthly_expenses", 0)
        check_result["details"]["monthly_expenses"] = expenses
        
        # Income-expense validation
        if expenses > 0:
            if expenses > income * 2:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="inconsistency",
                    field="income_data",
                    message=f"Expenses (AED {expenses:.2f}) are {expenses/income:.1f}x income (AED {income:.2f})",
                    documents_affected=["bank_statement"],
                    suggested_resolution="Review expense calculation or verify additional income sources"
                ))
            
            check_result["details"]["savings_rate"] = ((income - expenses) / income * 100) if income > 0 else 0
        
        # Assets and liabilities
        total_assets = data.assets_liabilities.get("total_assets", 0)
        total_liabilities = data.assets_liabilities.get("total_liabilities", 0)
        net_worth = data.assets_liabilities.get("net_worth", 0)
        
        # Verify net worth calculation
        calculated_net_worth = total_assets - total_liabilities
        if abs(calculated_net_worth - net_worth) > 100:
            issues.append(ValidationIssue(
                severity="warning",
                category="inconsistency",
                field="assets_liabilities.net_worth",
                message=f"Net worth calculation mismatch: Reported {net_worth}, calculated {calculated_net_worth}",
                documents_affected=["assets_liabilities"],
                suggested_resolution="Verify asset and liability totals"
            ))
        
        check_result["details"]["total_assets"] = total_assets
        check_result["details"]["total_liabilities"] = total_liabilities
        check_result["details"]["net_worth"] = net_worth
        
        return issues, check_result
    
    # ========== Employment Validation ==========
    
    def _validate_employment(self, data: ExtractedData) -> Tuple[List[ValidationIssue], Dict]:
        """Validate employment data"""
        issues = []
        check_result = {"passed": True, "details": {}}
        
        employment_status = data.employment_data.get("employment_status", "unknown")
        income = data.income_data.get("monthly_income", 0)
        
        check_result["details"]["employment_status"] = employment_status
        
        # Check consistency between employment status and income
        if employment_status == "employed" and income < 1000:
            issues.append(ValidationIssue(
                severity="warning",
                category="inconsistency",
                field="employment_data.employment_status",
                message="Marked as employed but income is very low",
                documents_affected=["resume", "bank_statement"],
                suggested_resolution="Verify employment status and income sources"
            ))
        
        if employment_status == "unemployed" and income > 5000:
            issues.append(ValidationIssue(
                severity="info",
                category="inconsistency",
                field="employment_data.employment_status",
                message="Marked as unemployed but has significant income",
                documents_affected=["resume", "bank_statement"],
                suggested_resolution="Check for self-employment or other income sources"
            ))
        
        # Years of experience
        years_exp = data.employment_data.get("years_of_experience", 0)
        check_result["details"]["years_of_experience"] = years_exp
        
        return issues, check_result
    
    # ========== Name Consistency (Fuzzy Matching) ==========
    
    def _validate_name_consistency_fuzzy(self, data: ExtractedData) -> Tuple[List[ValidationIssue], Dict]:
        """Validate name consistency across documents using fuzzy matching"""
        issues = []
        names = {}
        
        # Collect names from different sources
        if data.applicant_info.get("full_name"):
            names["emirates_id"] = data.applicant_info["full_name"]
        
        if data.income_data.get("account_holder"):
            names["bank_statement"] = data.income_data["account_holder"]
        
        if data.employment_data.get("full_name"):
            names["resume"] = data.employment_data["full_name"]
        
        check_result = {
            "names_found": names,
            "is_consistent": True,
            "similarity_scores": {}
        }
        
        # If we have multiple names, check similarity
        if len(names) >= 2:
            name_list = list(names.items())
            
            for i in range(len(name_list)):
                for j in range(i + 1, len(name_list)):
                    doc1, name1 = name_list[i]
                    doc2, name2 = name_list[j]
                    
                    similarity = self._name_similarity(name1, name2)
                    check_result["similarity_scores"][f"{doc1}_vs_{doc2}"] = similarity
                    
                    if similarity < 0.7:  # 70% similarity threshold
                        issues.append(ValidationIssue(
                            severity="warning",
                            category="inconsistency",
                            field="full_name",
                            message=f"Name mismatch: '{name1}' vs '{name2}' (similarity: {similarity:.0%})",
                            documents_affected=[doc1, doc2],
                            suggested_resolution="Verify applicant identity across all documents"
                        ))
                        check_result["is_consistent"] = False
        
        return issues, check_result
    
    def _name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names (0.0 to 1.0)"""
        # Normalize names
        n1 = name1.lower().strip()
        n2 = name2.lower().strip()
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, n1, n2).ratio()
    
    # ========== Debt-to-Income Validation ==========
    
    def _validate_debt_to_income(self, data: ExtractedData) -> Tuple[List[ValidationIssue], Dict]:
        """Validate debt-to-income ratio"""
        issues = []
        
        income = data.income_data.get("monthly_income", 0)
        liabilities = data.assets_liabilities.get("total_liabilities", 0)
        
        if income == 0:
            return issues, {"dti_ratio": None, "is_healthy": None}
        
        # Estimate monthly debt payment (assume 5% of total liabilities)
        monthly_debt = liabilities * 0.05
        dti_ratio = (monthly_debt / income) * 100
        
        check_result = {
            "monthly_income": income,
            "total_liabilities": liabilities,
            "estimated_monthly_debt": monthly_debt,
            "dti_ratio": round(dti_ratio, 2),
            "is_healthy": dti_ratio < 43
        }
        
        if dti_ratio > 43:
            issues.append(ValidationIssue(
                severity="warning",
                category="financial_risk",
                field="debt_to_income",
                message=f"High debt-to-income ratio: {dti_ratio:.1f}% (healthy threshold: <43%)",
                documents_affected=["bank_statement", "assets_liabilities"],
                suggested_resolution="Consider debt consolidation or income improvement programs"
            ))
        
        return issues, check_result
    
    # ========== Data Integrity ==========
    
    def _check_data_integrity(self, data: ExtractedData) -> List[ValidationIssue]:
        """Check for data integrity issues"""
        issues = []
        
        # Check for obviously wrong values
        if data.assets_liabilities.get("total_assets", 0) < 0:
            issues.append(ValidationIssue(
                severity="critical",
                category="data_error",
                field="assets_liabilities.total_assets",
                message="Assets cannot be negative",
                documents_affected=["assets_liabilities"]
            ))
        
        if data.income_data.get("monthly_income", 0) < 0:
            issues.append(ValidationIssue(
                severity="critical",
                category="data_error",
                field="income_data.monthly_income",
                message="Income cannot be negative",
                documents_affected=["bank_statement"]
            ))
        
        return issues
    
    # ========== Scoring ==========
    
    def _calculate_completeness_score(self, data: ExtractedData) -> float:
        """Calculate data completeness score"""
        total_weight = 0
        filled_weight = 0
        
        # Critical fields (higher weight)
        critical_fields = {
            ("applicant_info", "full_name"): 10,
            ("applicant_info", "id_number"): 10,
            ("applicant_info", "nationality"): 5,
            ("applicant_info", "date_of_birth"): 5,
            ("income_data", "monthly_income"): 10,
            ("income_data", "account_holder"): 5,
        }
        
        # Important fields (medium weight)
        important_fields = {
            ("income_data", "monthly_expenses"): 7,
            ("income_data", "average_balance"): 5,
            ("employment_data", "employment_status"): 7,
            ("employment_data", "years_of_experience"): 5,
            ("assets_liabilities", "total_assets"): 5,
            ("assets_liabilities", "total_liabilities"): 5,
        }
        
        all_fields = {**critical_fields, **important_fields}
        
        for (category, field), weight in all_fields.items():
            total_weight += weight
            
            value = getattr(data, category).get(field)
            if value and value != "Not found" and value != 0:
                filled_weight += weight
        
        return filled_weight / total_weight if total_weight > 0 else 0.0
    
    def _calculate_confidence_score(self, issues: List[ValidationIssue], 
                                    completeness: float) -> float:
        """Calculate overall confidence score"""
        # Start with completeness score
        score = completeness
        
        # Deduct for issues
        for issue in issues:
            if issue.severity == "critical":
                score -= 0.15
            elif issue.severity == "warning":
                score -= 0.05
            elif issue.severity == "info":
                score -= 0.01
        
        return max(0.0, min(1.0, score))
