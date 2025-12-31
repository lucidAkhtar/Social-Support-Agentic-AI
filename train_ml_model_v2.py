"""
Random Forest Model Training - V2 with Feature Consistency
FAANG Standards: Consistent features between training and inference
Trains on 40 diverse applications, generates 10 test applications
"""
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
import joblib
import random

# Feature names (CRITICAL: Must match between training and inference)
FEATURE_NAMES = [
    'monthly_income',
    'monthly_expenses',
    'monthly_net',
    'family_size',
    'total_assets',
    'total_liabilities',
    'net_worth',
    'credit_score'
]

class FeatureExtractor:
    """
    Centralized feature extraction to ensure consistency.
    MUST be used for both training and inference.
    """
    
    @staticmethod
    def extract_features(app_data: Dict) -> np.ndarray:
        """
        Extract 8 features from application data.
        
        Returns:
            np.ndarray with shape (8,) containing features in this order:
            [monthly_income, monthly_expenses, monthly_net, family_size,
             total_assets, total_liabilities, net_worth, credit_score]
        """
        features = [
            float(app_data.get('monthly_income', 0)),
            float(app_data.get('monthly_expenses', 0)),
            float(app_data.get('monthly_income', 0)) - float(app_data.get('monthly_expenses', 0)),  # monthly_net
            int(app_data.get('family_size', 1)),
            float(app_data.get('total_assets', 0)),
            float(app_data.get('total_liabilities', 0)),
            float(app_data.get('total_assets', 0)) - float(app_data.get('total_liabilities', 0)),  # net_worth
            int(app_data.get('credit_score', 600))
        ]
        
        return np.array(features)
    
    @staticmethod
    def validate_features(features: np.ndarray) -> bool:
        """Validate feature array shape and values"""
        if features.shape != (8,):
            print(f"❌ Invalid feature shape: {features.shape}, expected (8,)")
            return False
        
        if np.any(np.isnan(features)):
            print(f"❌ NaN values in features: {features}")
            return False
        
        return True


def load_training_data() -> Tuple[np.ndarray, np.ndarray, List[Dict]]:
    """
    Load 40 diverse applications for training.
    
    Returns:
        X: Feature matrix (40, 8)
        y: Labels (40,) - 1 for eligible (score >= 30), 0 for not eligible
        apps: List of application dictionaries
    """
    print("📂 Loading training data from disk...")
    
    docs_dir = Path("data/processed/documents")
    applications = []
    
    for app_dir in sorted(docs_dir.glob("APP-*")):
        app_id = app_dir.name
        
        # Load metadata (has policy_score and profile)
        metadata_file = app_dir / "metadata.json"
        if not metadata_file.exists():
            print(f"⚠️  Skipping {app_id}: metadata.json not found")
            continue
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        profile = metadata['profile']
        
        app_data = {
            "app_id": app_id,
            "monthly_income": profile['monthly_income'],
            "monthly_expenses": profile['monthly_expenses'],
            "family_size": profile['family_size'],
            "employment_status": profile['employment_status'],
            "total_assets": profile['total_assets'],
            "total_liabilities": profile['total_liabilities'],
            "credit_score": profile['credit_score'],
            "policy_score": metadata['policy_score']
        }
        
        applications.append(app_data)
    
    print(f"✅ Loaded {len(applications)} applications")
    
    # Extract features using FeatureExtractor
    extractor = FeatureExtractor()
    X = []
    y = []
    
    for app in applications:
        features = extractor.extract_features(app)
        
        if not extractor.validate_features(features):
            print(f"⚠️  Skipping {app['app_id']}: Invalid features")
            continue
        
        X.append(features)
        
        # Label: Eligible if policy_score >= 30
        label = 1 if app['policy_score'] >= 30 else 0
        y.append(label)
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"📊 Feature matrix shape: {X.shape}")
    print(f"📊 Label distribution: {np.bincount(y)}")
    print(f"   - Not eligible (score < 30): {np.sum(y == 0)}")
    print(f"   - Eligible (score >= 30): {np.sum(y == 1)}")
    
    return X, y, applications


