#!/usr/bin/env python3
"""
FAANG-Grade Random Forest Model Training for Social Support System
==================================================================

Features:
- 12 comprehensive features (financial + demographic + employment)
- Class balancing for skewed data
- Feature importance analysis
- Cross-validation with proper metrics
- Model versioning and metadata tracking
- Production-ready with proper error handling


"""

import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    precision_recall_curve, f1_score, accuracy_score
)
from sklearn.preprocessing import StandardScaler
import joblib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class FANGGradeMLTrainer:
    """
    ML trainer for social support eligibility prediction.
    
    Social Support Logic:
    - LOW income + HIGH need = Label 1 (APPROVE)
    - HIGH income + LOW need = Label 0 (REJECT)
    """
    
    # 12 production-grade features
    FEATURE_NAMES = [
        # Financial Features (6)
        'monthly_income',
        'family_size',
        'net_worth',
        'total_assets',
        'total_liabilities',
        'credit_score',
        
        # Employment Features (3)
        'employment_years',
        'is_employed',
        'is_unemployed',
        
        # Housing & Demographics (3)
        'owns_property',
        'rents',
        'lives_with_family'
    ]
    
    def __init__(self, test_data_path: str = "data/test_applications"):
        self.test_data_path = Path(test_data_path)
        self.models_path = Path("models")
        self.models_path.mkdir(exist_ok=True)
        
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importances = None
        
    def load_training_data(self) -> Tuple[pd.DataFrame, np.ndarray]:
        """Load training data from test_applications with proper labels."""
        
        print("="*80)
        print("LOADING TRAINING DATA FROM TEST APPLICATIONS")
        print("="*80)
        
        # Load metadata
        metadata_file = self.test_data_path.parent / "test_applications_metadata.json"
        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata not found: {metadata_file}")
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        applications = metadata['applications']
        
        # Convert to DataFrame
        df = pd.DataFrame(applications)
        
        # Create labels based on case_id
        # approved_* = 1, soft_decline_* = 0.5, reject_* = 0
        def get_label(case_id: str) -> int:
            if case_id.startswith('approved'):
                return 1  # APPROVE
            elif case_id.startswith('reject'):
                return 0  # REJECT
            else:  # soft_decline
                # Treat soft_decline as borderline - for training, use 0 (reject) to be conservative
                return 0
        
        df['label'] = df['case_id'].apply(get_label)
        
        print(f"\n✓ Loaded {len(df)} applications")
        print(f"  • APPROVED (label=1): {(df['label'] == 1).sum()} cases")
        print(f"  • SOFT_DECLINE (label=0): {((df['case_id'].str.startswith('soft_decline')) & (df['label'] == 0)).sum()} cases")
        print(f"  • REJECT (label=0): {((df['case_id'].str.startswith('reject')) & (df['label'] == 0)).sum()} cases")
        
        # Extract features
        X = self._extract_features(df)
        y = df['label'].values
        
        return X, y
    
    def _extract_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract 12 production-grade features."""
        
        features = []
        
        for _, row in df.iterrows():
            # Financial features
            monthly_income = float(row['monthly_income'])
            family_size = int(row['family_size'])
            net_worth = float(row['net_worth'])
            total_assets = float(row['total_assets'])
            total_liabilities = float(row['total_liabilities'])
            credit_score = int(row['credit_score'])
            
            # Employment features
            employment_years = int(row['employment_years'])
            employment_status = row['employment_status']
            is_employed = 1 if employment_status == 'employed' else 0
            is_unemployed = 1 if employment_status == 'unemployed' else 0
            
            # Housing features
            housing_type = row['housing_type']
            owns_property = 1 if 'Own' in housing_type else 0
            rents = 1 if housing_type == 'Rent' else 0
            lives_with_family = 1 if housing_type == 'Live with family' else 0
            
            feature_vector = [
                monthly_income,
                family_size,
                net_worth,
                total_assets,
                total_liabilities,
                credit_score,
                employment_years,
                is_employed,
                is_unemployed,
                owns_property,
                rents,
                lives_with_family
            ]
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def train_model(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Train Random Forest with FAANG-grade configuration."""
        
        print("\n" + "="*80)
        print("TRAINING RANDOM FOREST MODEL")
        print("="*80)
        
        # Feature scaling
        print("\n[1/5] Feature scaling...")
        X_scaled = self.scaler.fit_transform(X)
        
        # Train-test split
        print("[2/5] Train-test split (80/20)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"  • Training set: {len(X_train)} samples")
        print(f"  • Test set: {len(X_test)} samples")
        
        # Train Random Forest with class balancing
        print("\n[3/5] Training Random Forest...")
        self.model = RandomForestClassifier(
            n_estimators=200,           # More trees for stability
            max_depth=10,               # Prevent overfitting
            min_samples_split=2,        # Allow detailed splits
            min_samples_leaf=1,         # Flexible leaf nodes
            max_features='sqrt',        # Standard for classification
            bootstrap=True,             # Bagging for variance reduction
            class_weight='balanced',    # Handle class imbalance
            random_state=42,
            n_jobs=-1                   # Use all CPUs
        )
        
        self.model.fit(X_train, y_train)
        print("  ✓ Model trained successfully")
        
        # Feature importances
        self.feature_importances = dict(zip(
            self.FEATURE_NAMES,
            self.model.feature_importances_
        ))
        
        # Evaluation
        print("\n[4/5] Model evaluation...")
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)
        
        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        # Cross-validation
        print("\n[5/5] Cross-validation (5-fold)...")
        cv_scores = cross_val_score(
            self.model, X_scaled, y,
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
            scoring='f1'
        )
        
        print(f"\n{'='*80}")
        print("MODEL PERFORMANCE")
        print(f"{'='*80}")
        print(f"\nTest Set Performance:")
        print(f"  • Accuracy: {accuracy:.3f}")
        print(f"  • F1 Score: {f1:.3f}")
        
        print(f"\nCross-Validation (5-fold):")
        print(f"  • Mean F1: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
        print(f"  • Scores: {[f'{s:.3f}' for s in cv_scores]}")
        
        print(f"\nConfusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(f"  [[TN={cm[0,0]}, FP={cm[0,1]}],")
        print(f"   [FN={cm[1,0]}, TP={cm[1,1]}]]")
        
        print(f"\nFeature Importances (Top 5):")
        sorted_importances = sorted(
            self.feature_importances.items(),
            key=lambda x: x[1],
            reverse=True
        )
        for feat, imp in sorted_importances[:5]:
            print(f"  • {feat:25s}: {imp:.4f}")
        
        # Return training report
        return {
            'test_accuracy': float(accuracy),
            'test_f1': float(f1),
            'cv_mean_f1': float(cv_scores.mean()),
            'cv_std_f1': float(cv_scores.std()),
            'cv_scores': [float(s) for s in cv_scores],
            'confusion_matrix': cm.tolist(),
            'feature_importances': self.feature_importances,
            'n_train_samples': len(X_train),
            'n_test_samples': len(X_test),
            'n_features': len(self.FEATURE_NAMES)
        }
    
    def save_model(self, training_report: Dict):
        """Save model, scaler, and metadata."""
        
        print(f"\n{'='*80}")
        print("SAVING MODEL ARTIFACTS")
        print(f"{'='*80}")
        
        # Save model
        model_path = self.models_path / "eligibility_model_v3.pkl"
        joblib.dump(self.model, model_path)
        print(f"\n✓ Model saved: {model_path} ({model_path.stat().st_size / 1024:.1f} KB)")
        
        # Save scaler
        scaler_path = self.models_path / "feature_scaler_v3.pkl"
        joblib.dump(self.scaler, scaler_path)
        print(f"✓ Scaler saved: {scaler_path}")
        
        # Save feature names
        features_path = self.models_path / "feature_names_v3.json"
        with open(features_path, 'w') as f:
            json.dump(self.FEATURE_NAMES, f, indent=2)
        print(f"✓ Feature names saved: {features_path}")
        
        # Save metadata
        metadata = {
            "model_version": "v3",
            "model_type": "RandomForestClassifier",
            "n_features": len(self.FEATURE_NAMES),
            "feature_names": self.FEATURE_NAMES,
            "training_date": datetime.now().isoformat(),
            "training_samples": training_report['n_train_samples'],
            "test_accuracy": training_report['test_accuracy'],
            "test_f1": training_report['test_f1'],
            "cv_mean_f1": training_report['cv_mean_f1'],
            "hyperparameters": {
                "n_estimators": 200,
                "max_depth": 10,
                "class_weight": "balanced"
            },
            "label_definition": "1=APPROVE (low income, high need), 0=REJECT (high income, low need)",
            "note": "Use FeatureExtractor.extract_features() for inference"
        }
        
        metadata_path = self.models_path / "model_metadata_v3.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Metadata saved: {metadata_path}")
        
        # Save training report
        report_path = self.models_path / "training_report_v3.json"
        with open(report_path, 'w') as f:
            json.dump(training_report, f, indent=2)
        print(f"✓ Training report saved: {report_path}")
        
        print(f"\n{'='*80}")
        print("MODEL TRAINING COMPLETE")
        print(f"{'='*80}")
        print("\nModel artifacts:")
        print(f"  • eligibility_model_v3.pkl")
        print(f"  • feature_scaler_v3.pkl")
        print(f"  • feature_names_v3.json")
        print(f"  • model_metadata_v3.json")
        print(f"  • training_report_v3.json")
        print("\nNext steps:")
        print("  1. Update eligibility_agent.py to use v3 model")
        print("  2. Restart FastAPI server")
        print("  3. Test with approved_1 application")
        print(f"{'='*80}\n")
    
    def test_predictions(self, X: np.ndarray, y: np.ndarray):
        """Test model predictions on all samples."""
        
        print(f"\n{'='*80}")
        print("TESTING MODEL PREDICTIONS")
        print(f"{'='*80}\n")
        
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        # Load metadata for case names
        metadata_file = self.test_data_path.parent / "test_applications_metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        print(f"{'Case ID':<20} {'True Label':<12} {'Predicted':<12} {'Probability':<15} {'Match'}")
        print("-" * 80)
        
        for i, app in enumerate(metadata['applications']):
            case_id = app['case_id']
            true_label = y[i]
            pred_label = predictions[i]
            prob = probabilities[i][1]  # Probability of class 1 (approve)
            match = "✓" if true_label == pred_label else "✗"
            
            print(f"{case_id:<20} {true_label:<12} {pred_label:<12} {prob:>6.2%}         {match}")


def main():
    """Train FAANG-grade ML model."""
    
    print("\n" + "="*80)
    print("FAANG-GRADE ML MODEL TRAINING")
    print("Social Support Eligibility Prediction")
    print("="*80)
    
    # Initialize trainer
    trainer = FANGGradeMLTrainer()
    
    # Load data
    X, y = trainer.load_training_data()
    
    # Train model
    training_report = trainer.train_model(X, y)
    
    # Test predictions
    trainer.test_predictions(X, y)
    
    # Save model
    trainer.save_model(training_report)
    
    print("\n🎉 FAANG-grade model ready for production!")
    return training_report


if __name__ == "__main__":
    main()
