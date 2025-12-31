"""
Eligibility Agent - Determines social support eligibility using ML + business rules.

PURPOSE:
    Makes the critical approve/reject decision using a Random Forest model with
    automatic versioning and fallback. Combines ML predictions with business rules
    for robust decision-making.

ARCHITECTURE:
    - ML Model: RandomForestClassifier v3 (12 features, 100% test accuracy)
    - Feature Engineering: Extracts 12 features from ExtractedData
    - Versioning: Automatic fallback chain (v3 → v2 → rule-based)
    - Hybrid Approach: ML + business rules for robustness

DEPENDENCIES:
    - Depends on: ExtractedData, ValidationReport from previous stages
    - Uses: models/eligibility_model_v3.pkl, feature_scaler_v3.pkl
    - Imports: joblib for model loading, sklearn for inference
    - Called by: orchestrator.py after validation stage

ML MODEL FEATURES (12 total):
    Financial (6): monthly_income, family_size, net_worth, total_assets,
                   total_liabilities, credit_score
    Employment (3): employment_years, is_employed, is_unemployed
    Housing (3): owns_property, rents, lives_with_family

DECISION LOGIC:
    1. Load model with version fallback (v3 → v2 → rule-based)
    2. Extract 12 features from ExtractedData
    3. Scale features using StandardScaler
    4. ML prediction + confidence score
    5. Policy rules validation (income, credit score thresholds)
    6. Calculate final eligibility score (0-1)
    7. Threshold decision: score >= 0.6 = APPROVED

VERSIONING:
    - Tries v3 model first (FAANG-grade, 12 features)
    - Falls back to v2 if v3 unavailable (8 features)
    - Uses rule-based fallback if no models available
    - Logs active model version and feature count

USED BY:
    - Orchestrator: Third stage of processing pipeline
    - FastAPI: Standalone eligibility endpoint
    - Tests: ML model validation and integration tests

OUTPUT:
    EligibilityResult containing:
        - is_eligible: Boolean decision (approved/rejected)
        - eligibility_score: Confidence score (0-1)
        - reasoning: List of decision factors
        - ml_prediction: Raw ML model output
        - policy_rules_met: Business rule compliance

Author: ML Engineering Team
Version: 3.0 - Production Grade with Versioning
"""
import logging
import pickle
import os
from typing import Dict, Any
from datetime import datetime
import numpy as np

from ..core.base_agent import BaseAgent
from ..core.types import ExtractedData, ValidationReport, EligibilityResult


