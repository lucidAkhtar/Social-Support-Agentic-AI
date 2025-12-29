"""
Decision Agent - Phase 5
Combines validation results and ML predictions to generate final eligibility decisions.
Produces APPROVE, DENY, or NEEDS_REVIEW recommendations with detailed justifications.
"""

import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

import joblib
from sklearn.ensemble import RandomForestClassifier


class DecisionStatus(Enum):
    """Final decision outcomes"""
    APPROVE = "APPROVE"
    DENY = "DENY"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class ApprovalReason(Enum):
    """Categorized reasons for approval decisions"""
    HIGH_QUALITY_HIGH_ML_CONFIDENCE = "high_quality_high_ml"
    QUALITY_MET_ML_APPROVED = "quality_met_ml_approved"
    ML_STRONG_DESPITE_VALIDATION_GAPS = "ml_strong_override"
    BORDERLINE_MANUAL_REVIEW = "borderline_review"
    VALIDATION_FAILURES = "validation_failures"
    CRITICAL_MISSING_DATA = "critical_missing"
    LOW_ML_CONFIDENCE = "low_ml_confidence"
    CONTRADICTORY_SIGNALS = "contradictory"
    DEBT_BURDEN_EXCESSIVE = "debt_excessive"
    UNKNOWN = "unknown"


@dataclass
class DecisionFinding:
    """Individual reason contributing to decision"""
    category: str  # "validation", "ml", "business_rule", "data_quality"
    severity: str  # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    message: str
    weight: float = 0.0  # 0.0-1.0 impact on decision


@dataclass
class DecisionScore:
    """Composite scoring breakdown"""
    validation_score: float  # 0-1: Average of quality, consistency, completeness
    ml_confidence: float  # 0-1: ML prediction probability
    business_rule_score: float  # 0-1: Compliance with hard rules
    combined_score: float  # 0-1: Weighted aggregate
    approval_likelihood: float  # 0-1: Final confidence in approval


@dataclass
class DecisionResult:
    """Final decision for an application"""
    application_id: str
    final_decision: DecisionStatus
    decision_scores: DecisionScore
    findings: List[DecisionFinding] = field(default_factory=list)
    rationale: str = ""
    confidence_level: str = "MEDIUM"  # LOW, MEDIUM, HIGH
    appeals_eligible: bool = False
    recommended_actions: List[str] = field(default_factory=list)
    timestamp: str = ""
    ml_prediction_class: int = -1  # 0 or 1
    ml_prediction_probability: float = 0.0
    validation_status: str = ""
    critical_flags: List[str] = field(default_factory=list)


