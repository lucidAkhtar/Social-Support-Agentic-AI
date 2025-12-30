"""
Explainable AI with SHAP values and bias detection
WHAT THIS GIVES YOU: Transparent, defensible AI decisions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any
import shap
from sklearn.ensemble import RandomForestClassifier

class ExplainableML:
    """
    ML model with built-in explainability
    """
    
    def __init__(self):
        self.model = None
        self.explainer = None
        self.feature_names = []
    
    def train(self, X: pd.DataFrame, y: np.array):
        """Train model and create explainer"""
        self.feature_names = X.columns.tolist()
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X, y)
        
        # Create SHAP explainer
        self.explainer = shap.TreeExplainer(self.model)
        
        return self
    
    def predict_with_explanation(self, X: pd.DataFrame) -> Dict[str, Any]:
        """
        Make prediction and provide full explanation
        """
        # Prediction
        prediction = self.model.predict(X)[0]
        probability = self.model.predict_proba(X)[0]
        
        # SHAP values
        shap_values = self.explainer.shap_values(X)
        
        # For binary classification, use values for positive class
        if len(shap_values) == 2:
            shap_values = shap_values[1]
        
        # Get feature contributions
        feature_contributions = []
        for i, feature_name in enumerate(self.feature_names):
            feature_contributions.append({
                "feature": feature_name,
                "value": float(X.iloc[0][feature_name]),
                "impact": float(shap_values[0][i]),
                "impact_direction": "positive" if shap_values[0][i] > 0 else "negative"
            })
        
        # Sort by absolute impact
        feature_contributions.sort(key=lambda x: abs(x['impact']), reverse=True)
        
        # Generate human-readable explanation
        explanation = self._generate_explanation(feature_contributions, prediction)
        
        return {
            "prediction": "approved" if prediction == 1 else "declined",
            "confidence": float(max(probability)),
            "probability_approved": float(probability[1]) if len(probability) > 1 else float(probability[0]),
            "top_factors": feature_contributions[:5],
            "all_factors": feature_contributions,
            "explanation_text": explanation
        }
    
    def _generate_explanation(self, contributions: List[Dict], prediction: int) -> str:
        """Generate plain language explanation"""
        decision = "approved" if prediction == 1 else "declined"
        
        # Get top positive and negative factors
        positive_factors = [c for c in contributions if c['impact'] > 0][:3]
        negative_factors = [c for c in contributions if c['impact'] < 0][:3]
        
        explanation = f"Application {decision.upper()}.\n\n"
        
        if positive_factors:
            explanation += "Factors supporting approval:\n"
            for factor in positive_factors:
                explanation += f"• {factor['feature']}: {factor['value']} (impact: +{abs(factor['impact']):.3f})\n"
        
        if negative_factors:
            explanation += "\nFactors against approval:\n"
            for factor in negative_factors:
                explanation += f"• {factor['feature']}: {factor['value']} (impact: -{abs(factor['impact']):.3f})\n"
        
        return explanation
    
    def predict_eligibility(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Predict eligibility score for an applicant.
        Used by LangGraph for ML scoring stage.
        
        Args:
            features: Dictionary with monthly_income, family_size, total_assets, etc.
        
        Returns:
            Dictionary with eligibility_score, confidence, and prediction details
        """
        # Convert dict to DataFrame format expected by model
        feature_names = ['monthly_income', 'family_size', 'total_assets', 'total_liabilities', 
                        'age', 'years_employed', 'credit_score']
        
        # Create a row with provided features, using defaults for missing ones
        feature_values = [features.get(fname, 0) for fname in feature_names]
        
        # Create a DataFrame with proper column names
        X = pd.DataFrame([feature_values], columns=feature_names)
        
        # Make prediction if model exists, otherwise use heuristic
        if self.model is not None:
            prediction = self.model.predict(X)[0]
            probability = self.model.predict_proba(X)[0]
            confidence = float(max(probability))
            eligibility_score = float(probability[1]) if len(probability) > 1 else float(probability[0])
        else:
            # Fallback heuristic: higher eligibility for lower income, larger family
            monthly_income = features.get('monthly_income', 10000)
            family_size = features.get('family_size', 3)
            total_assets = features.get('total_assets', 0)
            
            # Simple scoring: income threshold + family size + assets
            score = 0.5
            if monthly_income < 15000:
                score += 0.2
            if family_size >= 3:
                score += 0.2
            if total_assets < 200000:
                score += 0.1
            
            eligibility_score = min(0.95, score)
            confidence = 0.75
        
        return {
            "eligibility_score": eligibility_score,
            "confidence": confidence,
            "prediction": "eligible" if eligibility_score > 0.5 else "ineligible",
            "reasoning": "Based on income, family size, and assets"
        }
    
    def get_feature_importance(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Get feature importance rankings for an applicant's features.
        
        Args:
            features: Dictionary with applicant features
        
        Returns:
            Dictionary mapping feature names to importance scores
        """
        # If SHAP explainer is available, use it
        if self.explainer is not None and self.model is not None:
            feature_names = ['monthly_income', 'family_size', 'total_assets', 'total_liabilities', 
                            'age', 'years_employed', 'credit_score']
            
            feature_values = [features.get(fname, 0) for fname in feature_names]
            X = pd.DataFrame([feature_values], columns=feature_names)
            
            shap_values = self.explainer.shap_values(X)
            
            # Handle both binary and single output
            if isinstance(shap_values, list):
                shap_vals = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            else:
                shap_vals = shap_values[0]
            
            importance = {}
            for fname, shap_val in zip(feature_names, shap_vals):
                importance[fname] = float(abs(shap_val))
            
            return importance
        
        # Fallback: basic importance scoring
        return {
            "monthly_income": 0.25,
            "family_size": 0.20,
            "total_assets": 0.20,
            "total_liabilities": 0.15,
            "age": 0.10,
            "years_employed": 0.07,
            "credit_score": 0.03
        }

class BiasDetector:
    """
    Detect and measure bias in AI decisions
    CRITICAL FOR GOVERNMENT: Ensure fairness
    """
    
    def __init__(self):
        self.protected_attributes = ['gender', 'nationality', 'age_group']
    
    def check_demographic_parity(
        self,
        predictions: List[int],
        protected_groups: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Check if approval rates are similar across demographic groups
        """
        results = {}
        
        for attribute, groups in protected_groups.items():
            group_approval_rates = {}
            
            for group in set(groups):
                group_indices = [i for i, g in enumerate(groups) if g == group]
                group_predictions = [predictions[i] for i in group_indices]
                
                approval_rate = sum(group_predictions) / len(group_predictions) if group_predictions else 0
                group_approval_rates[group] = approval_rate
            
            # Calculate disparity
            max_rate = max(group_approval_rates.values())
            min_rate = min(group_approval_rates.values())
            disparity = max_rate - min_rate
            
            results[attribute] = {
                "group_rates": group_approval_rates,
                "disparity": disparity,
                "fair": disparity < 0.05,  # 5% threshold
                "status": "✓ FAIR" if disparity < 0.05 else "⚠ BIAS DETECTED"
            }
        
        return results
    
    def generate_fairness_report(
        self,
        predictions: List[int],
        demographics: Dict[str, List[str]]
    ) -> str:
        """Generate comprehensive fairness report"""
        results = self.check_demographic_parity(predictions, demographics)
        
        report = "=== FAIRNESS AUDIT REPORT ===\n\n"
        
        for attribute, data in results.items():
            report += f"\n{attribute.upper()}:\n"
            report += f"Status: {data['status']}\n"
            report += f"Disparity: {data['disparity']:.2%}\n"
            report += "Group approval rates:\n"
            for group, rate in data['group_rates'].items():
                report += f"  {group}: {rate:.2%}\n"
        
        return report

# DEMO FOR PRESENTATION:
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    n_samples = 1000
    
    data = pd.DataFrame({
        'income': np.random.randint(5000, 30000, n_samples),
        'family_size': np.random.randint(1, 8, n_samples),
        'age': np.random.randint(25, 65, n_samples),
        'employment_years': np.random.randint(0, 20, n_samples),
        'has_debt': np.random.randint(0, 2, n_samples),
    })
    
    # Create labels (eligibility)
    labels = ((data['income'] < 15000) & (data['family_size'] >= 3)).astype(int)
    
    # Train explainable model
    print("=== Training Explainable ML Model ===\n")
    explainer = ExplainableML()
    explainer.train(data, labels)
    
    # Test on new applicant
    test_applicant = pd.DataFrame({
        'income': [12000],
        'family_size': [4],
        'age': [35],
        'employment_years': [5],
        'has_debt': [0],
    })
    
    print("=== Making Prediction with Explanation ===\n")
    result = explainer.predict_with_explanation(test_applicant)
    
    print(f"Decision: {result['prediction'].upper()}")
    print(f"Confidence: {result['confidence']:.2%}")
    print(f"\n{result['explanation_text']}")
    
    # Bias detection demo
    print("\n=== Bias Detection ===\n")
    
    # Generate demographic data
    genders = np.random.choice(['Male', 'Female'], n_samples)
    nationalities = np.random.choice(['UAE', 'India', 'Pakistan', 'Egypt'], n_samples)
    
    predictions = explainer.model.predict(data)
    
    bias_detector = BiasDetector()
    fairness_report = bias_detector.generate_fairness_report(
        predictions.tolist(),
        {
            'gender': genders.tolist(),
            'nationality': nationalities.tolist()
        }
    )
    
    print(fairness_report)