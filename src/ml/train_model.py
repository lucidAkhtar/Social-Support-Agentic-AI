"""
ML Model Training Pipeline
Trains Random Forest model on synthetic data for eligibility prediction
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import json
from pathlib import Path
from datetime import datetime


class EligibilityModelTrainer:
    """Train and evaluate Random Forest model for eligibility prediction"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path
        self.model = None
        self.feature_columns = [
            "age", "family_size", "years_of_experience",
            "monthly_income", "monthly_expenses", "net_monthly_income",
            "total_assets", "total_liabilities", "net_worth",
            "credit_score", "dti_ratio"
        ]
        self.categorical_features = ["employment_status", "nationality", "gender"]
        
    def load_data(self) -> pd.DataFrame:
        """Load synthetic data"""
        if self.data_path:
            df = pd.read_csv(self.data_path)
        else:
            # Look for most recent synthetic data
            data_dir = Path("data/synthetic")
            csv_files = list(data_dir.glob("synthetic_applicants_*.csv"))
            if not csv_files:
                raise FileNotFoundError("No synthetic data found. Run synthetic_data_generator.py first.")
            
            latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
            df = pd.read_csv(latest_file)
            print(f"Loaded data from: {latest_file}")
        
        print(f"Dataset size: {len(df)} samples")
        print(f"Features: {len(self.feature_columns)} numerical + {len(self.categorical_features)} categorical")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> tuple:
        """Prepare features for training"""
        # Encode categorical features
        df_encoded = df.copy()
        
        # One-hot encode employment status
        employment_dummies = pd.get_dummies(df['employment_status'], prefix='employment')
        df_encoded = pd.concat([df_encoded, employment_dummies], axis=1)
        
        # Encode gender (binary)
        df_encoded['gender_encoded'] = (df['gender'] == 'Male').astype(int)
        
        # For nationality, create "is_uae" feature
        df_encoded['is_uae'] = (df['nationality'] == 'UAE').astype(int)
        
        # Select features - only numerical columns
        feature_cols = self.feature_columns.copy()
        feature_cols.extend([col for col in df_encoded.columns if col.startswith('employment_')])
        feature_cols.extend(['gender_encoded', 'is_uae'])
        
        # Ensure all columns exist and convert to numeric
        X = df_encoded[feature_cols].copy()
        
        # Convert all columns to numeric, coerce errors to NaN, then fill with 0
        for col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce').fillna(0)
        
        y = df_encoded['is_eligible']
        
        print(f"\nFeature matrix shape: {X.shape}")
        print(f"Target distribution: {y.value_counts().to_dict()}")
        print(f"Feature columns: {feature_cols}")
        
        return X, y, feature_cols
    
    def train_model(self, X, y, use_grid_search=False):
        """Train Random Forest model"""
        print("\n" + "=" * 60)
        print("TRAINING RANDOM FOREST MODEL")
        print("=" * 60)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")
        
        if use_grid_search:
            print("\nPerforming Grid Search for hyperparameter tuning...")
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, 30, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
            
            rf = RandomForestClassifier(random_state=42)
            grid_search = GridSearchCV(rf, param_grid, cv=5, scoring='roc_auc', n_jobs=-1, verbose=1)
            grid_search.fit(X_train, y_train)
            
            self.model = grid_search.best_estimator_
            print(f"\nBest parameters: {grid_search.best_params_}")
            print(f"Best cross-validation score: {grid_search.best_score_:.4f}")
        else:
            # Train with default good parameters
            self.model = RandomForestClassifier(
                n_estimators=200,
                max_depth=20,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )
            
            print("\nTraining model...")
            self.model.fit(X_train, y_train)
        
        # Cross-validation
        print("\nPerforming 5-fold cross-validation...")
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5, scoring='roc_auc')
        print(f"Cross-validation ROC-AUC scores: {cv_scores}")
        print(f"Mean CV ROC-AUC: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Evaluate on test set
        print("\n" + "=" * 60)
        print("MODEL EVALUATION")
        print("=" * 60)
        
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred, target_names=['Not Eligible', 'Eligible']))
        
        print("\nConfusion Matrix:")
        cm = confusion_matrix(y_test, y_pred)
        print(cm)
        
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        print(f"\nROC-AUC Score: {roc_auc:.4f}")
        
        # Feature importance
        print("\n" + "=" * 60)
        print("FEATURE IMPORTANCE")
        print("=" * 60)
        feature_importance = pd.DataFrame({
            'feature': X.columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\nTop 15 Most Important Features:")
        print(feature_importance.head(15).to_string(index=False))
        
        return X_test, y_test, y_pred, y_pred_proba, feature_importance
    
    def save_model(self, output_dir: str = "src/ml"):
        """Save trained model"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_path = f"{output_dir}/eligibility_model.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"\n✓ Model saved: {model_path}")
        
        # Save feature names
        features_path = f"{output_dir}/model_features.json"
        with open(features_path, 'w') as f:
            json.dump({
                "features": list(self.feature_columns),
                "model_type": "RandomForestClassifier",
                "trained_at": datetime.now().isoformat()
            }, f, indent=2)
        print(f"✓ Features saved: {features_path}")
        
        return model_path
    
    def plot_results(self, y_test, y_pred, y_pred_proba, feature_importance, output_dir="data/synthetic"):
        """Generate evaluation plots"""
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 1. Confusion Matrix
        plt.figure(figsize=(8, 6))
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
        plt.title('Confusion Matrix')
        plt.ylabel('True Label')
        plt.xlabel('Predicted Label')
        plt.savefig(f"{output_dir}/confusion_matrix.png", dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {output_dir}/confusion_matrix.png")
        plt.close()
        
        # 2. ROC Curve
        fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        plt.figure(figsize=(8, 6))
        plt.plot(fpr, tpr, label=f'ROC curve (AUC = {roc_auc:.3f})')
        plt.plot([0, 1], [0, 1], 'k--', label='Random')
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('ROC Curve')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f"{output_dir}/roc_curve.png", dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {output_dir}/roc_curve.png")
        plt.close()
        
        # 3. Feature Importance
        plt.figure(figsize=(10, 8))
        top_features = feature_importance.head(15)
        plt.barh(range(len(top_features)), top_features['importance'])
        plt.yticks(range(len(top_features)), top_features['feature'])
        plt.xlabel('Importance')
        plt.title('Top 15 Feature Importances')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig(f"{output_dir}/feature_importance.png", dpi=150, bbox_inches='tight')
        print(f"✓ Saved: {output_dir}/feature_importance.png")
        plt.close()


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("ML MODEL TRAINING PIPELINE")
    print("=" * 60)
    
    # Initialize trainer
    trainer = EligibilityModelTrainer()
    
    # Load data
    print("\n1. Loading Data...")
    df = trainer.load_data()
    
    # Prepare features
    print("\n2. Preparing Features...")
    X, y, feature_cols = trainer.prepare_features(df)
    
    # Train model
    print("\n3. Training Model...")
    X_test, y_test, y_pred, y_pred_proba, feature_importance = trainer.train_model(X, y, use_grid_search=False)
    
    # Save model
    print("\n4. Saving Model...")
    model_path = trainer.save_model()
    
    # Plot results
    print("\n5. Generating Plots...")
    trainer.plot_results(y_test, y_pred, y_pred_proba, feature_importance)
    
    print("\n" + "=" * 60)
    print("✓ ML MODEL TRAINING COMPLETE")
    print("=" * 60)
    print(f"\nModel saved at: {model_path}")
    print("Ready to use in EligibilityAgent!")


if __name__ == "__main__":
    main()
