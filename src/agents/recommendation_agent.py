"""
Recommendation Agent - LangGraph Node 4

LANGGRAPH INTEGRATION:
    - Called by: langgraph_orchestrator._recommend_node()
    - Position: Fourth node in LangGraph StateGraph workflow
    - Input State: application_id, extracted_data, eligibility_result
    - Updates State: recommendation, stage=GENERATING_RECOMMENDATION
    - Next Node: explain_node (always)

PURPOSE:
    Production-grade recommendation generation with intelligent decision-making,
    precise rules and comprehensive program matching. Calculates financial support
    amount and matches to appropriate programs.

ARCHITECTURE:
    - Intelligent support amount calculation
    - Comprehensive program matching
    - Detailed reasoning for transparency
"""
import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime

from ..core.base_agent import BaseAgent
from ..core.types import ExtractedData, EligibilityResult, Recommendation, DecisionType


class RecommendationAgent(BaseAgent):
    """
    High-quality recommendation generation with:
    - Precise decision logic based on multiple factors
    - Intelligent support amount calculation
    - Comprehensive program matching
    - Detailed reasoning
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("RecommendationAgent", config)
        self.logger = logging.getLogger("RecommendationAgent")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive recommendation"""
        start_time = datetime.now()
        application_id = input_data["application_id"]
        extracted_data = input_data["extracted_data"]
        eligibility_result = input_data["eligibility_result"]
        
        self.logger.info(f"[{application_id}] Generating recommendation")
        
        # Step 1: Determine decision with detailed analysis
        decision, decision_factors = self._determine_decision_detailed(
            extracted_data, eligibility_result
        )
        
        # Step 2: Calculate financial support
        financial_support_amount = None
        financial_support_type = None
        
        if decision in [DecisionType.APPROVED, DecisionType.SOFT_DECLINED]:
            financial_support_amount, financial_support_type = self._calculate_support_precise(
                extracted_data, eligibility_result, decision
            )
        
        # Step 3: Match relevant programs
        programs = self._match_enablement_programs(
            extracted_data, eligibility_result, decision
        )
        
        # Step 4: Generate detailed reasoning
        reasoning = self._generate_detailed_reasoning(
            extracted_data, eligibility_result, decision,
            financial_support_amount, programs, decision_factors
        )
        
        # Step 5: Calculate confidence
        confidence = self._calculate_recommendation_confidence(
            eligibility_result, extracted_data
        )
        
        # Step 6: Extract key factors
        key_factors = self._extract_key_factors(
            extracted_data, eligibility_result, decision_factors
        )
        
        recommendation = Recommendation(
            decision=decision,
            financial_support_amount=financial_support_amount,
            financial_support_type=financial_support_type,
            economic_enablement_programs=programs,
            confidence_level=confidence,
            reasoning=reasoning,
            key_factors=key_factors
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(
            f"[{application_id}] Recommendation complete - "
            f"Decision: {decision.value}, "
            f"Support: {financial_support_amount or 0:.2f} AED, "
            f"Programs: {len(programs)}"
        )
        
        return {
            "recommendation": recommendation,
            "recommendation_time": duration
        }
    
    # ========== Decision Logic ==========
    
    def _determine_decision_detailed(self, data: ExtractedData, 
                                     eligibility: EligibilityResult) -> Tuple[DecisionType, Dict]:
        """Determine decision with detailed factor analysis"""
        # Safety check for None eligibility
        if eligibility is None:
            self.logger.error("Eligibility result is None")
            return DecisionType.DECLINED, {"error": "No eligibility data"}
        
        factors = {
            "eligibility_score": eligibility.eligibility_score if eligibility else 0.0,
            "has_regular_income": False,
            "income_adequate": False,
            "employment_stable": False,
            "debt_manageable": False,
            "financial_need": False
        }
        
        # Safety check for None data
        if data is None or data.income_data is None:
            self.logger.error("Extracted data or income data is None")
            return DecisionType.DECLINED, factors
        
        # Income analysis
        monthly_income = data.income_data.get("monthly_income", 0) if data.income_data else 0
        monthly_expenses = data.income_data.get("monthly_expenses", 0) if data.income_data else 0
        
        factors["has_regular_income"] = monthly_income >= 1000
        factors["income_adequate"] = monthly_income >= 3000
        
        # Financial gap analysis
        financial_gap = monthly_expenses - monthly_income
        factors["financial_need"] = financial_gap > 500
        
        # Employment analysis (with None checks)
        employment_status = data.employment_data.get("employment_status", "unknown") if data.employment_data else "unknown"
        years_experience = data.employment_data.get("years_of_experience", 0) if data.employment_data else 0
        
        factors["employment_stable"] = (
            employment_status == "employed" and 
            years_experience >= 1
        )
        
        # Debt analysis (with None checks)
        total_liabilities = data.assets_liabilities.get("total_liabilities", 0) if data.assets_liabilities else 0
        if monthly_income > 0:
            monthly_debt = total_liabilities * 0.05
            dti = (monthly_debt / monthly_income) * 100
            factors["debt_manageable"] = dti < 43
        else:
            factors["debt_manageable"] = total_liabilities < 10000
        
        # Decision logic (with None check for eligibility)
        score = eligibility.eligibility_score if eligibility else 0.0
        
        if score >= 0.70 and factors["has_regular_income"]:
            decision = DecisionType.APPROVED
        elif score >= 0.50 and factors["financial_need"]:
            decision = DecisionType.APPROVED
        elif score >= 0.35:
            decision = DecisionType.SOFT_DECLINED
        else:
            decision = DecisionType.DECLINED
        
        return decision, factors
    
    # ========== Support Amount Calculation ==========
    
    def _calculate_support_precise(self, data: ExtractedData, 
                                   eligibility: EligibilityResult,
                                   decision: DecisionType) -> Tuple[float, str]:
        """Calculate precise support amount based on multiple factors"""
        
        # Safety checks for None
        if data is None:
            return 0.0, "None"
        
        monthly_income = data.income_data.get("monthly_income", 0) if data.income_data else 0
        monthly_expenses = data.income_data.get("monthly_expenses", 0) if data.income_data else 0
        family_size = data.family_info.get("family_size", 1) if data.family_info else 1
        net_worth = data.assets_liabilities.get("net_worth", 0) if data.assets_liabilities else 0
        
        # Calculate base need
        financial_gap = max(0, monthly_expenses - monthly_income)
        
        # Family size multiplier
        family_multiplier = 1.0 + min((family_size - 1) * 0.15, 0.5)
        
        # Eligibility score multiplier (with None check)
        score_multiplier = eligibility.eligibility_score if eligibility else 0.0
        
        # Net worth adjustment (reduce support for those with significant assets)
        if net_worth > 50000:
            wealth_adjustment = 0.7
        elif net_worth > 20000:
            wealth_adjustment = 0.85
        else:
            wealth_adjustment = 1.0
        
        # Calculate base amount
        if decision == DecisionType.APPROVED:
            # Full support calculation
            base_amount = financial_gap * 0.75  # Cover 75% of gap
            adjusted_amount = base_amount * family_multiplier * score_multiplier * wealth_adjustment
            
            # Apply limits
            min_support = 500
            max_support = 5000
            final_amount = max(min_support, min(adjusted_amount, max_support))
            
            # Determine type
            if final_amount >= 3000:
                support_type = "Full Monthly Assistance"
            elif final_amount >= 1500:
                support_type = "Standard Support Package"
            else:
                support_type = "Basic Assistance"
                
        else:  # SOFT_DECLINED
            # Minimal support for soft decline
            base_amount = min(financial_gap * 0.3, 1500)
            final_amount = base_amount * family_multiplier
            support_type = "Transitional Support"
        
        return round(final_amount, 2), support_type
    
    # ========== Program Matching ==========
    
    def _match_enablement_programs(self, data: ExtractedData, 
                                   eligibility: EligibilityResult,
                                   decision: DecisionType) -> List[Dict[str, Any]]:
        """Match relevant enablement programs based on applicant profile"""
        programs = []
        
        employment_status = data.employment_data.get("employment_status", "unknown")
        years_experience = data.employment_data.get("years_of_experience", 0)
        monthly_income = data.income_data.get("monthly_income", 0)
        net_worth = data.assets_liabilities.get("net_worth", 0)
        
        # Priority 1: Employment programs (if unemployed or low income)
        if employment_status in ["unemployed", "unknown"] or monthly_income < 2000:
            programs.append({
                "program_name": "UAE Job Placement Service",
                "name": "UAE Job Placement Service",
                "category": "employment",
                "description": "Connect with verified UAE employers actively hiring. One-on-one job matching based on skills and experience.",
                "duration": "Ongoing support until placement",
                "eligibility": "All applicants",
                "benefits": "Job interviews within 2 weeks, resume optimization, interview coaching",
                "priority": "high"
            })
        
        # Priority 2: Skills development (if low experience or low income)
        if years_experience < 3 or monthly_income < 3000:
            programs.append({
                "program_name": "Professional Skills Bootcamp",
                "name": "Professional Skills Bootcamp",
                "program_name": "Professional Skills Bootcamp",
                "name": "Professional Skills Bootcamp",
                "category": "upskilling",
                "description": "Intensive training in high-demand skills: Digital Marketing, Customer Service Excellence, Data Entry, Technical Support.",
                "duration": "8-12 weeks (full-time)",
                "eligibility": "High school education or equivalent",
                "benefits": "Industry certification, job placement assistance, networking events",
                "priority": "high"
            })
        
        # Priority 3: Career counseling (always relevant)
        programs.append({
            "program_name": "Career Development Counseling",
                "name": "Career Development Counseling",
            "program_name": "Career Development Counseling",
                "name": "Career Development Counseling",
            "category": "counseling",
            "description": "Personalized career planning with certified counselors. Identify strengths, set goals, create action plans.",
            "duration": "4-6 sessions over 3 months",
            "eligibility": "All applicants",
            "benefits": "Personalized career roadmap, skills assessment, goal tracking",
            "priority": "medium"
        })
        
        # Priority 4: Financial literacy (if poor financial management)
        monthly_expenses = data.income_data.get("monthly_expenses", 0)
        if monthly_expenses > monthly_income * 1.2:
            programs.append({
                "program_name": "Financial Wellness Program",
                "name": "Financial Wellness Program",
                "program_name": "Financial Wellness Program",
                "name": "Financial Wellness Program",
                "category": "financial_education",
                "description": "Learn budgeting, debt management, savings strategies, and financial planning for UAE residents.",
                "duration": "4-week workshop series",
                "eligibility": "All applicants",
                "benefits": "Personal budget template, debt reduction plan, savings calculator",
                "priority": "high"
            })
        else:
            programs.append({
                "program_name": "Financial Planning Workshop",
                "name": "Financial Planning Workshop",
                "program_name": "Financial Planning Workshop",
                "name": "Financial Planning Workshop",
                "category": "financial_education",
                "description": "Basic financial literacy: budgeting, saving, and UAE financial services.",
                "duration": "2-day workshop",
                "eligibility": "All applicants",
                "benefits": "Financial planning toolkit, banking guidance",
                "priority": "low"
            })
        
        # Priority 5: Entrepreneurship (if experienced and some capital)
        if years_experience >= 5 and net_worth > 10000:
            programs.append({
                "program_name": "Small Business Development Program",
                "name": "Small Business Development Program",
                "category": "entrepreneurship",
                "description": "Complete business startup support: business planning, licensing guidance, marketing, financial management.",
                "duration": "6-month incubator program",
                "eligibility": "5+ years experience, business concept, minimum capital",
                "benefits": "Mentor assigned, license support, networking, seed funding opportunities",
                "priority": "medium"
            })
        
        # Priority 6: Education advancement (if young or low education)
        # Could be inferred from employment data
        if years_experience < 2:
            programs.append({
                "program_name": "Higher Education Scholarship Program",
                "name": "Higher Education Scholarship Program",
                "category": "education",
                "description": "Scholarships for vocational training, diploma programs, and university degrees in high-demand fields.",
                "duration": "Varies by program (6 months - 4 years)",
                "eligibility": "Under 35 years, UAE resident, academic requirements",
                "benefits": "Tuition coverage, study materials, stipend available",
                "priority": "medium"
            })
        
        # Priority 7: Mental health & wellbeing (if high stress indicators)
        if monthly_expenses > monthly_income * 1.5 or employment_status == "unemployed":
            programs.append({
                "program_name": "Wellbeing & Resilience Support",
                "name": "Wellbeing & Resilience Support",
                "category": "mental_health",
                "description": "Free counseling services, stress management workshops, peer support groups.",
                "duration": "Ongoing",
                "eligibility": "All applicants",
                "benefits": "Confidential counseling, coping strategies, community support",
                "priority": "medium"
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        programs.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return programs[:5]  # Return top 5 most relevant programs
    
    # ========== Reasoning Generation ==========
    
    def _generate_detailed_reasoning(self, data: ExtractedData, 
                                    eligibility: EligibilityResult,
                                    decision: DecisionType,
                                    support_amount: float,
                                    programs: List[Dict],
                                    factors: Dict) -> str:
        """Generate comprehensive reasoning for the decision"""
        
        reasoning_parts = []
        
        # Opening statement (with None check)
        if decision == DecisionType.APPROVED:
            score_text = f" (Eligibility Score: {eligibility.eligibility_score:.2%})" if eligibility else ""
            reasoning_parts.append(f" **Application APPROVED**{score_text}")
        elif decision == DecisionType.SOFT_DECLINED:
            score_text = f" (Eligibility Score: {eligibility.eligibility_score:.2%})" if eligibility else ""
            reasoning_parts.append(f" **Application SOFT DECLINED**{score_text}")
        else:
            score_text = f" (Eligibility Score: {eligibility.eligibility_score:.2%})" if eligibility else ""
            reasoning_parts.append(f" **Application DECLINED**{score_text}")
        
        reasoning_parts.append("")
        
        # Financial analysis (with None checks)
        monthly_income = data.income_data.get("monthly_income", 0) if data and data.income_data else 0
        monthly_expenses = data.income_data.get("monthly_expenses", 0) if data and data.income_data else 0
        gap = monthly_expenses - monthly_income
        
        reasoning_parts.append("**Financial Analysis:**")
        reasoning_parts.append(f"- Monthly Income: AED {monthly_income:,.2f}")
        reasoning_parts.append(f"- Monthly Expenses: AED {monthly_expenses:,.2f}")
        
        if gap > 0:
            reasoning_parts.append(f"- **Financial Gap: AED {gap:,.2f}** (expenses exceed income)")
        else:
            reasoning_parts.append(f"- Financial Surplus: AED {abs(gap):,.2f}")
        
        reasoning_parts.append("")
        
        # Support decision
        if support_amount:
            reasoning_parts.append(f"**Financial Support: AED {support_amount:,.2f}/month**")
            reasoning_parts.append(f"This amount is calculated to help bridge {support_amount/gap*100 if gap > 0 else 0:.0f}% of your financial gap while encouraging financial independence.")
            reasoning_parts.append("")
        
        # Employment status
        employment_status = data.employment_data.get("employment_status", "unknown")
        years_exp = data.employment_data.get("years_of_experience", 0)
        
        reasoning_parts.append("**Employment Status:**")
        if employment_status == "employed":
            reasoning_parts.append(f" Currently employed ({years_exp} years experience)")
        elif employment_status == "unemployed":
            reasoning_parts.append("Currently unemployed - employment support recommended")
        else:
            reasoning_parts.append(" Employment status unclear")
        
        reasoning_parts.append("")
        
        # Key factors
        reasoning_parts.append("**Decision Factors:**")
        if factors["has_regular_income"]:
            reasoning_parts.append(" Has regular income stream")
        if factors["employment_stable"]:
            reasoning_parts.append(" Stable employment history")
        if factors["debt_manageable"]:
            reasoning_parts.append(" Debt levels are manageable")
        if factors["financial_need"]:
            reasoning_parts.append(" Clear financial need demonstrated")
        
        reasoning_parts.append("")
        
        # Programs
        if programs:
            reasoning_parts.append(f"**Recommended Programs ({len(programs)}):**")
            for program in programs[:3]:
                reasoning_parts.append(f"- **{program['name']}**: {program['description'][:100]}...")
        
        reasoning_parts.append("")
        
        # Next steps
        if decision == DecisionType.APPROVED:
            reasoning_parts.append("**Next Steps:** Support will be disbursed monthly. Participation in at least one enablement program is encouraged.")
        elif decision == DecisionType.SOFT_DECLINED:
            reasoning_parts.append("**Next Steps:** Complete recommended programs and reapply in 3-6 months with improved financial stability.")
        else:
            reasoning_parts.append("**Next Steps:** Focus on employment and income improvement. Reapply after 6 months.")
        
        return "\n".join(reasoning_parts)
    
    # ========== Confidence & Key Factors ==========
    
    def _calculate_recommendation_confidence(self, eligibility: EligibilityResult,
                                            data: ExtractedData) -> float:
        """Calculate confidence in recommendation"""
        # Safety check
        if eligibility is None:
            return 0.0
        
        confidence = eligibility.eligibility_score
        
        # Boost confidence if data is complete (with None checks)
        has_income = data.income_data.get("monthly_income", 0) > 0 if data and data.income_data else False
        has_employment = data.employment_data.get("employment_status") in ["employed", "unemployed"] if data and data.employment_data else False
        has_id = data.applicant_info.get("id_number") not in [None, "Not found"] if data and data.applicant_info else False
        
        if has_income and has_employment and has_id:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def _extract_key_factors(self, data: ExtractedData, 
                            eligibility: EligibilityResult,
                            factors: Dict) -> List[str]:
        """Extract key decision factors"""
        # Safety check
        if eligibility is None or data is None:
            return ["Insufficient data for analysis"]
        
        key_factors = []
        
        # Positive factors (with None check)
        if eligibility.eligibility_score >= 0.6:
            key_factors.append(f"Strong eligibility score: {eligibility.eligibility_score:.0%}")
        
        if factors.get("has_regular_income") and data.income_data:
            income = data.income_data.get("monthly_income", 0)
            key_factors.append(f"Regular income: AED {income:,.2f}/month")
        
        if factors.get("employment_stable") and data.employment_data:
            years = data.employment_data.get("years_of_experience", 0)
            key_factors.append(f"Stable employment: {years} years experience")
        
        # Risk factors
        if factors["financial_need"]:
            key_factors.append("Demonstrated financial need")
        
        if not factors["debt_manageable"]:
            key_factors.append("High debt-to-income ratio")
        
        return key_factors[:5]