def train_model(X: np.ndarray, y: np.ndarray) -> RandomForestClassifier:
    """
    Train Random Forest classifier with cross-validation.
    """
    print("\n🌲 Training Random Forest model...")
    
    # Check class balance
    class_counts = np.bincount(y)
    print(f"   Class distribution: {class_counts}")
    
    if len(class_counts) < 2:
        print("⚠️  Warning: Only one class present. Model will have 100% accuracy but is meaningless.")
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y if len(class_counts) > 1 else None
    )
    
    print(f"   Training set: {X_train.shape[0]} samples")
    print(f"   Test set: {X_test.shape[0]} samples")
    
    # Train model
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    
    print(f"\n📈 Model Performance:")
    print(f"   Training accuracy: {train_score:.3f}")
    print(f"   Test accuracy: {test_score:.3f}")
    
    # Cross-validation
    if len(class_counts) > 1:
        cv_scores = cross_val_score(model, X, y, cv=5)
        print(f"   Cross-validation scores: {cv_scores}")
        print(f"   CV mean: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    
    # Predictions
    y_pred = model.predict(X_test)
    
    print(f"\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=['Not Eligible', 'Eligible']))
    
    print(f"\n🎯 Confusion Matrix:")
    print(confusion_matrix(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': FEATURE_NAMES,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print(f"\n🔍 Feature Importance:")
    print(feature_importance.to_string(index=False))
    
    return model


def generate_test_applications() -> List[Dict]:
    """
    Generate 10 test applications with diverse scores.
    3 LOW (25-40), 4 MEDIUM (41-65), 3 HIGH (66-100)
    """
    print("\n🧪 Generating 10 test applications...")
    
    test_apps = []
    
    # 3 LOW tier (wealthy singles, don't need support)
    for i in range(3):
        app = {
            "app_id": f"TEST-LOW-{i+1:03d}",
            "applicant_name": f"Test Low {i+1}",
            "monthly_income": random.uniform(500, 2500),  # 10 pts
            "monthly_expenses": random.uniform(300, 1500),
            "family_size": 1,  # 5 pts
            "employment_status": "Unemployed",  # 0 pts
            "total_assets": random.uniform(400000, 800000),  # 5 pts (wealthy)
            "total_liabilities": random.uniform(50000, 200000),
            "credit_score": random.randint(300, 540)  # 5 pts
        }
        test_apps.append(app)
    
    # 4 MEDIUM tier (average families)
    for i in range(4):
        app = {
            "app_id": f"TEST-MED-{i+1:03d}",
            "applicant_name": f"Test Medium {i+1}",
            "monthly_income": random.uniform(3500, 8500),  # 20 pts
            "monthly_expenses": random.uniform(2000, 6000),
            "family_size": random.randint(2, 4),  # 10-20 pts
            "employment_status": random.choice(["Private Employee", "Self Employed"]),  # 5-10 pts
            "total_assets": random.uniform(60000, 200000),  # 10 pts
            "total_liabilities": random.uniform(20000, 80000),
            "credit_score": random.randint(620, 750)  # 10-15 pts
        }
        test_apps.append(app)
    
    # 3 HIGH tier (struggling families, need urgent support)
    for i in range(3):
        app = {
            "app_id": f"TEST-HIGH-{i+1:03d}",
            "applicant_name": f"Test High {i+1}",
            "monthly_income": random.uniform(1500, 2900),  # 10 pts
            "monthly_expenses": random.uniform(2000, 3500),
            "family_size": random.randint(5, 8),  # 20 pts
            "employment_status": "Government Employee",  # 20 pts
            "total_assets": random.uniform(8000, 45000),  # 15 pts (low assets)
            "total_liabilities": random.uniform(5000, 20000),
            "credit_score": random.randint(550, 700)  # 10 pts
        }
        test_apps.append(app)
    
    # Calculate policy scores for reference
    from fix_dataset_generation import ScoringConstraints
    constraints = ScoringConstraints()
    
    for app in test_apps:
        score = constraints.calculate_score(app)
        app['policy_score'] = score
    
    # Save test applications
    output_file = Path("test_applications.json")
    with open(output_file, 'w') as f:
        json.dump(test_apps, f, indent=2)
    
    print(f"✅ Generated 10 test applications, saved to: {output_file}")
    
    # Print distribution
    low_count = sum(1 for app in test_apps if app['policy_score'] < 40)
    med_count = sum(1 for app in test_apps if 40 <= app['policy_score'] < 65)
    high_count = sum(1 for app in test_apps if app['policy_score'] >= 65)
    
    print(f"   Distribution: {low_count} LOW, {med_count} MEDIUM, {high_count} HIGH")
    
    return test_apps


def test_inference(model: RandomForestClassifier, test_apps: List[Dict]):
    """
    Test model inference on test applications.
    CRITICAL: Uses FeatureExtractor to ensure feature consistency.
    """
    print("\n🔮 Testing model inference on test applications...")
    
    extractor = FeatureExtractor()
    
    for app in test_apps:
        # Extract features (same method used in training)
        features = extractor.extract_features(app)
        
        # Validate
        if not extractor.validate_features(features):
            print(f"❌ Invalid features for {app['app_id']}")
            continue
        
        # Predict
        features_2d = features.reshape(1, -1)
        prediction = model.predict(features_2d)[0]
        probability = model.predict_proba(features_2d)[0]
        
        # Result
        result = "ELIGIBLE" if prediction == 1 else "NOT ELIGIBLE"
        confidence = probability[prediction]
        
        print(f"   {app['app_id']}: Policy={app['policy_score']:.1f}, "
              f"Predicted={result} (confidence={confidence:.2%})")


def save_model(model: RandomForestClassifier):
    """Save model and metadata"""
    print("\n💾 Saving model...")
    
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    
    # Save model
    model_path = models_dir / "eligibility_model_v2.pkl"
    joblib.dump(model, model_path)
    print(f"   Model saved to: {model_path}")
    
    # Save feature names
    features_path = models_dir / "feature_names.json"
    with open(features_path, 'w') as f:
        json.dump(FEATURE_NAMES, f, indent=2)
    print(f"   Feature names saved to: {features_path}")
    
    # Save metadata
    metadata = {
        "model_type": "RandomForestClassifier",
        "n_features": len(FEATURE_NAMES),
        "feature_names": FEATURE_NAMES,
        "training_date": datetime.now().isoformat(),
        "label_definition": "1 if policy_score >= 30 else 0",
        "note": "Use FeatureExtractor.extract_features() for inference to ensure consistency"
    }
    
    metadata_path = models_dir / "model_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"   Metadata saved to: {metadata_path}")


def main():
    print("="*80)
    print("RANDOM FOREST MODEL TRAINING - V2")
    print("Training on 40 diverse applications with feature consistency")
    print("="*80)
    
    # Step 1: Load training data
    X, y, applications = load_training_data()
    
    if X.shape[0] < 10:
        print(f"\n❌ Error: Insufficient training data ({X.shape[0]} samples)")
        print("   Run: poetry run python fix_dataset_generation.py")
        return
    
    # Step 2: Train model
    model = train_model(X, y)
    
    # Step 3: Generate test applications
    test_apps = generate_test_applications()
    
    # Step 4: Test inference
    test_inference(model, test_apps)
    
    # Step 5: Save model
    save_model(model)
    
    print("\n" + "="*80)
    print("MODEL TRAINING COMPLETE")
    print("="*80)
    print("\nFiles created:")
    print("1. models/eligibility_model_v2.pkl - Trained model")
    print("2. models/feature_names.json - Feature names for consistency")
    print("3. models/model_metadata.json - Model metadata")
    print("4. test_applications.json - 10 test applications (3 LOW, 4 MED, 3 HIGH)")
    print("\nNext steps:")
    print("1. Test inference: Use FeatureExtractor.extract_features() for consistency")
    print("2. Test endpoints: poetry run python fastapi_test_endpoints.py")
    print("3. Integrate with chatbot: Load model and use FeatureExtractor")


if __name__ == "__main__":
    main()
