"""
Recommendation Agent
Uses LLM reasoning to generate final recommendations for:
1. Financial support approval/decline
2. Economic enablement programs (upskilling, job matching, career counseling)
"""
import logging
from typing import Dict, Any
from datetime import datetime

from ..core.base_agent import BaseAgent
from ..core.types import ExtractedData, EligibilityResult, Recommendation, DecisionType


class RecommendationAgent(BaseAgent):
    """
    Generates final recommendations using LLM reasoning
    Considers eligibility results and applicant profile
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("RecommendationAgent", config)
        self.logger = logging.getLogger("RecommendationAgent")
        
        # LLM service (will be injected)
        self.llm_service = None
        
        # Economic enablement programs database
        self.enablement_programs = self._load_enablement_programs()
    
    def register_llm_service(self, llm_service):
        """Register LLM service"""
        self.llm_service = llm_service
        self.logger.info("LLM service registered")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate recommendation
        
        Input:
            - application_id
            - extracted_data: ExtractedData
            - eligibility_result: EligibilityResult
        
        Output:
            - recommendation: Recommendation
        """
        start_time = datetime.now()
        application_id = input_data["application_id"]
        extracted_data = input_data["extracted_data"]
        eligibility_result = input_data["eligibility_result"]
        
        self.logger.info(f"[{application_id}] Generating recommendation")
        
        # Step 1: Determine decision type
        decision = self._determine_decision(eligibility_result)
        
        # Step 2: Calculate financial support amount (if approved)
        financial_support_amount = None
        financial_support_type = None
        
        if decision in [DecisionType.APPROVED]:
            financial_support_amount, financial_support_type = self._calculate_support_amount(
                extracted_data, eligibility_result
            )
        
        # Step 3: Recommend economic enablement programs
        enablement_programs = self._recommend_enablement_programs(
            extracted_data, eligibility_result
        )
        
        # Step 4: Generate reasoning using LLM
        reasoning, key_factors = await self._generate_llm_reasoning(
            extracted_data, eligibility_result, decision,
            financial_support_amount, enablement_programs
        )
        
        # Step 5: Calculate confidence
        confidence_level = self._calculate_confidence(eligibility_result)
        
        recommendation = Recommendation(
            decision=decision,
            financial_support_amount=financial_support_amount,
            financial_support_type=financial_support_type,
            economic_enablement_programs=enablement_programs,
            confidence_level=confidence_level,
            reasoning=reasoning,
            key_factors=key_factors
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"[{application_id}] Recommendation complete - Decision: {decision.value}")
        
        return {
            "recommendation": recommendation,
            "recommendation_time": duration
        }
    
    def _determine_decision(self, eligibility_result: EligibilityResult) -> DecisionType:
        """Determine approval decision based on eligibility"""
        score = eligibility_result.eligibility_score
        
        if score >= 0.75:
            return DecisionType.APPROVED
        elif score >= 0.6:
            return DecisionType.APPROVED  # Borderline but approve
        elif score >= 0.4:
            return DecisionType.SOFT_DECLINED  # Encourage reapplication with improvements
        else:
            return DecisionType.DECLINED
    
    def _calculate_support_amount(self, extracted_data: ExtractedData,
                                  eligibility_result: EligibilityResult) -> tuple:
        """Calculate financial support amount"""
        monthly_income = extracted_data.income_data.get("monthly_income", 0)
        monthly_expenses = extracted_data.income_data.get("monthly_expenses", 0)
        family_size = extracted_data.family_info.get("family_size", 1)
        
        # Base support calculation
        monthly_gap = max(0, monthly_expenses - monthly_income)
        
        # Adjust for family size
        family_factor = 1.0 + (family_size - 1) * 0.2
        
        # Calculate support
        base_amount = min(monthly_gap * 0.7, 3000)  # Cover 70% of gap, max 3000 AED
        adjusted_amount = base_amount * family_factor
        
        # Determine support type
        if adjusted_amount >= 2000:
            support_type = "Full Financial Assistance"
        elif adjusted_amount >= 1000:
            support_type = "Partial Financial Assistance"
        else:
            support_type = "Minimal Support Package"
        
        return round(adjusted_amount, 2), support_type
    
    def _recommend_enablement_programs(self, extracted_data: ExtractedData,
                                      eligibility_result: EligibilityResult) -> list:
        """Recommend economic enablement programs"""
        programs = []
        
        employment_status = extracted_data.employment_data.get("employment_status", "")
        years_experience = extracted_data.employment_data.get("years_of_experience", 0)
        skills = extracted_data.employment_data.get("skills", [])
        education = extracted_data.employment_data.get("education", [])
        
        # Job matching
        if employment_status in ["unemployed", "unknown"]:
            programs.append({
                "program_name": "Job Matching Service",
                "category": "employment",
                "description": "Connect with employers seeking candidates with your skills",
                "duration": "Ongoing",
                "priority": "high"
            })
        
        # Upskilling
        if years_experience < 3 or not skills:
            programs.append({
                "program_name": "Professional Skills Development",
                "category": "upskilling",
                "description": "Technical and soft skills training programs",
                "duration": "3-6 months",
                "priority": "high"
            })
        
        # Career counseling (always recommend)
        programs.append({
            "program_name": "Career Counseling & Planning",
            "category": "counseling",
            "description": "One-on-one career guidance and development planning",
            "duration": "3 sessions",
            "priority": "medium"
        })
        
        # Entrepreneurship (if has some experience)
        if years_experience >= 5 and extracted_data.assets_liabilities.get("net_worth", 0) > 5000:
            programs.append({
                "program_name": "Entrepreneurship Support Program",
                "category": "business",
                "description": "Training and resources to start your own business",
                "duration": "6 months",
                "priority": "medium"
            })
        
        # Financial literacy (always helpful)
        programs.append({
            "program_name": "Financial Literacy Workshop",
            "category": "financial_education",
            "description": "Learn budgeting, saving, and financial planning",
            "duration": "2 weeks",
            "priority": "low"
        })
        
        return programs
    
    async def _generate_llm_reasoning(self, extracted_data: ExtractedData,
                                     eligibility_result: EligibilityResult,
                                     decision: DecisionType,
                                     support_amount: float,
                                     enablement_programs: list) -> tuple:
        """Generate reasoning using LLM"""
        
        # Build prompt for LLM
        prompt = self._build_reasoning_prompt(
            extracted_data, eligibility_result, decision,
            support_amount, enablement_programs
        )
        
        if self.llm_service:
            try:
                reasoning = await self.llm_service.generate(prompt, max_tokens=500)
            except Exception as e:
                self.logger.error(f"LLM generation error: {e}")
                reasoning = self._generate_fallback_reasoning(
                    extracted_data, eligibility_result, decision
                )
        else:
            reasoning = self._generate_fallback_reasoning(
                extracted_data, eligibility_result, decision
            )
        
        # Extract key factors
        key_factors = self._extract_key_factors(eligibility_result, extracted_data)
        
        return reasoning, key_factors
    
    def _build_reasoning_prompt(self, extracted_data: ExtractedData,
                                eligibility_result: EligibilityResult,
                                decision: DecisionType,
                                support_amount: float,
                                enablement_programs: list) -> str:
        """Build prompt for LLM reasoning generation"""
        
        income_info = extracted_data.income_data
        employment_info = extracted_data.employment_data
        
        prompt = f"""As a social support case manager, provide a clear and empathetic explanation for the following decision:

Decision: {decision.value.upper()}
Eligibility Score: {eligibility_result.eligibility_score:.2f}
{"Financial Support: " + str(support_amount) + " AED/month" if support_amount else "No financial support"}

Applicant Profile:
- Monthly Income: {income_info.get('monthly_income', 0)} AED
- Monthly Expenses: {income_info.get('monthly_expenses', 0)} AED
- Employment: {employment_info.get('employment_status', 'unknown')}
- Experience: {employment_info.get('years_of_experience', 0)} years

Key Assessment Factors:
{chr(10).join(eligibility_result.reasoning)}

Recommended Programs: {len(enablement_programs)} programs

Provide a 2-3 paragraph explanation that:
1. Summarizes the decision and key factors
2. Explains the rationale in empathetic terms
3. Highlights next steps and opportunities

Response:"""
        
        return prompt
    
    def _generate_fallback_reasoning(self, extracted_data: ExtractedData,
                                    eligibility_result: EligibilityResult,
                                    decision: DecisionType) -> str:
        """Generate reasoning without LLM"""
        
        income = extracted_data.income_data.get("monthly_income", 0)
        score = eligibility_result.eligibility_score
        
        if decision == DecisionType.APPROVED:
            return f"""Based on comprehensive assessment, your application has been APPROVED for social support.

The evaluation considered your current financial situation (monthly income: {income} AED), employment status, and overall needs. The eligibility score of {score:.2f} indicates you meet the criteria for assistance.

This support is designed to help stabilize your situation while you pursue economic enablement opportunities. We encourage you to participate in the recommended programs to build long-term financial independence."""
        
        elif decision == DecisionType.SOFT_DECLINED:
            return f"""After careful review, your application requires additional information or improvements before approval.

While your eligibility score of {score:.2f} shows potential, certain criteria need to be addressed. We encourage you to:
1. Update your documentation if circumstances have changed
2. Participate in our enablement programs to strengthen your application
3. Reapply in 3-6 months

We're committed to supporting your journey toward financial stability."""
        
        else:
            return f"""After thorough assessment, we're unable to approve your application at this time.

Based on the evaluation (score: {score:.2f}), your current situation doesn't meet the program's eligibility criteria. However, we encourage you to:
1. Explore the economic enablement programs available
2. Consider reapplying if your circumstances change
3. Contact our support team for guidance

We remain committed to helping you achieve financial stability through alternative pathways."""
    
    def _extract_key_factors(self, eligibility_result: EligibilityResult,
                            extracted_data: ExtractedData) -> list:
        """Extract key decision factors"""
        factors = []
        
        # Income factor
        if eligibility_result.income_assessment.get("needs_support"):
            factors.append(f"Low income level: {eligibility_result.income_assessment.get('income_level')}")
        
        # Wealth factor
        if eligibility_result.wealth_assessment.get("needs_support"):
            factors.append(f"Limited assets: {eligibility_result.wealth_assessment.get('wealth_level')} net worth")
        
        # Employment factor
        if eligibility_result.employment_assessment.get("needs_enablement"):
            factors.append(f"Employment situation: {eligibility_result.employment_assessment.get('employment_status')}")
        
        # ML prediction
        ml_prob = eligibility_result.ml_prediction.get("probability", 0)
        factors.append(f"ML model confidence: {ml_prob*100:.1f}%")
        
        # Policy compliance
        rules_met = sum(eligibility_result.policy_rules_met.values())
        total_rules = len(eligibility_result.policy_rules_met)
        factors.append(f"Policy compliance: {rules_met}/{total_rules} requirements met")
        
        return factors
    
    def _calculate_confidence(self, eligibility_result: EligibilityResult) -> float:
        """Calculate recommendation confidence"""
        score = eligibility_result.eligibility_score
        
        # Higher confidence for clear cases (very high or very low scores)
        if score >= 0.8 or score <= 0.3:
            return 0.9
        elif score >= 0.7 or score <= 0.4:
            return 0.75
        else:
            return 0.6  # Borderline cases have lower confidence
    
    def _load_enablement_programs(self) -> Dict[str, Any]:
        """Load enablement programs database"""
        return {
            "job_matching": "Job Matching Service",
            "upskilling": "Professional Skills Development",
            "counseling": "Career Counseling & Planning",
            "entrepreneurship": "Entrepreneurship Support Program",
            "financial_literacy": "Financial Literacy Workshop"
        }
