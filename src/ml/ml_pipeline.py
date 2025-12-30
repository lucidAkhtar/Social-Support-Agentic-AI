"""
Real ML pipeline using scikit-learn and SHAP for interpretable predictions.
"""

import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Tuple
import pickle

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import shap
except ImportError:
    RandomForestClassifier = None
    shap = None


class EligibilityMLModel:
    """Train and use ML model for social support eligibility scoring."""
    
    def __init__(self, model_path: str = "models/eligibility_model.pkl"):
        self.model_path = Path(model_path)
        self.model = None
        self.scaler = None
        self.explainer = None
        self.feature_names = [
            "monthly_income", "family_size", "num_dependents",
            "employment_stability", "education_level",
            "total_assets", "total_liabilities", "age"
        ]
        
        self._load_or_train()
    
    def _load_or_train(self):
        """Load existing model or train new one."""
        
        if self.model_path.exists():
            try:
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                print(f"✓ Loaded existing model from {self.model_path}")
                return
            except:
                pass
        
        # Train new model
        print("Training new eligibility model...")
        self._train_model()
    
    def _train_model(self):
        """Train ML model on synthetic data."""
        
        if RandomForestClassifier is None:
            raise RuntimeError("scikit-learn not installed")
        
        # Generate synthetic training data
        np.random.seed(42)
        n_samples = 500
        
        # Features: [income, family_size, dependents, stability, education, assets, liabilities, age]
        X = np.random.rand(n_samples, 8) * 100
        
        # Eligibility rules (synthetic but realistic)
        y = []
        for sample in X:
            income, family, deps, stability, edu, assets, liab, age = sample
            
            # Eligibility formula
            score = 0
            score -= income / 100 * 50  # Lower income = more eligible
            score += family / 10 * 20   # Larger family = more eligible
            score += deps / 10 * 15     # More dependents = more eligible
            score += stability * 10     # Employment stability helps
            score -= edu * 5            # Education lowers need
            score -= assets / 100 * 20  # More assets = less eligible
            score += liab / 100 * 10    # More debt = more eligible
            score += (age - 50) / 10 * 5  # Age factor
            
            y.append(1 if score > 0 else 0)
        
        X = np.clip(X, 0, 100)
        y = np.array(y)
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.model.fit(X, y)
        
        # Save model
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.model, f)
        
        print(f"✓ Trained and saved model to {self.model_path}")
    
    def predict_eligibility(self, applicant_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict eligibility and get SHAP explanation.
        
        Args:
            applicant_data: {monthly_income, family_size, num_dependents, ...}
        
        Returns:
            {eligibility_score: 0-1, decision: "eligible"|"ineligible", 
             shap_values: {...}, feature_importance: {...}}
        """
        
        # Extract features in correct order
        features = np.array([[
            applicant_data.get("monthly_income", 0),
            applicant_data.get("family_size", 1),
            applicant_data.get("num_dependents", 0),
            applicant_data.get("employment_stability", 0.5),  # 0-1
            applicant_data.get("education_level", 50),  # 0-100
            applicant_data.get("total_assets", 0),
            applicant_data.get("total_liabilities", 0),
            applicant_data.get("age", 35)
        ]])
        
        # Predict probability
        try:
            eligibility_score = self.model.predict_proba(features)[0][1]
        except:
            return {
                "eligibility_score": 0.5,
                "decision": "review_needed",
                "confidence": 0.0,
                "shap_values": {},
                "feature_importance": {},
                "error": "Prediction failed"
            }
        
        # Generate SHAP explanation if available
        shap_explanation = {}
        if shap is not None:
            try:
                # Create SHAP explainer
                explainer = shap.TreeExplainer(self.model)
                shap_values = explainer.shap_values(features)[1]  # Class 1 (eligible)
                
                shap_explanation = {
                    f"{self.feature_names[i]}": float(shap_values[i])
                    for i in range(len(self.feature_names))
                }
            except:
                pass
        
        # Generate feature importance
        feature_importance = {}
        if self.model and hasattr(self.model, 'feature_importances_'):
            feature_importance = {
                self.feature_names[i]: float(self.model.feature_importances_[i])
                for i in range(len(self.feature_names))
            }
        
        decision = "eligible" if eligibility_score > 0.6 else "ineligible" if eligibility_score < 0.4 else "review_needed"
        
        return {
            "eligibility_score": float(eligibility_score),
            "decision": decision,
            "confidence": abs(eligibility_score - 0.5) * 2,  # 0-1
            "shap_values": shap_explanation,
            "feature_importance": feature_importance,
            "features_used": {
                self.feature_names[i]: float(features[0][i])
                for i in range(len(self.feature_names))
            }
        }
    
    def get_feature_importance_chart_data(self) -> Dict[str, float]:
        """Get data for SHAP chart in Streamlit."""
        if not self.model or not hasattr(self.model, 'feature_importances_'):
            return {}
        
        return {
            self.feature_names[i]: float(self.model.feature_importances_[i])
            for i in range(len(self.feature_names))
        }