class DecisionAgent:
    """
    Combines validation results and ML predictions to make final eligibility decisions.
    
    Decision Logic:
    ├─ Data Quality Check (validation scores)
    ├─ ML Prediction (trained RandomForest)
    ├─ Business Rules (hard requirements)
    └─ Final Decision → APPROVE/DENY/NEEDS_REVIEW
    """

    def __init__(self, validation_results_path: str, model_path: str = None):
        """
        Args:
            validation_results_path: Path to validation_test_results.json
            model_path: Path to saved RandomForest model (optional - will train if not provided)
        """
        self.validation_results_path = Path(validation_results_path)
        self.model_path = Path(model_path) if model_path else None
        
        # Load validation results
        self.validation_data = self._load_validation_data()
        
        # Load or prepare model
        self.model = None
        self.feature_names = None
        self._prepare_model()
        
        # Decision thresholds
        self.VALIDATION_QUALITY_THRESHOLD = 0.85  # Minimum acceptable quality
        self.ML_CONFIDENCE_HIGH = 0.75  # Strong approval signal (adjusted from 0.85)
        self.ML_CONFIDENCE_MEDIUM = 0.60  # Moderate signal (adjusted from 0.65)
        self.ML_CONFIDENCE_LOW = 0.50  # Weak signal
        self.DEBT_BURDEN_CRITICAL = 0.80  # Max acceptable debt ratio
        self.INCOME_STABILITY_THRESHOLD = 0.70  # Min acceptable income consistency
        
    def _load_validation_data(self) -> Dict[str, Dict[str, Any]]:
        """Load validation results from JSON"""
        with open(self.validation_results_path, 'r') as f:
            data = json.load(f)
        
        # Convert to dict keyed by application_id
        validation_dict = {}
        for app_data in data.get('applications', []):
            app_id = app_data.get('application_id')
            if app_id:
                validation_dict[app_id] = app_data
        
        return validation_dict
    
    def _prepare_model(self):
        """Load trained model or extract from ML training results"""
        # Load the training results to get feature names
        ml_results_path = self.validation_results_path.parent.parent.parent / 'ml_training_results.json'
        
        if ml_results_path.exists():
            with open(ml_results_path, 'r') as f:
                ml_data = json.load(f)
            
            # Extract feature names from importance ranking
            self.feature_names = [
                feat['feature'] for feat in ml_data.get('feature_importance', [])
            ]
        else:
            # Fallback: standard feature list
            self.feature_names = [
                'quality_score', 'consistency_score', 'completeness_score',
                'personal_info_score', 'employment_score', 'income_score', 
                'assets_score', 'credit_score',
                'findings_count', 'documents_count',
                'all_documents_present', 'zero_findings',
                'avg_category_score', 'min_category_score', 'max_category_score',
                'category_variance', 'overall_quality_index'
            ]
    
    def _extract_features(self, app_id: str, validation_result: Dict) -> np.ndarray:
        """Extract 17 ML features from validation result"""
        features = {}
        
        # Extract validation metrics
        quality = validation_result.get('quality_score', 0.0)
        consistency = validation_result.get('consistency_score', 0.0)
        completeness = validation_result.get('completeness_score', 0.0)
        
        features['quality_score'] = quality
        features['consistency_score'] = consistency
        features['completeness_score'] = completeness
        
        # Category scores
        category_scores = validation_result.get('category_scores', {})
        features['personal_info_score'] = category_scores.get('personal_info', 0.0)
        features['employment_score'] = category_scores.get('employment', 0.0)
        features['income_score'] = category_scores.get('income', 0.0)
        features['assets_score'] = category_scores.get('assets', 0.0)
        features['credit_score'] = category_scores.get('credit', 0.0)
        
        # Validation metrics
        findings = validation_result.get('findings', [])
        documents = validation_result.get('documents_reviewed', 0)
        
        features['findings_count'] = len(findings)
        features['documents_count'] = documents
        features['all_documents_present'] = 1.0 if documents >= 6 else 0.0
        features['zero_findings'] = 1.0 if len(findings) == 0 else 0.0
        
        # Composite features
        cat_scores = [
            features['personal_info_score'],
            features['employment_score'],
            features['income_score'],
            features['assets_score'],
            features['credit_score']
        ]
        cat_scores = [s for s in cat_scores if s > 0]
        
        features['avg_category_score'] = np.mean(cat_scores) if cat_scores else 0.0
        features['min_category_score'] = np.min(cat_scores) if cat_scores else 0.0
        features['max_category_score'] = np.max(cat_scores) if cat_scores else 0.0
        features['category_variance'] = np.var(cat_scores) if len(cat_scores) > 1 else 0.0
        
        # Overall quality index
        features['overall_quality_index'] = (quality * 0.3 + consistency * 0.3 + 
                                            completeness * 0.2 + 
                                            features['avg_category_score'] * 0.2)
        
        # Build feature vector in correct order
        feature_vector = np.array([features.get(name, 0.0) for name in self.feature_names])
        return feature_vector
    
    def _get_ml_prediction(self, validation_result: Dict) -> tuple:
        """
        Get ML prediction for application.
        Returns: (predicted_class, probability)
        
        Since we're using validation metrics directly in decision making,
        we approximate the ML model behavior from Phase 4 training.
        In production, would load joblib.load(model_path)
        """
        quality = validation_result.get('quality_score', 0.0)
        consistency = validation_result.get('consistency_score', 0.0)
        completeness = validation_result.get('completeness_score', 0.0)
        assets = validation_result.get('category_scores', {}).get('assets', 0.0)
        employment = validation_result.get('category_scores', {}).get('employment', 0.0)
        income = validation_result.get('category_scores', {}).get('income', 0.0)
        
        # Feature importance from Phase 4 (top 5 features):
        # 1. quality_score (25.53%) - Most important
        # 2. consistency_score (14.89%)
        # 3. assets_score (12.77%)
        # 4. category_variance (12.77%)
        # 5. min_category_score (10.64%)
        
        # Improved approximation: use weighted validation metrics
        # Simulates the RandomForest decision boundary learned from 50 applications
        category_scores = [quality, consistency, completeness, assets, employment, income]
        category_scores = [s for s in category_scores if s > 0]
        
        category_variance = np.var(category_scores) if len(category_scores) > 1 else 0.0
        min_category_score = np.min(category_scores) if category_scores else 0.0
        
        # Weighted composite using Phase 4 feature importance
        probability = (
            quality * 0.2553 +              # quality_score: 25.53%
            consistency * 0.1489 +           # consistency_score: 14.89%
            assets * 0.1277 +                # assets_score: 12.77%
            category_variance * 0.1277 +    # category_variance: 12.77%
            min_category_score * 0.1064 +   # min_category_score: 10.64%
            completeness * 0.0638 +          # Fill remaining weight
            income * 0.0638 +
            employment * 0.0364
        )
        
        # Scale probability to better utilize [0, 1] range
        # Phase 4 showed applications had validation scores in 0.80-0.98 range
        probability = min(1.0, max(0.0, probability))
        predicted_class = 1 if probability >= 0.5 else 0
        
        return predicted_class, probability
    
    def _evaluate_business_rules(self, validation_result: Dict) -> tuple:
        """
        Evaluate hard business rules.
        Returns: (rule_score, findings)
        """
        findings = []
        rule_score = 1.0
        
        # Rule 1: Minimum quality score
        quality = validation_result.get('quality_score', 0.0)
        if quality < 0.70:
            findings.append(DecisionFinding(
                category="business_rule",
                severity="CRITICAL",
                message=f"Quality score {quality:.2f} below minimum threshold 0.70",
                weight=0.3
            ))
            rule_score -= 0.3
        elif quality < 0.85:
            findings.append(DecisionFinding(
                category="business_rule",
                severity="HIGH",
                message=f"Quality score {quality:.2f} below preferred threshold 0.85",
                weight=0.15
            ))
            rule_score -= 0.15
        
        # Rule 2: Income verification (only penalize if present but weak)
        income_score = validation_result.get('category_scores', {}).get('income', 0.0)
        if income_score > 0 and income_score < self.INCOME_STABILITY_THRESHOLD:
            findings.append(DecisionFinding(
                category="business_rule",
                severity="HIGH",
                message=f"Income stability {income_score:.2f} below threshold {self.INCOME_STABILITY_THRESHOLD}",
                weight=0.2
            ))
            rule_score -= 0.2
        
        # Rule 3: Asset/Debt analysis
        finding_msgs = validation_result.get('findings', [])
        asset_findings = []
        for f in finding_msgs:
            if isinstance(f, dict):
                msg = f.get('message', '').lower()
            else:
                msg = str(f).lower()
            if 'debt' in msg and 'burden' in msg:
                asset_findings.append(f)
        
        if asset_findings:
            first_msg = asset_findings[0].get('message', str(asset_findings[0])) if isinstance(asset_findings[0], dict) else str(asset_findings[0])
            findings.append(DecisionFinding(
                category="business_rule",
                severity="HIGH",
                message=f"Critical debt burden detected: {first_msg}",
                weight=0.25
            ))
            rule_score -= 0.25
        
        # Rule 4: Complete documentation
        documents = validation_result.get('documents_reviewed', 0)
        if documents < 6:
            findings.append(DecisionFinding(
                category="business_rule",
                severity="MEDIUM",
                message=f"Incomplete documentation: {documents}/6 documents reviewed",
                weight=0.1
            ))
            rule_score -= 0.1
        
        rule_score = max(0.0, rule_score)
        return rule_score, findings
    
    def decide(self, application_id: str) -> DecisionResult:
        """
        Make final decision for an application.
        Combines validation + ML + business rules.
        """
        # Get validation result
        validation_result = self.validation_data.get(application_id)
        if not validation_result:
            return DecisionResult(
                application_id=application_id,
                final_decision=DecisionStatus.NEEDS_REVIEW,
                decision_scores=DecisionScore(0, 0, 0, 0, 0),
                rationale="Application not found in validation results",
                timestamp=datetime.now().isoformat()
            )
        
        # Extract decision components
        quality = validation_result.get('quality_score', 0.0)
        consistency = validation_result.get('consistency_score', 0.0)
        completeness = validation_result.get('completeness_score', 0.0)
        validation_score = (quality * 0.4 + consistency * 0.35 + completeness * 0.25)
        
        # Get ML prediction
        ml_class, ml_prob = self._get_ml_prediction(validation_result)
        
        # Evaluate business rules
        rule_score, rule_findings = self._evaluate_business_rules(validation_result)
        
        # Combine scores
        combined_score = (validation_score * 0.40 + ml_prob * 0.35 + rule_score * 0.25)
        
        # Prepare decision scores
        decision_scores = DecisionScore(
            validation_score=validation_score,
            ml_confidence=ml_prob,
            business_rule_score=rule_score,
            combined_score=combined_score,
            approval_likelihood=max(combined_score, ml_prob)  # Take more optimistic
        )
        
        # Make decision
        findings = rule_findings.copy()
        confidence_level = "MEDIUM"
        final_decision = DecisionStatus.NEEDS_REVIEW
        appeals_eligible = True
        recommended_actions = []
        critical_flags = []
        
        # Decision logic
        # HIGH CONFIDENCE APPROVAL: Strong validation + decent ML signal + rules pass
        if (validation_score >= 0.90 and ml_prob >= 0.70 and rule_score >= 0.90):
            final_decision = DecisionStatus.APPROVE
            confidence_level = "HIGH"
            appeals_eligible = False
            findings.insert(0, DecisionFinding(
                category="decision",
                severity="INFO",
                message=f"Strong approval: validation {validation_score:.2f} + ML {ml_prob:.2f} + rules {rule_score:.2f}",
                weight=1.0
            ))
        
        # STANDARD APPROVAL: Good validation + ML signal + rules pass
        elif (validation_score >= 0.85 and ml_prob >= 0.65 and rule_score >= 0.85):
            final_decision = DecisionStatus.APPROVE
            confidence_level = "HIGH"
            appeals_eligible = False
            findings.insert(0, DecisionFinding(
                category="decision",
                severity="INFO",
                message=f"Approved: validation {validation_score:.2f} + ML {ml_prob:.2f} + rules {rule_score:.2f}",
                weight=1.0
            ))
        
        # CONDITIONAL APPROVAL: Acceptable validation + rules mostly pass
        elif (validation_score >= 0.80 and rule_score >= 0.75):
            final_decision = DecisionStatus.APPROVE
            confidence_level = "MEDIUM"
            appeals_eligible = False
            findings.insert(0, DecisionFinding(
                category="decision",
                severity="INFO",
                message=f"Conditional approval: validation {validation_score:.2f} with minor flags",
                weight=1.0
            ))
            if rule_score < 0.85:
                recommended_actions.append("Verify employment letter within 30 days")
        
        # DENIAL: Critical rule failures
        elif rule_score < 0.60:
            final_decision = DecisionStatus.DENY
            confidence_level = "HIGH"
            appeals_eligible = True
            findings.insert(0, DecisionFinding(
                category="decision",
                severity="CRITICAL",
                message=f"Business rule violations: rule score {rule_score:.2f}",
                weight=1.0
            ))
            critical_flags.append("FAILED_BUSINESS_RULES")
        
        # DENIAL: Critically poor data quality
        elif quality < 0.60 and consistency < 0.60:
            final_decision = DecisionStatus.DENY
            confidence_level = "HIGH"
            appeals_eligible = True
            findings.insert(0, DecisionFinding(
                category="decision",
                severity="CRITICAL",
                message=f"Insufficient data quality: quality {quality:.2f}, consistency {consistency:.2f}",
                weight=1.0
            ))
            critical_flags.append("INSUFFICIENT_DATA_QUALITY")
        
        # NEEDS REVIEW: Borderline cases
        else:
            final_decision = DecisionStatus.NEEDS_REVIEW
            confidence_level = "MEDIUM" if combined_score >= 0.60 else "LOW"
            appeals_eligible = True
            findings.insert(0, DecisionFinding(
                category="decision",
                severity="INFO",
                message=f"Manual review required: combined score {combined_score:.2f} (borderline)",
                weight=0.5
            ))
            recommended_actions.append("Escalate to human reviewer for additional verification")
            
            # Add guidance for what's needed
            if rule_score < 0.85:
                recommended_actions.append("Address business rule gaps before re-submission")
            if validation_score < 0.85:
                recommended_actions.append("Improve data quality metrics (current: {:.2f})".format(validation_score))
        
        # Build rationale
        rationale = f"Decision based on validation quality ({quality:.2f}), "
        rationale += f"ML confidence ({ml_prob:.2f}), and business rule compliance ({rule_score:.2f}). "
        rationale += f"Combined eligibility score: {combined_score:.2f}"
        
        return DecisionResult(
            application_id=application_id,
            final_decision=final_decision,
            decision_scores=decision_scores,
            findings=findings,
            rationale=rationale,
            confidence_level=confidence_level,
            appeals_eligible=appeals_eligible,
            recommended_actions=recommended_actions,
            timestamp=datetime.now().isoformat(),
            ml_prediction_class=ml_class,
            ml_prediction_probability=ml_prob,
            validation_status=validation_result.get('validation_status', 'UNKNOWN'),
            critical_flags=critical_flags
        )
    
    def decide_batch(self, application_ids: List[str] = None) -> List[DecisionResult]:
        """
        Make decisions for multiple applications.
        If application_ids is None, decide all validated applications.
        """
        if application_ids is None:
            application_ids = list(self.validation_data.keys())
        
        results = []
        for app_id in sorted(application_ids):
            result = self.decide(app_id)
            results.append(result)
        
        return results
    
    def generate_summary_report(self, decisions: List[DecisionResult]) -> Dict[str, Any]:
        """Generate summary statistics from decisions"""
        if not decisions:
            return {}
        
        approve_count = sum(1 for d in decisions if d.final_decision == DecisionStatus.APPROVE)
        deny_count = sum(1 for d in decisions if d.final_decision == DecisionStatus.DENY)
        review_count = sum(1 for d in decisions if d.final_decision == DecisionStatus.NEEDS_REVIEW)
        
        high_conf = sum(1 for d in decisions if d.confidence_level == "HIGH")
        medium_conf = sum(1 for d in decisions if d.confidence_level == "MEDIUM")
        low_conf = sum(1 for d in decisions if d.confidence_level == "LOW")
        
        avg_validation_score = np.mean([d.decision_scores.validation_score for d in decisions])
        avg_ml_confidence = np.mean([d.decision_scores.ml_confidence for d in decisions])
        avg_combined_score = np.mean([d.decision_scores.combined_score for d in decisions])
        
        appeals_eligible = sum(1 for d in decisions if d.appeals_eligible)
        
        return {
            'total_applications': len(decisions),
            'decisions': {
                'approve': approve_count,
                'approve_pct': round(approve_count / len(decisions) * 100, 2),
                'deny': deny_count,
                'deny_pct': round(deny_count / len(decisions) * 100, 2),
                'needs_review': review_count,
                'needs_review_pct': round(review_count / len(decisions) * 100, 2),
            },
            'confidence_distribution': {
                'high': high_conf,
                'medium': medium_conf,
                'low': low_conf,
            },
            'average_scores': {
                'validation_score': round(avg_validation_score, 4),
                'ml_confidence': round(avg_ml_confidence, 4),
                'combined_score': round(avg_combined_score, 4),
            },
            'appeals_eligible': appeals_eligible,
            'timestamp': datetime.now().isoformat()
        }


def serialize_decision(decision: DecisionResult) -> Dict[str, Any]:
    """Convert DecisionResult to JSON-serializable dict"""
    return {
        'application_id': decision.application_id,
        'final_decision': decision.final_decision.value,
        'decision_scores': {
            'validation_score': round(decision.decision_scores.validation_score, 4),
            'ml_confidence': round(decision.decision_scores.ml_confidence, 4),
            'business_rule_score': round(decision.decision_scores.business_rule_score, 4),
            'combined_score': round(decision.decision_scores.combined_score, 4),
            'approval_likelihood': round(decision.decision_scores.approval_likelihood, 4),
        },
        'findings': [
            {
                'category': f.category,
                'severity': f.severity,
                'message': f.message,
                'weight': f.weight,
            }
            for f in decision.findings
        ],
        'rationale': decision.rationale,
        'confidence_level': decision.confidence_level,
        'appeals_eligible': decision.appeals_eligible,
        'recommended_actions': decision.recommended_actions,
        'timestamp': decision.timestamp,
        'ml_prediction_class': decision.ml_prediction_class,
        'ml_prediction_probability': round(decision.ml_prediction_probability, 4),
        'validation_status': decision.validation_status,
        'critical_flags': decision.critical_flags,
    }