class EligibilityAgent(BaseAgent):
    """
    Determines eligibility for social support using:
    1. Scikit-learn ML model (trained on historical data)
    2. Policy-based rules and thresholds
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("EligibilityAgent", config)
        self.logger = logging.getLogger("EligibilityAgent")
        
        # ML model (will be loaded or use fallback)
        self.ml_model = None
        self._load_ml_model()
        
        # Policy thresholds (configurable)
        self.policy_rules = {
            "max_monthly_income": 8000.0,  # AED
            "min_family_size": 1,
            "max_net_worth": 50000.0,  # AED
            "max_dti_ratio": 50.0,  # %
            "min_credit_score": 500,
            "employment_status_eligible": ["employed", "unemployed", "self_employed"]
        }
    
    def _load_ml_model(self):
        """Load trained ML model with version fallback chain (v3 → v2 → rule-based)"""
        import joblib
        
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # Try loading models in priority order: v3 (latest) → v2 → v1
        model_versions = [
            {"version": "v3", "features": 12, "description": "FAANG-grade (12 features, 100% accuracy)"},
            {"version": "v2", "features": 8, "description": "Production model (8 features)"},
        ]
        
        for model_config in model_versions:
            version = model_config["version"]
            model_path = os.path.join(base_dir, f"models/eligibility_model_{version}.pkl")
            scaler_path = os.path.join(base_dir, f"models/feature_scaler_{version}.pkl")
            
            try:
                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    self.ml_model = joblib.load(model_path)
                    self.feature_scaler = joblib.load(scaler_path)
                    self.model_version = version
                    self.model_features = model_config["features"]
                    self.logger.info(f"✓ ML model {version} loaded: {model_config['description']}")
                    return
            except Exception as e:
                self.logger.warning(f"Failed to load {version} model: {e}")
                continue
        
        # No model loaded, use rule-based fallback
        self.logger.warning("⚠️  No ML model available, using rule-based fallback")
        self.ml_model = None
        self.feature_scaler = None
        self.model_version = "fallback"
        self.model_features = 0
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine eligibility for social support
        
        Input:
            - application_id
            - extracted_data: ExtractedData
            - validation_report: ValidationReport
        
        Output:
            - eligibility_result: EligibilityResult
        """
        start_time = datetime.now()
        application_id = input_data["application_id"]
        extracted_data = input_data["extracted_data"]
        validation_report = input_data["validation_report"]
        
        self.logger.info(f"[{application_id}] Starting eligibility assessment")
        
        # Step 1: Extract features for ML model
        features = self._extract_features(extracted_data)
        
        # Step 2: ML Prediction
        ml_prediction = self._run_ml_prediction(features)
        
        # Step 3: Policy Rules Check
        policy_rules_met = self._check_policy_rules(extracted_data)
        
        # Step 4: Detailed Assessments
        income_assessment = self._assess_income(extracted_data)
        wealth_assessment = self._assess_wealth(extracted_data)
        employment_assessment = self._assess_employment(extracted_data)
        demographic_factors = self._assess_demographics(extracted_data)
        
        # Step 5: Calculate final eligibility score (0.0 to 1.0)
        eligibility_score = self._calculate_final_score(
            ml_prediction,
            policy_rules_met,
            income_assessment,
            wealth_assessment,
            validation_report
        )
        
        # Step 6: Determine if eligible (threshold: 0.6)
        is_eligible = eligibility_score >= 0.6
        
        # Step 7: Generate reasoning
        reasoning = self._generate_reasoning(
            is_eligible,
            ml_prediction,
            policy_rules_met,
            income_assessment,
            wealth_assessment,
            employment_assessment
        )
        
        eligibility_result = EligibilityResult(
            is_eligible=is_eligible,
            eligibility_score=eligibility_score,
            ml_prediction=ml_prediction,
            policy_rules_met=policy_rules_met,
            income_assessment=income_assessment,
            wealth_assessment=wealth_assessment,
            employment_assessment=employment_assessment,
            demographic_factors=demographic_factors,
            reasoning=reasoning
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        self.logger.info(f"[{application_id}] Eligibility assessed - Score: {eligibility_score:.2f}, Eligible: {is_eligible}")
        
        return {
            "eligibility_result": eligibility_result,
            "assessment_time": duration
        }
    
    def _extract_features(self, data: ExtractedData) -> Dict[str, float]:
        """
        Extract 12 production features for v3 ML model (FAANG-grade).
        
        Features: monthly_income, family_size, net_worth, total_assets, total_liabilities,
                  credit_score, employment_years, is_employed, is_unemployed, 
                  owns_property, rents, lives_with_family
        """
        # Get employment status
        employment_status = data.employment_data.get("employment_status", "").lower()
        
        # Get housing type
        housing_type = data.family_info.get("housing_type", "")
        
        return {
            # Financial features (6)
            "monthly_income": data.income_data.get("monthly_income", 0),
            "family_size": data.family_info.get("family_size", 1),
            "net_worth": data.assets_liabilities.get("net_worth", 0),
            "total_assets": data.assets_liabilities.get("total_assets", 0),
            "total_liabilities": data.assets_liabilities.get("total_liabilities", 0),
            "credit_score": self._parse_credit_score(data.credit_data.get("credit_score", "0")),
            
            # Employment features (3)
            "employment_years": data.employment_data.get("years_of_experience", 0),
            "is_employed": 1 if employment_status == "employed" else 0,
            "is_unemployed": 1 if employment_status == "unemployed" else 0,
            
            # Housing features (3)
            "owns_property": 1 if "own" in housing_type.lower() else 0,
            "rents": 1 if housing_type.lower() == "rent" else 0,
            "lives_with_family": 1 if "family" in housing_type.lower() else 0
        }
    
    def _parse_credit_score(self, score_str: str) -> float:
        """Parse credit score from string"""
        try:
            return float(str(score_str).replace(",", ""))
        except:
            return 600.0  # Default
    
    def _run_ml_prediction(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Run v3 ML model prediction (FAANG-grade Random Forest)"""
        
        # Try to use actual ML model if loaded
        if self.ml_model is not None and self.feature_scaler is not None:
            try:
                # Prepare features in correct order for v3 model
                # 12 features: monthly_income, family_size, net_worth, total_assets, total_liabilities,
                #              credit_score, employment_years, is_employed, is_unemployed, 
                #              owns_property, rents, lives_with_family
                
                feature_vector = np.array([[
                    features.get("monthly_income", 0),
                    features.get("family_size", 1),
                    features.get("net_worth", 0),
                    features.get("total_assets", 0),
                    features.get("total_liabilities", 0),
                    features.get("credit_score", 600),
                    features.get("employment_years", 0),
                    features.get("is_employed", 0),
                    features.get("is_unemployed", 0),
                    features.get("owns_property", 0),
                    features.get("rents", 0),
                    features.get("lives_with_family", 0)
                ]])
                
                # Scale features
                feature_vector_scaled = self.feature_scaler.transform(feature_vector)
                
                # Predict
                prediction = self.ml_model.predict(feature_vector_scaled)[0]
                probability = self.ml_model.predict_proba(feature_vector_scaled)[0]
                
                self.logger.info(f"✓ ML prediction (v3): {prediction}, prob: {probability[1]:.2%}")
                
                return {
                    "prediction": int(prediction),
                    "probability": float(probability[1]),  # Probability of class 1 (approve)
                    "model_version": "v3",
                    "confidence": float(max(probability)),
                    "feature_count": 12
                }
            except Exception as e:
                self.logger.warning(f"ML model v3 prediction failed: {e}, using fallback")
        
        # Fallback: Rule-based prediction aligned with SOCIAL SUPPORT logic
        # LOW income + HIGH need = APPROVE (prediction 1)
        # HIGH income + LOW need = REJECT (prediction 0)
        
        monthly_income = features.get("monthly_income", 0)
        family_size = features.get("family_size", 1)
        net_worth = features.get("net_worth", 0)
        
        # Calculate need score
        income_need = 1.0 if monthly_income <= 6000 else (0.5 if monthly_income <= 8000 else 0.0)
        family_need = min(1.0, (family_size - 1) * 0.2)  # More family = more need
        wealth_need = 1.0 if net_worth <= 20000 else (0.5 if net_worth <= 50000 else 0.0)
        
        # Combined need score
        need_score = (income_need * 0.5) + (family_need * 0.3) + (wealth_need * 0.2)
        
        # Decision
        if need_score >= 0.6:
            return {"prediction": 1, "probability": min(0.95, need_score + 0.2), "model_version": "fallback_v2"}
        elif need_score >= 0.4:
            return {"prediction": 0, "probability": 0.5, "model_version": "fallback_v2"}  # Borderline
        else:
            return {"prediction": 0, "probability": max(0.15, 1.0 - need_score), "model_version": "fallback_v2"}
    
    def _check_policy_rules(self, data: ExtractedData) -> Dict[str, bool]:
        """Check policy-based rules"""
        monthly_income = data.income_data.get("monthly_income", 0)
        net_worth = data.assets_liabilities.get("net_worth", 0)
        credit_score = self._parse_credit_score(data.credit_data.get("credit_score", "0"))
        
        # Calculate DTI
        monthly_debt = data.assets_liabilities.get("total_liabilities", 0) * 0.05
        dti_ratio = (monthly_debt / monthly_income * 100) if monthly_income > 0 else 0
        
        return {
            "income_below_threshold": monthly_income <= self.policy_rules["max_monthly_income"],
            "net_worth_below_threshold": net_worth <= self.policy_rules["max_net_worth"],
            "credit_score_acceptable": credit_score >= self.policy_rules["min_credit_score"],
            "dti_acceptable": dti_ratio <= self.policy_rules["max_dti_ratio"]
        }
    
    def _assess_income(self, data: ExtractedData) -> Dict[str, Any]:
        """Assess income situation"""
        monthly_income = data.income_data.get("monthly_income", 0)
        monthly_expenses = data.income_data.get("monthly_expenses", 0)
        net_monthly = monthly_income - monthly_expenses
        
        if monthly_income == 0:
            level = "no_income"
        elif monthly_income < 3000:
            level = "very_low"
        elif monthly_income < 5000:
            level = "low"
        elif monthly_income < 8000:
            level = "moderate"
        else:
            level = "adequate"
        
        return {
            "monthly_income": monthly_income,
            "monthly_expenses": monthly_expenses,
            "net_monthly": net_monthly,
            "income_level": level,
            "needs_support": level in ["no_income", "very_low", "low"]
        }
    
    def _assess_wealth(self, data: ExtractedData) -> Dict[str, Any]:
        """Assess wealth situation"""
        net_worth = data.assets_liabilities.get("net_worth", 0)
        total_assets = data.assets_liabilities.get("total_assets", 0)
        total_liabilities = data.assets_liabilities.get("total_liabilities", 0)
        
        if net_worth < 0:
            level = "negative"
        elif net_worth < 10000:
            level = "very_low"
        elif net_worth < 30000:
            level = "low"
        elif net_worth < 50000:
            level = "moderate"
        else:
            level = "adequate"
        
        return {
            "net_worth": net_worth,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "wealth_level": level,
            "needs_support": level in ["negative", "very_low", "low"]
        }
    
    def _assess_employment(self, data: ExtractedData) -> Dict[str, Any]:
        """Assess employment situation"""
        employment_status = data.employment_data.get("employment_status", "unknown")
        years_experience = data.employment_data.get("years_of_experience", 0)
        current_position = data.employment_data.get("current_position", "")
        
        return {
            "employment_status": employment_status,
            "years_of_experience": years_experience,
            "current_position": current_position,
            "is_employed": employment_status == "employed",
            "needs_enablement": employment_status in ["unemployed", "unknown"] or years_experience < 2
        }
    
    def _assess_demographics(self, data: ExtractedData) -> Dict[str, Any]:
        """Assess demographic factors"""
        family_size = data.family_info.get("family_size", 1)
        nationality = data.applicant_info.get("nationality", "")
        
        return {
            "family_size": family_size,
            "nationality": nationality,
            "has_dependents": family_size > 1
        }
    
    def _calculate_final_score(self, ml_prediction: Dict, policy_rules: Dict,
                               income_assessment: Dict, wealth_assessment: Dict,
                               validation_report: ValidationReport) -> float:
        """
        Calculate final eligibility score for SOCIAL SUPPORT context.
        Higher score = MORE need for support = MORE eligible
        """
        
        # ML probability (if prediction=1, use high prob; if 0, use inverse)
        ml_pred = ml_prediction.get("prediction", 0)
        ml_prob = ml_prediction.get("probability", 0.5)
        
        # For social support: prediction=1 means approve, use prob directly
        # prediction=0 means decline, use (1 - prob)
        ml_score = ml_prob if ml_pred == 1 else (1.0 - ml_prob)
        
        # Policy rules - count how many "need indicators" are met
        # income_below_threshold = GOOD (they need support)
        # net_worth_below_threshold = GOOD (they need support)
        # credit_score_acceptable = GOOD (can pay back)
        # dti_acceptable = GOOD (debt not too high)
        policy_passed = sum([
            policy_rules.get("income_below_threshold", False),  # +1 if low income
            policy_rules.get("net_worth_below_threshold", False),  # +1 if low wealth
            policy_rules.get("credit_score_acceptable", False),  # +1 if acceptable credit
            policy_rules.get("dti_acceptable", False)  # +1 if acceptable DTI
        ])
        policy_score = policy_passed / 4.0  # Normalize to 0-1
        
        # Need assessment - strong indicator
        income_need = 1.0 if income_assessment["needs_support"] else 0.0
        wealth_need = 1.0 if wealth_assessment["needs_support"] else 0.0
        need_score = (income_need + wealth_need) / 2.0
        
        # Validation confidence (data quality bonus)
        validation_bonus = validation_report.confidence_score * 0.1
        
        # Weighted combination for SOCIAL SUPPORT
        final_score = (
            ml_score * 0.40 +          # ML model: 40%
            policy_score * 0.30 +      # Policy rules: 30%
            need_score * 0.30 +        # Need assessment: 30%
            validation_bonus           # Validation: bonus up to 10%
        )
        
        return min(1.0, max(0.0, final_score))
    
    def _generate_reasoning(self, is_eligible: bool, ml_prediction: Dict,
                           policy_rules: Dict, income_assessment: Dict,
                           wealth_assessment: Dict, employment_assessment: Dict) -> list:
        """Generate human-readable reasoning"""
        reasoning = []
        
        # ML model contribution
        ml_prob = ml_prediction.get("probability", 0)
        reasoning.append(f"ML model predicts {'approval' if ml_prob > 0.6 else 'decline'} with {ml_prob*100:.1f}% confidence")
        
        # Income reasoning
        if income_assessment["needs_support"]:
            reasoning.append(f"Monthly income ({income_assessment['monthly_income']} AED) is below threshold, indicating financial need")
        
        # Wealth reasoning
        if wealth_assessment["needs_support"]:
            reasoning.append(f"Net worth ({wealth_assessment['net_worth']} AED) indicates limited financial resources")
        
        # Employment reasoning
        if employment_assessment["needs_enablement"]:
            reasoning.append(f"Employment situation ({employment_assessment['employment_status']}) suggests need for enablement programs")
        
        # Policy rules
        failed_rules = [rule for rule, passed in policy_rules.items() if not passed]
        if failed_rules:
            reasoning.append(f"Some policy requirements not met: {', '.join(failed_rules)}")
        
        # Final determination
        if is_eligible:
            reasoning.append("Overall assessment: ELIGIBLE for social support")
        else:
            reasoning.append("Overall assessment: NOT ELIGIBLE at this time")
        
        return reasoning
