# ML Model Building - Social Support Eligibility

## What?
Dual machine learning models (Random Forest + XGBoost) to predict social support eligibility with **100% accuracy** on synthetic data.

**Current Models:**
- **XGBoost v4** (Production Default) - `xgboost_v4.pkl` → `model_latest.pkl`
- **Random Forest v4** (Comparison) - `random_forest_v4.pkl`

## Why?

### Business Need
Automate eligibility decisions for social support applications to:
- Reduce manual review time
- Ensure consistent policy application
- Identify high-need cases quickly
- Minimize human bias

### Why XGBoost as Default?
1. **Better Regularization** - L1=0.1, L2=1.0 prevents overfitting
2. **Handles Class Imbalance** - `scale_pos_weight` for skewed data (90% approve, 10% decline)
3. **FAANG Industry Standard** - Used at Meta, Amazon, Netflix
4. **Faster Training/Prediction** - Optimized gradient boosting
5. **Production-Ready** - Robust error handling, better generalization

### Why Keep Random Forest?
- Baseline comparison for model validation
- Simpler interpretability for stakeholders
- Fallback option if XGBoost issues arise

## How?

### Feature Engineering (12 Features)
**Financial (6):**
- `monthly_income` - Primary income indicator
- `family_size` - Household dependency
- `net_worth` - Overall financial health
- `total_assets` - Asset holdings
- `total_liabilities` - Debt burden
- `credit_score` - Credit worthiness

**Employment (3):**
- `employment_years` - Job stability
- `is_employed` - Current employment status
- `is_unemployed` - Unemployment flag

**Housing (3):**
- `owns_property` - Property ownership
- `rents` - Rental status
- `lives_with_family` - Living arrangement

### Training Process
1. **Synthetic Data Generation** - 1000 samples (90% approve, 10% decline)
2. **Feature Scaling** - StandardScaler for normalization
3. **Model Training:**
   - Random Forest: `class_weight='balanced'`, 100 estimators
   - XGBoost: `scale_pos_weight`, learning_rate=0.1, max_depth=5
4. **Evaluation** - Accuracy, F1-score, ROC AUC
5. **Persistence** - Save models + metadata as v4

### Versioning Strategy
- **v4** (Current) - Dual models (XGBoost + RF) with 12 features
- **v3** (Previous) - Single RF model, 12 features
- **v2** (Legacy) - 8 features, production baseline
- **Fallback** - Rule-based if no models available

## Assumptions

### Data Distribution
- **90% Approval Rate** - Reflects social welfare policy (inclusive)
- **10% Decline Rate** - Only extreme cases rejected
- **Feature Correlations:**
  - Low income → High approval probability
  - High family size → High approval probability
  - Good credit score → Neutral (not primary factor)

### Synthetic Data Quality
- Training on generated data (not real historical cases)
- Assumes synthetic patterns match real-world distributions
- 100% accuracy expected on synthetic test set
- Real-world accuracy will vary (likely 85-95%)

### Feature Importance
Top predictors (assumed):
1. Monthly income (most critical)
2. Family size (high weight)
3. Employment status (moderate weight)
4. Credit score (low weight - social policy favors need over credit)

### Model Constraints
- No temporal features (application date, seasonality)
- No demographic features (age, gender, nationality) - fairness constraint
- No external data sources (market conditions, unemployment rates)

## Business Rules

### Approval Criteria (HIGH NEED)
**APPROVED** when:
- Monthly income ≤ $3,500 AND family size ≥ 4
- Unemployed + low assets (< $5,000)
- Credit score < 600 + high liabilities
- **Policy Score: 70-95** (need-based scoring)

### Conditional Approval (MODERATE NEED)
**CONDITIONAL** when:
- Monthly income $3,500-$6,000 + medium family (2-5)
- Employed but low income + high family size
- Recent job loss with assets to sustain temporarily
- **Policy Score: 50-70** (borderline cases)
- **Conditions:** Job search evidence, asset review, monthly check-ins

### Rejection Criteria (LOW NEED)
**DECLINED** when:
- Monthly income > $8,000 + small family (1-3)
- High net worth (> $50,000) regardless of income
- Credit score > 700 + low liabilities
- Property ownership + adequate income
- **Policy Score: 10-50** (low need)

### Policy Score Calculation
```
policy_score = 100 - (income/200) + (family_size * 5) - (credit_score/10)
```
**Logic:** Lower income + larger family + poor credit = higher need = higher score

### Decision Thresholds
- **ML Confidence ≥ 0.6** → Use ML prediction
- **ML Confidence < 0.6** → Escalate to manual review
- **Policy Score ≥ 70** → Override ML to APPROVE (need-based safety net)
- **Policy Score < 30** → Override ML to DECLINE (clear ineligibility)

### Priority Levels
- **HIGH** (Policy Score ≥ 70) - Process within 24 hours
- **MEDIUM** (50-70) - Process within 3 days
- **LOW** (< 50) - Standard 7-day processing

## Model Performance (v4)

### XGBoost (Default)
- Accuracy: **100%** (synthetic test set)
- F1-Score: **100%**
- ROC AUC: **100%**
- Features: 12

### Random Forest (Comparison)
- Accuracy: **100%** (synthetic test set)
- F1-Score: **100%**
- ROC AUC: **100%**
- Features: 12

### Expected Real-World Performance
- Accuracy: **85-95%** (accounting for real-world variance)
- False Positive Rate: < 5% (incorrect approvals)
- False Negative Rate: < 10% (incorrect denials - more acceptable)

## Integration

### FastAPI Endpoint
- Agent: `EligibilityAgent` in `src/agents/eligibility_agent.py`
- Model Loading: Auto-fallback (v4 XGBoost → v4 RF → v3 → v2 → rules)
- Prediction: Real-time inference via LangGraph orchestrator

### Model Selection Logic
1. Try `model_latest.pkl` (symlink to `xgboost_v4.pkl`)
2. Fallback to `random_forest_v4.pkl`
3. Fallback to `eligibility_model_v3.pkl`
4. Fallback to rule-based decision

---
**Last Updated:** January 2026  
**Model Version:** v4 (XGBoost + Random Forest)  
**Training Script:** `models/train_dual_models.py`
