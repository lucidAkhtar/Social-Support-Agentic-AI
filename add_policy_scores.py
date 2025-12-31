"""
Add Policy Scores to Generated Applications
Recalculate and save policy scores for all applications in data/processed/documents
"""
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from fix_dataset_generation import ScoringConstraints


def add_policy_scores():
    """Add policy_score to all application credit reports"""
    print("📊 Adding policy scores to applications...")
    
    docs_dir = Path("data/processed/documents")
    constraints = ScoringConstraints()
    
    updated_count = 0
    
    for app_dir in sorted(docs_dir.glob("APP-*")):
        app_id = app_dir.name
        
        # Load credit report and assets
        credit_file = app_dir / "credit_report.json"
        assets_file = app_dir / "assets_liabilities.json"
        
        if not credit_file.exists():
            print(f"⚠️  Skipping {app_id}: credit_report.json not found")
            continue
        
        with open(credit_file) as f:
            credit_data = json.load(f)
        
        assets_data = {}
        if assets_file.exists():
            with open(assets_file) as f:
                assets_data = json.load(f)
        
        # Build profile for scoring
        profile = {
            'monthly_income': credit_data.get('monthly_income', 0),
            'monthly_expenses': credit_data.get('monthly_expenses', 0),
            'family_size': credit_data.get('family_size', 1),
            'employment_status': credit_data.get('employment_status', 'Unknown'),
            'total_assets': assets_data.get('total_assets', 0),
            'total_liabilities': assets_data.get('total_liabilities', 0),
            'credit_score': credit_data.get('credit_score', 600)
        }
        
        # Calculate score
        policy_score = constraints.calculate_score(profile)
        
        # Add to credit report
        credit_data['policy_score'] = round(policy_score, 2)
        
        # Save updated credit report
        with open(credit_file, 'w') as f:
            json.dump(credit_data, f, indent=2)
        
        updated_count += 1
        
        if updated_count % 10 == 0:
            print(f"   Updated {updated_count} applications...")
    
    print(f"✅ Added policy scores to {updated_count} applications")
    
    # Show distribution
    scores = []
    for app_dir in sorted(docs_dir.glob("APP-*")):
        credit_file = app_dir / "credit_report.json"
        if credit_file.exists():
            with open(credit_file) as f:
                data = json.load(f)
                scores.append(data.get('policy_score', 0))
    
    if scores:
        low_count = sum(1 for s in scores if s < 40)
        med_count = sum(1 for s in scores if 40 <= s < 65)
        high_count = sum(1 for s in scores if s >= 65)
        
        print(f"\nScore Distribution:")
        print(f"  LOW    (<40):     {low_count:2d} apps ({low_count/len(scores)*100:.0f}%)")
        print(f"  MEDIUM (40-65):   {med_count:2d} apps ({med_count/len(scores)*100:.0f}%)")
        print(f"  HIGH   (>=65):    {high_count:2d} apps ({high_count/len(scores)*100:.0f}%)")


if __name__ == "__main__":
    add_policy_scores()
