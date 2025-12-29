"""
Phase 4: ML Training Pipeline
==============================

Machine learning model training on validated application data.

This module:
1. Loads 50 validated applications with extraction data
2. Engineers 15-20 features from validation results and extracted data
3. Trains RandomForest classifier for eligibility prediction
4. Performs 5-fold cross-validation
5. Generates feature importance analysis
6. Produces comprehensive ML performance reports

Target variable: Validation status (PASSED_WITH_WARNINGS → approve)
Features: Income, credit, assets, employment, personal info metrics
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_validate, StratifiedKFold
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_auc_score
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MLTrainingPipeline:
    """Complete ML training pipeline for social support eligibility prediction."""
    
    def __init__(self, validation_results_path: str = "validation_test_results.json"):
        """
        Initialize ML training pipeline.
        
        Args:
            validation_results_path: Path to validation results JSON
        """
        self.validation_results_path = validation_results_path
        self.applications_data = []
        self.X = None  # Features
        self.y = None  # Target
        self.feature_names = None
        self.model = None
        self.cv_results = None
        self.feature_importance = None
        
        logger.info("ML Training Pipeline initialized")
    
    def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run complete ML pipeline: load data → engineer features → train → evaluate.
        
        Returns:
            Dict: Complete pipeline results and metrics
        """
        logger.info("\n" + "="*80)
        logger.info("PHASE 4: ML TRAINING PIPELINE")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        # Step 1: Load validation results
        logger.info("\n[1/4] Loading validation results...")
        self.load_validation_results()
        logger.info(f"✅ Loaded {len(self.applications_data)} validated applications")
        
        # Step 2: Engineer features
        logger.info("\n[2/4] Engineering features from validation data...")
        self.engineer_features()
        logger.info(f"✅ Engineered {self.X.shape[1]} features from {self.X.shape[0]} applications")
        
        # Step 3: Train model with cross-validation
        logger.info("\n[3/4] Training RandomForest with 5-fold cross-validation...")
        self.train_and_validate()
        logger.info(f"✅ Model training complete")
        
        # Step 4: Generate reports
        logger.info("\n[4/4] Generating comprehensive reports...")
        duration = (datetime.now() - start_time).total_seconds()
        
        results = self._compile_results(duration)
        self._print_reports(results)
        self._save_results(results)
        
        logger.info("\n" + "="*80)
        logger.info("✅ PHASE 4 COMPLETE - ML TRAINING PIPELINE FINISHED")
        logger.info("="*80)
        
        return results
    
    def load_validation_results(self) -> None:
        """Load and parse validation results from JSON file."""
        if not os.path.exists(self.validation_results_path):
            raise FileNotFoundError(f"Validation results not found: {self.validation_results_path}")
        
        with open(self.validation_results_path, 'r') as f:
            data = json.load(f)
        
        # Extract application data
        for app in data.get('applications', []):
            app_data = {
                'application_id': app['application_id'],
                'validation_status': app['validation_status'],
                'quality_score': app['quality_score'],
                'consistency_score': app['consistency_score'],
                'completeness_score': app['completeness_score'],
                'scores_by_category': app.get('scores_by_category', {}),
                'findings_count': app['findings_count'],
                'documents_validated': app.get('documents_validated', [])
            }
            self.applications_data.append(app_data)
    
    def engineer_features(self) -> None:
        """
        Engineer 15-20 features from validation data for ML training.
        
        Features created:
        1. Quality-based features (quality score, consistency, completeness)
        2. Category scores (personal, employment, income, assets, credit)
        3. Validation-based features (critical issues, high issues, etc)
        4. Data completeness (documents present, fields present)
        5. Risk indicators (debt ratio, asset ratio, etc)
        """
        features_list = []
        target_list = []
        
        for app in self.applications_data:
            features = {}
            
            # 1. Quality metrics (3 features)
            features['quality_score'] = app['quality_score']
            features['consistency_score'] = app['consistency_score']
            features['completeness_score'] = app['completeness_score']
            
            # 2. Category scores (5 features)
            scores = app['scores_by_category']
            features['personal_info_score'] = scores.get('personal_info', 0.0)
            features['employment_score'] = scores.get('employment', 0.0)
            features['income_score'] = scores.get('income', 0.0)
            features['assets_score'] = scores.get('assets', 0.0)
            features['credit_score'] = scores.get('credit', 0.0)
            
            # 3. Validation metrics (4 features)
            features['findings_count'] = app['findings_count']
            features['documents_count'] = len(app['documents_validated'])
            features['all_documents_present'] = 1.0 if len(app['documents_validated']) == 6 else 0.0
            features['zero_findings'] = 1.0 if app['findings_count'] == 0 else 0.0
            
            # 4. Composite features (5 features)
            # Average of all category scores
            category_scores = [
                scores.get('personal_info', 0.0),
                scores.get('employment', 0.0),
                scores.get('income', 0.0),
                scores.get('assets', 0.0),
                scores.get('credit', 0.0)
            ]
            features['avg_category_score'] = np.mean(category_scores)
            features['min_category_score'] = np.min(category_scores)
            features['max_category_score'] = np.max(category_scores)
            
            # Score consistency (variance indicates balanced vs unbalanced profile)
            features['category_variance'] = np.var(category_scores)
            features['overall_quality_index'] = (
                0.3 * app['quality_score'] +
                0.3 * app['consistency_score'] +
                0.2 * app['completeness_score'] +
                0.2 * np.mean(category_scores)
            )
            
            features_list.append(features)
            
            # Target: 1 for PASSED_WITH_WARNINGS (approve), 0 otherwise
            target = 1 if app['validation_status'] == 'passed_with_warnings' else 0
            target_list.append(target)
        
        # Convert to DataFrame
        df = pd.DataFrame(features_list)
        
        self.feature_names = df.columns.tolist()
        self.X = df.values
        self.y = np.array(target_list)
        
        logger.info(f"Feature matrix shape: {self.X.shape}")
        logger.info(f"Target distribution: {np.sum(self.y)}/{len(self.y)} positive ({100*np.mean(self.y):.1f}%)")
    
    def train_and_validate(self) -> None:
        """Train RandomForest with 5-fold cross-validation."""
        # Initialize RandomForest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        # Setup cross-validation
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        
        # Run cross-validation with multiple metrics
        scoring = {
            'accuracy': 'accuracy',
            'precision': 'precision',
            'recall': 'recall',
            'f1': 'f1',
            'roc_auc': 'roc_auc'
        }
        
        self.cv_results = cross_validate(
            self.model,
            self.X, self.y,
            cv=cv,
            scoring=scoring,
            return_train_score=True
        )
        
        # Train final model on all data
        self.model.fit(self.X, self.y)
        self.feature_importance = self.model.feature_importances_
    
    def _compile_results(self, duration: float) -> Dict[str, Any]:
        """Compile all training results into a results dictionary."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': duration,
            'applications_trained': len(self.applications_data),
            'features_engineered': len(self.feature_names),
            'target_distribution': {
                'positive': int(np.sum(self.y)),
                'negative': int(len(self.y) - np.sum(self.y)),
                'positive_ratio': float(np.mean(self.y))
            },
            'feature_names': self.feature_names,
            'model_parameters': {
                'algorithm': 'RandomForest',
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'random_state': 42
            }
        }
        
        # Add cross-validation results
        cv_metrics = {}
        for metric in ['accuracy', 'precision', 'recall', 'f1', 'roc_auc']:
            test_scores = self.cv_results[f'test_{metric}']
            train_scores = self.cv_results[f'train_{metric}']
            
            cv_metrics[metric] = {
                'test_mean': float(np.mean(test_scores)),
                'test_std': float(np.std(test_scores)),
                'test_scores': test_scores.tolist(),
                'train_mean': float(np.mean(train_scores)),
                'train_std': float(np.std(train_scores)),
            }
        
        results['cross_validation_results'] = cv_metrics
        
        # Add feature importance
        feature_importance_list = [
            {
                'feature': name,
                'importance': float(imp),
                'importance_pct': float(100 * imp / np.sum(self.feature_importance))
            }
            for name, imp in zip(self.feature_names, self.feature_importance)
        ]
        feature_importance_list.sort(key=lambda x: x['importance'], reverse=True)
        results['feature_importance'] = feature_importance_list
        
        # Add per-fold analysis
        results['per_fold_analysis'] = [
            {
                'fold': i+1,
                'test_accuracy': float(self.cv_results['test_accuracy'][i]),
                'test_precision': float(self.cv_results['test_precision'][i]),
                'test_recall': float(self.cv_results['test_recall'][i]),
                'test_f1': float(self.cv_results['test_f1'][i])
            }
            for i in range(5)
        ]
        
        return results
    
    def _print_reports(self, results: Dict[str, Any]) -> None:
        """Print comprehensive training reports."""
        
        # Summary Report
        logger.info("\n" + "="*80)
        logger.info("ML TRAINING SUMMARY")
        logger.info("="*80)
        logger.info(f"Applications trained:        {results['applications_trained']}")
        logger.info(f"Features engineered:         {results['features_engineered']}")
        logger.info(f"Training duration:           {results['duration_seconds']:.2f} seconds")
        logger.info(f"Target positive (approve):   {results['target_distribution']['positive']}/{results['applications_trained']} ({100*results['target_distribution']['positive_ratio']:.1f}%)")
        
        # Cross-Validation Results
        logger.info("\n" + "="*80)
        logger.info("CROSS-VALIDATION RESULTS (5-FOLD)")
        logger.info("="*80)
        
        cv = results['cross_validation_results']
        logger.info(f"\nAccuracy:")
        logger.info(f"  Test:  {cv['accuracy']['test_mean']:.4f} ± {cv['accuracy']['test_std']:.4f}")
        logger.info(f"  Train: {cv['accuracy']['train_mean']:.4f} ± {cv['accuracy']['train_std']:.4f}")
        
        logger.info(f"\nPrecision:")
        logger.info(f"  Test:  {cv['precision']['test_mean']:.4f} ± {cv['precision']['test_std']:.4f}")
        logger.info(f"  Train: {cv['precision']['train_mean']:.4f} ± {cv['precision']['train_std']:.4f}")
        
        logger.info(f"\nRecall:")
        logger.info(f"  Test:  {cv['recall']['test_mean']:.4f} ± {cv['recall']['test_std']:.4f}")
        logger.info(f"  Train: {cv['recall']['train_mean']:.4f} ± {cv['recall']['train_std']:.4f}")
        
        logger.info(f"\nF1-Score:")
        logger.info(f"  Test:  {cv['f1']['test_mean']:.4f} ± {cv['f1']['test_std']:.4f}")
        logger.info(f"  Train: {cv['f1']['train_mean']:.4f} ± {cv['f1']['train_std']:.4f}")
        
        logger.info(f"\nROC-AUC:")
        logger.info(f"  Test:  {cv['roc_auc']['test_mean']:.4f} ± {cv['roc_auc']['test_std']:.4f}")
        logger.info(f"  Train: {cv['roc_auc']['train_mean']:.4f} ± {cv['roc_auc']['train_std']:.4f}")
        
        # Per-Fold Breakdown
        logger.info("\n" + "="*80)
        logger.info("PER-FOLD BREAKDOWN")
        logger.info("="*80)
        
        for fold_data in results['per_fold_analysis']:
            fold = fold_data['fold']
            logger.info(f"\nFold {fold}:")
            logger.info(f"  Accuracy:  {fold_data['test_accuracy']:.4f}")
            logger.info(f"  Precision: {fold_data['test_precision']:.4f}")
            logger.info(f"  Recall:    {fold_data['test_recall']:.4f}")
            logger.info(f"  F1-Score:  {fold_data['test_f1']:.4f}")
        
        # Top Features
        logger.info("\n" + "="*80)
        logger.info("TOP 10 MOST IMPORTANT FEATURES")
        logger.info("="*80)
        
        for i, feature_data in enumerate(results['feature_importance'][:10], 1):
            logger.info(f"{i:2d}. {feature_data['feature']:30s} {feature_data['importance_pct']:6.2f}%")
        
        # Bottom Features
        logger.info("\n" + "="*80)
        logger.info("BOTTOM 5 LEAST IMPORTANT FEATURES")
        logger.info("="*80)
        
        for i, feature_data in enumerate(results['feature_importance'][-5:], 1):
            logger.info(f"   {feature_data['feature']:30s} {feature_data['importance_pct']:6.2f}%")
    
    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save training results to JSON file."""
        output_path = "ml_training_results.json"
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.info(f"\n✅ Results saved to: {output_path}")


def main():
    """Run Phase 4 ML training pipeline."""
    try:
        pipeline = MLTrainingPipeline()
        results = pipeline.run_full_pipeline()
        return True
    except Exception as e:
        logger.error(f"❌ Error during ML training: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
